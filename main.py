import os
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
from src.logger import logger
from src.google_auth import get_credentials
from src.tldv_api import get_meetings, get_transcript_by_meeting_id, get_highlights_by_meeting_id
from src.transcript_formatter import format_transcript, format_highlights
from src.google_docs_api import create_google_doc, share_file_publicly
from src.google_calendar_api import find_concluded_events, attach_document_to_event, get_event_details

def main():
    """Main function to orchestrate the transcript processing workflow."""
    parser = argparse.ArgumentParser(description="Fetch tldv transcripts and attach them to Google Calendar events.")
    parser.add_argument("--days", type=int, help="Number of past days to search for meetings.")
    parser.add_argument("--hours", type=int, help="Number of past hours to search for meetings.")
    args = parser.parse_args()

    logger.info("Starting the transcript connector...")
    try:
        load_dotenv()

        logger.info("Step 1: Authenticating with Google...")
        creds = get_credentials()
        if not creds:
            return
        logger.info("Successfully authenticated with Google.")

        time_delta = timedelta(days=7) # Default
        if args.hours:
            time_delta = timedelta(hours=args.hours)
            logger.info(f"Searching for events in the last {args.hours} hours...")
        elif args.days:
            time_delta = timedelta(days=args.days)
            logger.info(f"Searching for events in the last {args.days} days...")
        else:
            logger.info("Defaulting to search for events in the last 7 days...")

        logger.info("Step 2: Fetching concluded calendar events...")
        calendar_events = find_concluded_events(creds, time_delta=time_delta)
        if not calendar_events:
            logger.info("No recently concluded events found to process.")
            return

        logger.info("Step 3: Fetching meetings from TLDV...")
        tldv_meetings_raw = get_meetings().get('results', [])
        if not tldv_meetings_raw:
            logger.warning("No meetings found in TLDV.")
            return

        # --- Two-Stage Matching Logic ---
        logger.info("\n--- Matching Calendar events with TLDV recordings ---")
        matched_pairs = []
        unmatched_events = list(calendar_events)
        unmatched_tldv = list(tldv_meetings_raw)

        # Stage 1: Match by Conference ID
        events_by_conf_id = {e.get('conferenceData', {}).get('conferenceId'): e for e in unmatched_events if e.get('conferenceData', {}).get('conferenceId')}
        tldv_by_conf_id = {m.get('extraProperties', {}).get('conferenceId'): m for m in unmatched_tldv if m.get('extraProperties', {}).get('conferenceId')}
        
        conf_ids_to_match = set(events_by_conf_id.keys()) & set(tldv_by_conf_id.keys())
        for conf_id in conf_ids_to_match:
            matched_pairs.append((events_by_conf_id[conf_id], tldv_by_conf_id[conf_id]))
            logger.info(f"Matched by Conference ID: '{events_by_conf_id[conf_id].get('summary')}'")
        
        # Remove matched items from the pools for the next stage
        unmatched_events = [e for e in unmatched_events if e.get('conferenceData', {}).get('conferenceId') not in conf_ids_to_match]
        unmatched_tldv = [m for m in unmatched_tldv if m.get('extraProperties', {}).get('conferenceId') not in conf_ids_to_match]
        logger.info(f"{len(conf_ids_to_match)} pairs matched by Conference ID.")

        # Stage 2: Match by Time Proximity
        logger.info(f"Attempting to match {len(unmatched_events)} remaining events and {len(unmatched_tldv)} recordings by time...")
        time_match_threshold = timedelta(minutes=5)
        
        temp_unmatched_tldv = []
        for tldv_meeting in unmatched_tldv:
            best_match_event = None
            smallest_diff = time_match_threshold

            tldv_start_str = tldv_meeting.get('recordingStartedAt')
            if not tldv_start_str: continue
            tldv_start_time = datetime.fromisoformat(tldv_start_str.replace('Z', '+00:00'))

            for event in unmatched_events:
                event_start_str = event.get('start', {}).get('dateTime')
                if not event_start_str: continue
                event_start_time = datetime.fromisoformat(event_start_str.replace('Z', '+00:00'))

                time_diff = abs(tldv_start_time - event_start_time)
                if time_diff < smallest_diff:
                    smallest_diff = time_diff
                    best_match_event = event
            
            if best_match_event:
                logger.info(f"Matched by Time: '{best_match_event.get('summary')}' and TLDV recording '{tldv_meeting.get('name')}' (diff: {smallest_diff})")
                matched_pairs.append((best_match_event, tldv_meeting))
                unmatched_events.remove(best_match_event)
            else:
                temp_unmatched_tldv.append(tldv_meeting)
        
        unmatched_tldv = temp_unmatched_tldv
        logger.info(f"{len(matched_pairs) - len(conf_ids_to_match)} pairs matched by time.")

        if not matched_pairs:
            logger.info("No matching events and recordings found. Exiting.")
            return

        # --- Processing Matched Pairs ---
        logger.info("\n--- Starting Event Processing ---")
        shared_drive_id = os.getenv('SHARED_DRIVE_ID')
        folder_id = os.getenv('SHARED_DRIVE_FOLDER_ID')
        ignore_keywords_str = os.getenv('IGNORE_KEYWORDS', '1:1,1-1,catch-up')
        ignore_keywords = [keyword.strip().lower() for keyword in ignore_keywords_str.split(',')]
        logger.info(f"Using ignore keywords: {ignore_keywords}")

        for event, tldv_meeting in matched_pairs:
            try:
                event_name = event.get('summary')
                logger.info(f"\nProcessing pair: '{event_name}' (Event ID: {event.get('id')})")

                title_lower = event_name.lower() if event_name else ''
                if any(keyword in title_lower for keyword in ignore_keywords):
                    logger.info(f"Event '{event_name}' title contains an ignore keyword. Skipping.")
                    continue

                meeting_id = tldv_meeting.get('id')
                logger.info(f"Using matched TLDV meeting: '{tldv_meeting.get('name')}' (ID: {meeting_id}).")

                # --- Process Transcript ---
                transcript_data = get_transcript_by_meeting_id(meeting_id)
                if transcript_data:
                    transcript_title_prefix = f"Transcript for {event_name}"
                    if any(att.get('title', '').startswith(transcript_title_prefix) for att in event.get('attachments', [])):
                        logger.info(f"Event '{event_name}' already has a transcript. Skipping transcript creation.")
                    else:
                        logger.info("Transcript found. Processing...")
                        formatted_transcript = format_transcript(transcript_data)
                        doc_title = f"{transcript_title_prefix} ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
                        logger.info(f"Creating Google Doc for transcript: '{doc_title}'")
                        doc_id = create_google_doc(creds, doc_title, formatted_transcript, shared_drive_id, folder_id)
                        if doc_id:
                            file_details = share_file_publicly(creds, doc_id)
                            if file_details:
                                attach_document_to_event(creds, event.get('id'), doc_id, file_details)
                else:
                    logger.info("No transcript data found for this meeting.")

                # --- Process Highlights (AI Notes) ---
                highlights_data = get_highlights_by_meeting_id(meeting_id)
                if highlights_data:
                    notes_title_prefix = f"AI Notes for {event_name}"
                    if any(att.get('title', '').startswith(notes_title_prefix) for att in event.get('attachments', [])):
                        logger.info(f"Event '{event_name}' already has AI Notes. Skipping notes creation.")
                    else:
                        logger.info("AI Notes found. Processing...")
                        formatted_highlights = format_highlights(highlights_data)
                        doc_title = f"{notes_title_prefix} ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
                        logger.info(f"Creating Google Doc for AI Notes: '{doc_title}'")
                        doc_id = create_google_doc(creds, doc_title, formatted_highlights, shared_drive_id, folder_id)
                        if doc_id:
                            file_details = share_file_publicly(creds, doc_id)
                            if file_details:
                                attach_document_to_event(creds, event.get('id'), doc_id, file_details)
                else:
                    logger.info("No AI Notes data found for this meeting.")

            except Exception as e:
                logger.error(f"An error occurred while processing event '{event.get('summary', 'Unknown')}': {e}", exc_info=True)

    except Exception as e:
        logger.critical(f"An unexpected error occurred in the main function: {e}", exc_info=True)

    logger.info("Process finished.")

if __name__ == "__main__":
    main()
