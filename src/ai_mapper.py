import os
from typing import List, Dict, Any, Optional

import litellm

from src.logger import logger
from src.providers.base import Meeting

# Configuration for litellm proxy
LITELLM_API_BASE = os.environ.get("LITELLM_API_BASE")
LITELLM_API_KEY = os.environ.get("LITELLM_API_KEY")

class AIMapper:
    """
    Uses a Large Language Model (LLM) via litellm to intelligently match a meeting's
    raw file content to the most likely calendar event from a list of candidates.
    """
    MODEL = "gpt-4o"

    def __init__(self):
        self.api_base = LITELLM_API_BASE
        self.api_key = LITELLM_API_KEY
        self.enabled = bool(self.api_base and self.api_key)
        if not self.enabled:
            logger.warning("AI Mapper is disabled. LITELLM_API_BASE and/or LITELLM_API_KEY are not set.")

    def match_meeting_to_event(self, meeting: Meeting, events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Uses an AI model to find the best matching event for a given meeting's raw text content."""
        if not self.enabled:
            return None

        raw_content = meeting.original_data.get('raw_content')
        if not raw_content:
            logger.warning(f"Cannot perform AI matching for meeting {meeting.id} without raw content.")
            return None

        # Prepare a simplified list of events for the prompt
        event_summaries = []
        for i, event in enumerate(events):
            event_summaries.append(
                f"Event Index: {i}\n"
                f"Event ID: {event['id']}\n"
                f"  Title: {event.get('summary', 'No Title')}\n"
                f"  Start Time: {event['start'].get('dateTime')}\n"
                f"  Attendees: {[att.get('email') for att in event.get('attendees', [])]}"
            )
        
        events_prompt_text = "\n\n".join(event_summaries)

        prompt = (
            f"You are an intelligent assistant. Your task is to analyze the raw text from a file and determine which calendar event it corresponds to. "
            f"The file content could be a meeting transcript, personal notes, or any other text.\n\n"
            f"--- FILE CONTENT START ---\n{raw_content[:15000]}\n--- FILE CONTENT END ---\n\n"
            f"Here is a list of potential calendar events:\n--- CALENDAR EVENTS START ---\n{events_prompt_text}\n--- CALENDAR EVENTS END ---\n\n"
            f"Analyze the file content for topics, names, projects, or any other clues. Compare this context with the titles, times, and attendees of the calendar events. "
            f"Based on your analysis, which event is the most likely match?\n\n"
            f"IMPORTANT: Your response MUST be ONLY the numeric 'Event Index' of the single best match. "
            f"DO NOT include any other text, explanations, or formatting. "
            f"If no event is a clear match, you MUST respond with the single word 'None'."
        )

        try:
            logger.info(f"Sending request to AI for matching file content (length: {len(raw_content)} chars) against {len(events)} events...")
            response = litellm.completion(
                model=self.MODEL,
                messages=[{"content": prompt, "role": "user"}],
                api_base=self.api_base,
                api_key=self.api_key,
                temperature=0.0
            )
            
            response_text = response.choices[0].message.content.strip()
            logger.info(f"AI response received: '{response_text}'")

            if response_text.lower() == 'none':
                return None

            try:
                best_match_index = int(response_text)
                if 0 <= best_match_index < len(events):
                    matched_event = events[best_match_index]
                    logger.info(f"Successfully matched content to event '{matched_event.get('summary', 'No Title')}' using AI.")
                    return matched_event
                else:
                    logger.warning(f"AI returned an out-of-bounds index: {best_match_index}")
                    return None
            except (ValueError, IndexError):
                logger.warning(f"AI returned an invalid index: '{response_text}'. Expected a number or 'None'.")
                return None

        except Exception as e:
            logger.error(f"An error occurred during AI matching: {e}", exc_info=True)
            return None
