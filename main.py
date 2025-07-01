from dotenv import load_dotenv
from src.logger import logger
from src.google_auth import get_credentials
from src.tldv_api import get_meetings, get_transcript_by_meeting_id
from src.transcript_formatter import format_transcript
from src.google_docs_api import create_document, insert_text, share_document
from src.google_calendar_api import get_calendar_events, add_link_to_event_description

def main():
    """Main function to run the transcript connector."""
    logger.info("Starting the transcript connector...")

    try:
        # Load environment variables from .env file
        load_dotenv()

        logger.info("Step 1: Authenticating with Google...")
        creds = get_credentials() # Uncomment when OAuth is fixed
        # creds = "dummy_credentials" # Using a stub for now
        if not creds:
            logger.error("Failed to get Google credentials. Exiting.")
            return
        logger.info("Successfully authenticated with Google.")

        logger.info("Step 2: Fetching calendar events...")
        calendar_events = get_calendar_events(creds)

        logger.info("Step 3: Fetching meetings from TLDV...")
        meetings_data = get_meetings()
        if not meetings_data or 'results' not in meetings_data:
            logger.error("Could not fetch meetings from TLDV. Exiting.")
            return
        
        tldv_meetings = {m.get('extraProperties', {}).get('conferenceId'): m for m in meetings_data['results'] if m.get('extraProperties', {}).get('conferenceId')}
        logger.info(f"Found {len(tldv_meetings)} TLDV meetings with conference IDs.")

        # 4. Process each calendar event
        for event in calendar_events:
            event_name = event.get('summary')
            conference_id = event.get('conferenceId')
            logger.info(f"Processing event: '{event_name}' (Conference ID: {conference_id})")

            try:
                # Check for existing transcript link in the description
                description = event.get('description', '')
                if description and 'Transcript:' in description:
                    logger.info(f"Event '{event_name}' already has a transcript link. Skipping.")
                    continue

                # Find matching TLDV meeting
                matching_meeting = tldv_meetings.get(conference_id)
                if not matching_meeting:
                    logger.warning(f"No matching TLDV recording found for event '{event_name}'. Skipping.")
                    continue

                # 5. Get TLDV transcript
                meeting_id = matching_meeting.get('id')
                logger.info(f"Found matching TLDV meeting: '{matching_meeting.get('name')}' (ID: {meeting_id}). Fetching transcript...")
                transcript_data = get_transcript_by_meeting_id(meeting_id)
                if not transcript_data:
                    logger.warning(f"Could not fetch transcript for meeting {meeting_id}. Skipping.")
                    continue

                # 6. Format transcript
                logger.info("Formatting transcript...")
                formatted_transcript = format_transcript(transcript_data)

                # 7. Create Google Doc
                logger.info("Creating Google Doc...")
                doc_title = f"Transcript for {event_name}"
                document_id = create_document(creds, doc_title)
                if not document_id:
                    logger.error(f"Failed to create Google Doc for event '{event_name}'. Skipping.")
                    continue

                # 8. Insert transcript into Google Doc
                logger.info("Inserting transcript into Google Doc...")
                insert_text(creds, document_id, formatted_transcript)

                # 9. Attach Google Doc to Calendar event
                logger.info("Attaching document to calendar event...")
                document_url = f"https://docs.google.com/document/d/{document_id}"
                add_link_to_event_description(creds, event.get('id'), document_url)

                # 10. Share document with invitees
                invitees = event.get('invitees', [])
                if invitees:
                    emails = [invitee['email'] for invitee in invitees]
                    logger.info("Sharing document with invitees...")
                    share_document(creds, document_id, emails)

            except Exception as e:
                logger.error(f"An error occurred while processing event '{event_name}': {e}", exc_info=True)

    except Exception as e:
        logger.critical(f"A critical error occurred in the main process: {e}", exc_info=True)
    
    logger.info("Process finished.")

if __name__ == "__main__":
    main()
