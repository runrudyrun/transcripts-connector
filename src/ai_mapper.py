import os
from typing import List, Dict, Any, Optional

import litellm
from litellm import completion

from src.logger import logger
from src.providers.base import Meeting

# Configuration for litellm proxy
LITELLM_API_BASE = os.environ.get("LITELLM_API_BASE")
LITELLM_API_KEY = os.environ.get("LITELLM_API_KEY")

class AIMapper:
    """
    Uses a Large Language Model (LLM) via litellm to intelligently match a transcript
    to the most likely calendar event from a list of candidates.
    """
    # When using a proxy, the model name is often prefixed by the provider
    # The proxy configuration will map this to the actual model.
    # We use the original model name here, assuming the proxy handles it.
    MODEL = "gpt-4o-mini"
    PROMPT_TEMPLATE = """
        You are an intelligent assistant helping to match a meeting transcript to a Google Calendar event.
        Based on the transcript content below, which of the following calendar events is the most likely match?

        TRANSCRIPT CONTENT (first 1500 characters):
        ---
        {transcript_content}
        ---

        CANDIDATE CALENDAR EVENTS:
        {event_options}

        Please analyze the participant names, topics, and any other clues in the transcript.
        Respond with the number of the best matching event (e.g., '1', '2', etc.).
        If you are confident that NONE of the events match, respond with the word 'NONE'.
        Your response must be ONLY the number or the word 'NONE'.
    """

    def _build_prompt(self, transcript_content: str, events: List[Dict[str, Any]]) -> str:
        """Builds the full prompt for the LLM."""
        event_options = ""
        for i, event in enumerate(events):
            event_summary = event.get('summary', 'No Title')
            event_organizer = event.get('organizer', {}).get('email', 'N/A')
            event_time = event.get('start', {}).get('dateTime', 'N/A')
            event_options += f"{i+1}. Summary: {event_summary}, Organizer: {event_organizer}, Time: {event_time}\n"
        
        # Limit transcript content to avoid excessive token usage
        truncated_transcript = transcript_content[:1500]

        return self.PROMPT_TEMPLATE.format(
            transcript_content=truncated_transcript,
            event_options=event_options.strip()
        )

    def choose_event(self, transcript_content: str, events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Sends the request to the LLM and parses the response to select an event."""
        if not events:
            return None

        prompt = self._build_prompt(transcript_content, events)
        messages = [{"role": "user", "content": prompt}]

        try:
            logger.info(f"Sending request to LLM ({self.MODEL}) via proxy to match transcript with {len(events)} events.")
            
            # If using a litellm proxy, set the api_base and api_key
            if LITELLM_API_BASE and LITELLM_API_KEY:
                response = completion(
                    model=self.MODEL, 
                    messages=messages, 
                    temperature=0.0,
                    api_base=LITELLM_API_BASE,
                    api_key=LITELLM_API_KEY
                )
            else:
                # Fallback to direct API call if proxy is not configured
                logger.warning("LITELLM_API_BASE or LITELLM_API_KEY not set. Falling back to direct API call.")
                response = completion(model=self.MODEL, messages=messages, temperature=0.0)

            choice = response.choices[0].message.content.strip()
            logger.info(f"LLM choice: '{choice}'")

            if choice.upper() == 'NONE':
                return None
            if choice.isdigit():
                choice_index = int(choice) - 1
                if 0 <= choice_index < len(events):
                    return events[choice_index]
            
            logger.warning(f"LLM returned an invalid choice: '{choice}'. Could not match event.")
            return None

        except Exception as e:
            logger.error(f"Error during LLM completion call: {e}", exc_info=True)
            return None
