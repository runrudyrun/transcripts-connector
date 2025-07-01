# This file will contain functions to interact with the Google Calendar API.
from src.logger import logger

# TODO: Replace with actual Google Calendar API calls

def get_calendar_events(creds):
    """(Stub) Fetches upcoming events from Google Calendar."""
    logger.info("(Stub) Fetching events from Google Calendar.")

    # This is a mock event. The 'conferenceId' should match the one in the
    # 'extraProperties' of a TLDV meeting object to test the matching logic.
    # To find a real conferenceId, you can inspect the output of get_meetings()
    # in tldv_api.py and pick one.
    mock_events = [
        {
            'summary': '1:1 Kolya with Roman Ianvarev about future teams',
            'id': 'b1ddq0btuhcvqr98bt0v831g3h',
            # Using a real conferenceId from the TLDV debug output
            'conferenceId': 'phg-akrz-ctx',
            'invitees': [
                {'email': 'participant1@example.com'},
                {'email': 'participant2@example.com'}
            ] 
        }
    ]
    logger.info(f"(Stub) Found {len(mock_events)} events.")
    return mock_events

def get_event_attachments(creds, event_id):
    """(Stub) Checks for attachments on a calendar event."""
    logger.info(f"(Stub) Checking for attachments on event {event_id}.")
    # Return an empty list to simulate no existing document
    return []

def attach_document_to_event(creds, event_id, document_url):
    """(Stub) Attaches a Google Doc to a calendar event."""
    logger.info(f"(Stub) Attaching document {document_url} to event {event_id}.")
    # TODO: Implement actual Google Calendar API call to add an attachment.
    logger.info("(Stub) Attachment complete.")
    return True
