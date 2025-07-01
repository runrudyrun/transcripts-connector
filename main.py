import os
from datetime import datetime
from dotenv import load_dotenv
from src.logger import logger
from src.google_auth import get_credentials
from src.tldv_api import get_meetings, get_transcript_by_meeting_id
from src.transcript_formatter import format_transcript
from src.google_docs_api import create_google_doc, share_file_publicly
from src.google_calendar_api import get_calendar_events, attach_document_to_event, get_event_details

def main():
    """Main function to orchestrate the transcript processing workflow."""
    logger.info("Starting the transcript connector...")

    try:
        load_dotenv()

        logger.info("Step 1: Authenticating with Google...")
        creds = get_credentials()
        if not creds:
            logger.error("Failed to get Google credentials. Exiting.")
            return
        logger.info("Successfully authenticated with Google.")

        logger.info("Step 2: Fetching calendar events...")
        calendar_events = get_calendar_events(creds)
        if calendar_events is None:
            logger.error("Could not fetch calendar events. Exiting.")
            return

        logger.info("Step 3: Fetching meetings from TLDV...")
        meetings_data = get_meetings()
        if not meetings_data or 'results' not in meetings_data:
            logger.error("Could not fetch meetings from TLDV. Exiting.")
            return
        
        tldv_meetings = {m.get('extraProperties', {}).get('conferenceId'): m for m in meetings_data['results'] if m.get('extraProperties', {}).get('conferenceId')}
        logger.info(f"Found {len(tldv_meetings)} TLDV meetings with conference IDs.")

        shared_drive_id = os.getenv('SHARED_DRIVE_ID')
        folder_id = os.getenv('SHARED_DRIVE_FOLDER_ID')
        if shared_drive_id:
            if folder_id:
                logger.info(f"Shared Drive ID: {shared_drive_id}, Folder ID: {folder_id}. Documents will be created in this folder.")
            else:
                logger.info(f"Shared Drive ID found: {shared_drive_id}. Documents will be created in the drive's root.")
        else:
            logger.info("No Shared Drive ID found. Documents will be created in the user's 'My Drive'.")

        logger.info("\n--- Starting Event Processing ---")
        for event in calendar_events:
            try:
                event_name = event.get('summary')
                conference_id = event.get('conferenceId')
                logger.info(f"\nProcessing event: '{event_name}' (ID: {event.get('id')})")

                if not conference_id:
                    logger.info(f"Event '{event_name}' has no conference ID. Skipping.")
                    continue

                # Refined filter for confidential meetings (1-on-1s, reviews, etc.)
                attendees = [att for att in event.get('attendees', []) if not att.get('resource', False)]
                title_lower = event_name.lower() if event_name else ''

                # Keywords that indicate a private or 1-on-1 meeting.
                confidential_keywords = ['1:1', '1-1', 'one-on-one', 'one to one', 'catch-up', 'performance review']

                is_confidential_by_title = any(keyword in title_lower for keyword in confidential_keywords)
                is_confidential_by_size = len(attendees) == 2

                if is_confidential_by_title or is_confidential_by_size:
                    reason = "title keyword" if is_confidential_by_title else "attendee count"
                    logger.info(f"Event '{event_name}' appears to be a confidential meeting (reason: {reason}). Skipping.")
                    continue

                # Check if a transcript is already attached to avoid duplication.
                doc_title_prefix = f"[ANAIT]__Transcript for {event_name}"
                if any(att.get('title', '').startswith(doc_title_prefix) for att in event.get('attachments', [])):
                    logger.info(f"Event '{event_name}' already has a transcript with this prefix. Skipping.")
                    continue

                matching_meeting = tldv_meetings.get(conference_id)
                if not matching_meeting:
                    logger.info(f"No matching TLDV recording found for event '{event_name}'. Skipping.")
                    continue

                meeting_id = matching_meeting.get('id')
                logger.info(f"Found matching TLDV meeting: '{matching_meeting.get('name')}' (ID: {meeting_id}). Fetching transcript...")
                transcript_data = get_transcript_by_meeting_id(meeting_id)
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
