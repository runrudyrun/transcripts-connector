import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from src.logger import logger
from src.google_auth import get_credentials
from src.providers import get_all_meetings, get_transcript
from src.provider_helpers import get_conference_id, get_start_time, get_meeting_name, get_meeting_id
from src.transcript_formatter import format_transcript
from src.google_docs_api import create_google_doc, share_file_publicly
from src.google_calendar_api import find_concluded_events, attach_document_to_event, get_event_details

def main():
    """Main function to orchestrate the transcript processing workflow."""
    logger.info("Starting the transcript connector...")
    try:
        load_dotenv()

        logger.info("Step 1: Authenticating with Google...")
        creds = get_credentials()
        if not creds:
            return
        logger.info("Successfully authenticated with Google.")

        logger.info("Step 2: Fetching concluded calendar events from the last 7 days...")
        calendar_events = find_concluded_events(creds, days_ago=7)
        if not calendar_events:
            logger.info("No recently concluded events found to process.")
            return

        logger.info("Step 3: Fetching meetings from all enabled providers...")
        all_meetings = get_all_meetings()
        if not all_meetings:
            logger.warning("No meetings found in TLDV.")
            return

        # --- Two-Stage Matching Logic ---
        logger.info("\n--- Matching Calendar events with TLDV recordings ---")
        matched_pairs = []
        unmatched_events = list(calendar_events)
        unmatched_meetings = list(all_meetings)

        # Stage 1: Match by Conference ID
        events_by_conf_id = {e.get('conferenceData', {}).get('conferenceId'): e for e in unmatched_events if e.get('conferenceData', {}).get('conferenceId')}
        meetings_by_conf_id = {get_conference_id(m): m for m in unmatched_meetings if get_conference_id(m)}
        
        conf_ids_to_match = set(events_by_conf_id.keys()) & set(meetings_by_conf_id.keys())
        for conf_id in conf_ids_to_match:
            matched_pairs.append((events_by_conf_id[conf_id], meetings_by_conf_id[conf_id]))
            logger.info(f"Matched by Conference ID: '{events_by_conf_id[conf_id].get('summary')}'")
        
        # Remove matched items from the pools for the next stage
        unmatched_events = [e for e in unmatched_events if e.get('conferenceData', {}).get('conferenceId') not in conf_ids_to_match]
        unmatched_meetings = [m for m in unmatched_meetings if get_conference_id(m) not in conf_ids_to_match]
        logger.info(f"{len(conf_ids_to_match)} pairs matched by Conference ID.")

        # Stage 2: Match by Time Proximity
        logger.info(f"Attempting to match {len(unmatched_events)} remaining events and {len(unmatched_meetings)} recordings by time...")
        time_match_threshold = timedelta(minutes=5)
        
        temp_unmatched_meetings = []
        for meeting in unmatched_meetings:
            best_match_event = None
            smallest_diff = time_match_threshold

            meeting_start_time = get_start_time(meeting)
            if not meeting_start_time: continue

            for event in unmatched_events:
                event_start_str = event.get('start', {}).get('dateTime')
                if not event_start_str: continue
                event_start_time = datetime.datetime.fromisoformat(event_start_str.replace('Z', '+00:00'))

                time_diff = abs(meeting_start_time - event_start_time)
                if time_diff < smallest_diff:
                    smallest_diff = time_diff
                    best_match_event = event
            
            if best_match_event:
                logger.info(f"Matched by Time: '{best_match_event.get('summary')}' and '{get_meeting_name(meeting)}' from {meeting.get('source')} (diff: {smallest_diff})")
                matched_pairs.append((best_match_event, meeting))
                unmatched_events.remove(best_match_event)
            else:
                temp_unmatched_meetings.append(meeting)
        
        unmatched_meetings = temp_unmatched_meetings
        logger.info(f"{len(matched_pairs) - len(conf_ids_to_match)} pairs matched by time.")

        if not matched_pairs:
            logger.info("No matching events and recordings found. Exiting.")
            return

        # --- Processing Matched Pairs ---
        logger.info("\n--- Starting Event Processing ---")
        shared_drive_id = os.getenv('SHARED_DRIVE_ID')
        folder_id = os.getenv('SHARED_DRIVE_FOLDER_ID')

        for event, meeting in matched_pairs:
            try:
                event_name = event.get('summary')
                logger.info(f"\nProcessing pair: '{event_name}' (Event ID: {event.get('id')})")

                attendees = [att for att in event.get('attendees', []) if not att.get('resource', False)]
                title_lower = event_name.lower() if event_name else ''
                confidential_keywords = ['1:1', '1-1', 'one-on-one', 'one to one', 'catch-up', 'performance review']
                is_confidential_by_title = any(keyword in title_lower for keyword in confidential_keywords)
                is_confidential_by_size = len(attendees) == 2
                if is_confidential_by_title or is_confidential_by_size:
                    reason = "title keyword" if is_confidential_by_title else "attendee count"
                    logger.info(f"Event '{event_name}' appears to be a confidential meeting (reason: {reason}). Skipping.")
                    continue

                doc_title_prefix = f"ANAIT: Transcript for {event_name}"
                if any(att.get('title', '').startswith(doc_title_prefix) for att in event.get('attachments', [])):
                    logger.info(f"Event '{event_name}' already has a transcript with this prefix. Skipping.")
                    continue

                meeting_id = get_meeting_id(meeting)
                provider_name = meeting.get('source', 'unknown').upper()
                logger.info(f"Using matched {provider_name} meeting: '{get_meeting_name(meeting)}' (ID: {meeting_id}). Fetching transcript...")
                transcript_data = get_transcript(meeting)
                if not transcript_data:
                    logger.warning(f"Could not fetch transcript for meeting {meeting_id}. Skipping.")
                    continue

                logger.info("Formatting transcript...")
                formatted_transcript = format_transcript(transcript_data)

                doc_title = f"{doc_title_prefix} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
                
                logger.info(f"Creating Google Doc: '{doc_title}'")
                doc_id = create_google_doc(creds, doc_title, formatted_transcript, shared_drive_id, folder_id)
                if not doc_id:
                    logger.warning(f"Skipping event {event['id']} due to document creation failure.")
                    continue

                logger.info(f"Sharing document {doc_id} and getting details...")
                file_details = share_file_publicly(creds, doc_id)
                if not file_details:
                    logger.error(f"Could not share or retrieve details for doc {doc_id}. Skipping attachment.")
                    continue
                
                logger.info(f"Attaching document '{file_details.get('name')}' to calendar event...")
                attach_document_to_event(creds, event.get('id'), doc_id, file_details)

                logger.info(f"DIAGNOSTIC: Fetching event details for '{event.get('id')}' post-attachment.")
                event_details_post = get_event_details(creds, event.get('id'))
                if event_details_post and 'attachments' in event_details_post:
                    logger.info(f"DIAGNOSTIC: Found attachments: {event_details_post['attachments']}")
                else:
                    logger.info("DIAGNOSTIC: No attachments found post-attachment.")

            except Exception as e:
                logger.error(f"An error occurred while processing event '{event.get('summary', 'Unknown')}': {e}", exc_info=True)

    except Exception as e:
        logger.critical(f"An unexpected error occurred in the main function: {e}", exc_info=True)

    logger.info("Process finished.")

if __name__ == "__main__":
    main()
