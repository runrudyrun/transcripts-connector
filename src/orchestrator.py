import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple

from src.google_api import GoogleApi
from src.providers.base import BaseConnector, Meeting
from src.logger import logger

# Keywords to identify and ignore certain events
IGNORE_KEYWORDS = os.environ.get("IGNORE_KEYWORDS", "1:1,1-1,catch-up").split(',')

class Orchestrator:
    """Handles the main logic of fetching, matching, and processing events."""

    def __init__(self, connector: BaseConnector, google_api: GoogleApi):
        self.connector = connector
        self.google_api = google_api

    def run(self, days: int):
        """Main execution flow."""
        logger.info(f"Starting the transcript connector...")
        logger.info(f"Using connector: {self.connector.__class__.__name__}")

        logger.info("Step 1: Authenticating with Google...")
        if not self.google_api.authenticate():
            logger.error("Failed to authenticate with Google. Exiting.")
            return
        logger.info("Successfully authenticated with Google.")

        logger.info(f"Searching for events in the last {days} days...")
        events = self._get_concluded_events(days)
        if not events:
            logger.info("No concluded events found to process.")
            return
        logger.info(f"Found {len(events)} concluded events to process.")

        logger.info(f"Step 3: Fetching meetings from {self.connector.__class__.__name__}...")
        meetings = self.connector.get_meetings()
        if not meetings:
            logger.warning(f"No meetings found in {self.connector.__class__.__name__}.")
            return

        matched_pairs = self._match_events_with_recordings(events, meetings)
        if not matched_pairs:
            logger.info("No matching events and recordings found.")
            logger.info("\nProcess finished.")
            return

        logger.info("\n--- Starting Event Processing ---")
        logger.info(f"Using ignore keywords: {IGNORE_KEYWORDS}")
        for event, meeting in matched_pairs:
            self._process_event_and_recording(event, meeting)
        
        logger.info("\nProcess finished.")

    def _get_concluded_events(self, days: int) -> List[Dict[str, Any]]:
        """Fetches calendar events that have concluded within the given timeframe."""
        logger.info("Step 2: Fetching concluded calendar events...")
        now = datetime.now(timezone.utc)
        time_min = now - timedelta(days=days)
        logger.info(f"Searching for concluded events from the last {days} days, {time_min.strftime('%H:%M:%S')}...")
        return self.google_api.get_concluded_events(time_min)

    def _match_events_with_recordings(self, events: List[Dict[str, Any]], meetings: List[Meeting]) -> List[Tuple[Dict[str, Any], Meeting]]:
        """Matches calendar events with recordings using a two-stage approach."""
        logger.info(f"\n--- Matching Calendar events with {self.connector.__class__.__name__} recordings ---")
        
        id_matched_pairs, remaining_events, remaining_meetings = [], list(events), list(meetings)
        try:
            logger.info("Entering conference ID matching stage...")
            id_matched_pairs, remaining_events, remaining_meetings = self._match_by_conference_id(events, meetings)
            logger.info("Conference ID matching stage finished successfully.")
        except Exception as e:
            logger.error(f"An unexpected error occurred during conference ID matching: {e}", exc_info=True)
            # In case of error, we fall back to time-based matching with all original events and meetings
            remaining_events = events
            remaining_meetings = meetings

        logger.info(f"Attempting to match {len(remaining_events)} remaining events and {len(remaining_meetings)} recordings by time...")
        time_matched_pairs, _, _ = self._match_by_time_and_title(remaining_events, remaining_meetings)
        
        return id_matched_pairs + time_matched_pairs

    def _match_by_conference_id(self, events: List[Dict[str, Any]], meetings: List[Meeting]) -> Tuple[List[Tuple[Dict[str, Any], Meeting]], List[Dict[str, Any]], List[Meeting]]:
        """Matches events and meetings based on Google Meet conference ID."""
        logger.info("--- Starting Conference ID Matching ---")
        matched_pairs = []
        unmatched_events = []
        meeting_ids_matched = set()

        for event in events:
            conference_id = event.get('conferenceData', {}).get('conferenceId')
            if not conference_id:
                unmatched_events.append(event)
                continue

            found_match = False
            for meeting in meetings:
                if meeting.id in meeting_ids_matched or not hasattr(meeting, 'conference_id') or not meeting.conference_id:
                    continue
                if meeting.conference_id == conference_id:
                    logger.info(f"Matched by Conference ID: '{event.get('summary')}' and recording '{meeting.name}'")
                    matched_pairs.append((event, meeting))
                    meeting_ids_matched.add(meeting.id)
                    found_match = True
                    break
            if not found_match:
                unmatched_events.append(event)
        
        unmatched_meetings = [m for m in meetings if m.id not in meeting_ids_matched]
        logger.info(f"{len(matched_pairs)} pairs matched by Conference ID.")
        return matched_pairs, unmatched_events, unmatched_meetings

    def _match_by_time_and_title(self, events: List[Dict[str, Any]], meetings: List[Meeting]) -> Tuple[List[Tuple[Dict[str, Any], Meeting]], List[Dict[str, Any]], List[Meeting]]:
        """Matches events and meetings based on time and title similarity."""
        logger.info("--- Starting Time-Based Matching ---")
        matched_pairs = []
        unmatched_events = []
        meeting_ids_matched = set()

        for event in events:
            event_summary = event.get('summary', 'NO_TITLE')
            event_start_str = event.get('start', {}).get('dateTime')
            if not event_start_str:
                unmatched_events.append(event)
                continue

            event_start = datetime.fromisoformat(event_start_str.replace('Z', '+00:00'))

            found_match = False
            for meeting in meetings:
                if meeting.id in meeting_ids_matched:
                    continue

                time_diff = abs(event_start - meeting.start_time)
                titles_match = event_summary.lower() == meeting.name.lower()

                if titles_match and time_diff < timedelta(minutes=5):
                    logger.info(f"SUCCESS: Matched by Time: '{event_summary}' (diff: {time_diff}) and recording '{meeting.name}'")
                    matched_pairs.append((event, meeting))
                    meeting_ids_matched.add(meeting.id)
                    found_match = True
                    break
            if not found_match:
                unmatched_events.append(event)

        unmatched_meetings = [m for m in meetings if m.id not in meeting_ids_matched]
        logger.info(f"--- Time-Based Matching Finished: {len(matched_pairs)} pairs matched. ---")
        return matched_pairs, unmatched_events, unmatched_meetings

    def _process_event_and_recording(self, event: Dict[str, Any], meeting: Meeting):
        """Processes a single matched event-recording pair."""
        event_summary = event.get('summary', 'No Title')
        event_id = event.get('id')
        logger.info(f"\nProcessing pair: '{event_summary}' (Event ID: {event_id})")
        logger.info(f"Using matched recording: '{meeting.name}' (ID: {meeting.id}).")

        if any(keyword.lower() in event_summary.lower() for keyword in IGNORE_KEYWORDS):
            logger.info(f"Event '{event_summary}' is in the ignore list, skipping.")
            return
        
        # Process Transcript
        if self.google_api.has_attachment(event.get('attachments', []), 'Transcript for'):
            logger.info(f"Event '{event_summary}' already has a transcript attachment, skipping transcript.")
        else:
            transcript = self.connector.get_transcript(meeting.id)
            if transcript:
                logger.info("Transcript found. Processing...")
                doc_title = f"Transcript for {event_summary} ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
                self.google_api.create_and_attach_doc(event_id, doc_title, transcript.text)
            else:
                logger.info("No transcript found for this recording.")

        # Process AI Notes
        if self.google_api.has_attachment(event.get('attachments', []), 'AI Notes for'):
            logger.info(f"Event '{event_summary}' already has an AI Notes attachment, skipping notes.")
        else:
            notes = self.connector.get_notes(meeting.id)
            if notes:
                logger.info("AI Notes found. Processing...")
                doc_title = f"AI Notes for {event_summary} ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
                self.google_api.create_and_attach_doc(event_id, doc_title, notes.content)
            else:
                logger.info("No AI notes found for this recording.")
