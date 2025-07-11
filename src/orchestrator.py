import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple

from src.google_api import GoogleApi
from src.providers.base import BaseConnector, Meeting
from src.ai_mapper import AIMapper
from src.logger import logger

# Keywords to identify and ignore certain events
IGNORE_KEYWORDS = os.environ.get("IGNORE_KEYWORDS", "1:1,1-1,catch-up").split(',')

class Orchestrator:
    """Handles the main logic of fetching, matching, and processing events."""

    def __init__(self, connector: BaseConnector, google_api: GoogleApi):
        self.connector = connector
        self.google_api = google_api
        self.ai_mapper = AIMapper()

    def authenticate(self) -> bool:
        """Authenticates with Google and returns True on success."""
        logger.info("Step 1: Authenticating with Google...")
        if not self.google_api.authenticate():
            logger.error("Failed to authenticate with Google. Exiting.")
            return False
        logger.info("Successfully authenticated with Google.")
        return True

    def fetch_calendar_events(self, days: float) -> List[Dict[str, Any]]:
        """Fetches calendar events that have concluded within the given timeframe."""
        logger.info(f"Step 2: Fetching concluded calendar events from the last {days:.2f} days...")
        now = datetime.now(timezone.utc)
        time_min = now - timedelta(days=days)
        logger.info(f"Searching for concluded events from {time_min.strftime('%Y-%m-%d %H:%M:%S')} UTC...")
        events = self.google_api.get_concluded_events(time_min)
        if not events:
            logger.info("No concluded events found to process.")
        else:
            logger.info(f"Found {len(events)} concluded events to process.")
        return events

    def fetch_meetings_from_connector(self, days: float) -> List[Meeting]:
        """Fetches meetings from the configured connector."""
        logger.info(f"Step 3: Fetching meetings from {self.connector.__class__.__name__} for the last {days:.2f} days...")
        meetings = self.connector.get_meetings(days=days)
        if not meetings:
            logger.warning(f"No meetings found in {self.connector.__class__.__name__}.")
        return meetings

    def match_events_and_meetings(self, events: List[Dict[str, Any]], meetings: List[Meeting], force_ai: bool = False) -> List[Tuple[Dict[str, Any], Meeting]]:
        """Matches calendar events with recordings using a multi-stage approach."""
        logger.info(f"\n--- Matching {len(events)} events with {len(meetings)} {self.connector.__class__.__name__} recordings ---")
        
        all_matches = []
        unmatched_events, unmatched_meetings = list(events), list(meetings)

        if force_ai:
            logger.info("--- AI matching is forced, skipping standard matching methods. ---")
        else:
            # --- Stage 1: Match by comparing conference ID ---
            stage1_matches, unmatched_events, unmatched_meetings = self._match_by_conference_id(unmatched_events, unmatched_meetings)
            all_matches.extend(stage1_matches)

            # --- Stage 2: Match by comparing title and start time ---
            stage2_matches, unmatched_events, unmatched_meetings = self._match_by_time_and_title(unmatched_events, unmatched_meetings)
            all_matches.extend(stage2_matches)

        # --- Stage 3: Match using AI for remaining items ---
        if unmatched_events and unmatched_meetings:
            stage3_matches, unmatched_events, unmatched_meetings = self._match_by_ai(unmatched_events, unmatched_meetings)
            all_matches.extend(stage3_matches)

        logger.info(f"\n--- Matched {len(all_matches)} pairs ---")
        for event, meeting in all_matches:
            logger.info(f"  - Event: '{event.get('summary')}' matched with Meeting: '{meeting.name}'")

        final_unmatched_events_count = len(events) - len(all_matches)
        final_unmatched_meetings_count = len(meetings) - len(all_matches)

        logger.info(f"Remaining unmatched events: {final_unmatched_events_count}")
        logger.info(f"Remaining unmatched meetings: {final_unmatched_meetings_count}")

        return all_matches

    def process_attachment(self, event: Dict[str, Any], meeting: Meeting, dry_run: bool = False):
        """Processes a single matched event-recording pair."""
        event_summary = event.get('summary', 'No Title')
        event_id = event.get('id')
        logger.info(f"\n--- Processing Attachment for: '{event_summary}' (Event ID: {event_id}) ---")
        logger.info(f"Using matched recording: '{meeting.name}' (ID: {meeting.id}).")

        if any(keyword.lower() in event_summary.lower() for keyword in IGNORE_KEYWORDS):
            logger.info(f"Event '{event_summary}' is in the ignore list, skipping.")
            return
        
        # Process Transcript
        if self.google_api.has_attachment(event.get('attachments', []), 'Transcript for'):
            logger.info(f"Event '{event_summary}' already has a transcript attachment, skipping transcript.")
        else:
            transcript = self.connector.get_transcript(meeting)
            if transcript and transcript.text:
                transcript_doc_title = f"{event_summary} - Transcript"
                if dry_run:
                    logger.info(f"[DRY RUN] Would attach transcript to event '{event_summary}' with title '{transcript_doc_title}'.")
                else:
                    logger.info(f"Attaching transcript to event '{event_summary}'...")
                    self.google_api.create_and_attach_google_doc(event, transcript_doc_title, transcript.text)

        # Process AI Notes
        if self.google_api.has_attachment(event.get('attachments', []), 'AI Notes for'):
            logger.info(f"Event '{event_summary}' already has an AI Notes attachment, skipping notes.")
        else:
            # In the new flow, we always use the raw transcript text.
            # The get_notes method is deprecated for these connectors.
            transcript = self.connector.get_transcript(meeting)
            if transcript and transcript.text:
                logger.info(f"Using raw file content for '{meeting.name}'.")
                # Use the meeting's name (derived from filename) for the doc title
                notes_doc_title = f"Notes for {meeting.name}"
                if not dry_run:
                    logger.info(f"Attaching notes to event '{event_summary}'...")
                    self.google_api.create_and_attach_google_doc(event, notes_doc_title, transcript.text)

    def _process_matches(self, matched_pairs: List[Tuple[Dict[str, Any], Meeting]], dry_run: bool):
        """Processes matched pairs to generate notes and attach them to calendar events."""
        if not matched_pairs:
            return

        logger.info("\n--- Step 4: Processing matched pairs ---")
        for event, meeting in matched_pairs:
            event_summary = event.get('summary', 'Untitled Event')

            # Check if event already has our notes attached
            if self.google_api.has_attachment(event.get('attachments', []), 'Notes for'):
                logger.info(f"Event '{event_summary}' already has a notes attachment, skipping.")
                continue

            # In the new flow, we always use the raw transcript text.
            transcript = self.connector.get_transcript(meeting)
            if not transcript or not transcript.text:
                logger.warning(f"Skipping attachment for '{meeting.name}' because it has no content.")
                continue

            logger.info(f"Using raw file content for '{meeting.name}'.")
            notes_doc_title = f"Notes for {meeting.name}"
            if dry_run:
                logger.info(f"[DRY RUN] Would attach file content to event '{event_summary}'.")
            else:
                logger.info(f"Attaching notes to event '{event_summary}'...")
                self.google_api.create_and_attach_google_doc(event, notes_doc_title, transcript.text)

    def run_cli(self, days: float, dry_run: bool = False, force_ai: bool = False):
        """Main execution flow for the command-line interface."""
        if dry_run:
            logger.info("\n*** DRY RUN MODE ACTIVATED ***")
            logger.info("No documents will be created or attached to calendar events.")
        logger.info(f"Starting the transcript connector...")
        logger.info(f"Using connector: {self.connector.__class__.__name__}")

        if not self.authenticate():
            return

        events = self.fetch_calendar_events(days)
        if not events:
            return

        meetings = self.fetch_meetings_from_connector(days)
        if not meetings:
            return

        matched_pairs = self.match_events_and_meetings(events, meetings, force_ai=force_ai)
        if not matched_pairs:
            logger.info("\nProcess finished.")
            return

        logger.info("\n--- Starting Event Processing ---")
        logger.info(f"Processing {len(matched_pairs)} matched items.")
        for event, meeting in matched_pairs:
            self.process_attachment(event, meeting, dry_run=dry_run)

        logger.info("\nProcess finished.")

    def _match_by_ai(self, unmatched_events: List[Dict[str, Any]], unmatched_meetings: List[Meeting]) -> Tuple[List[Tuple[Dict[str, Any], Meeting]], List[Dict[str, Any]], List[Meeting]]:
        """Uses AI to match remaining events and meetings based on raw file content."""
        if not self.ai_mapper:
            return [], unmatched_events, unmatched_meetings

        logger.info("Proceeding to AI-powered matching for remaining items.")
        ai_matches = []
        still_unmatched_meetings = []

        for meeting in unmatched_meetings:
            # The new AI mapper takes the whole meeting object and the list of events
            best_match_event = self.ai_mapper.match_meeting_to_event(meeting, unmatched_events)
            
            if best_match_event:
                ai_matches.append((best_match_event, meeting))
                # Important: remove the matched event so it cannot be matched again
                unmatched_events.remove(best_match_event)
            else:
                still_unmatched_meetings.append(meeting)
        
        logger.info(f"Found {len(ai_matches)} matches using AI.")
        # Return the matches, and the remaining unmatched items
        return ai_matches, unmatched_events, still_unmatched_meetings

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
