# This file will contain functions to interact with the Google Calendar API.
import datetime
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError
from src.logger import logger

def get_calendar_events(creds):
    """Fetches upcoming events from the user's primary Google Calendar."""
    try:
        service = build('calendar', 'v3', credentials=creds)
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        # Get events from the next 7 days
        time_max = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat() + 'Z'
        
        logger.info("Fetching events from Google Calendar for the next 7 days...")
        events_result = service.events().list(
            calendarId='primary', 
            timeMin=now,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime',
            # Request only the fields we need to be efficient
            fields='items(id,summary,attendees,attachments,conferenceData(conferenceId))'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            logger.info("No upcoming events found.")
            return []

        # Process events to extract the required info in a simple format
        processed_events = []
        for event in events:
            # Skip events without conference data or a conferenceId
            conference_data = event.get('conferenceData')
            if not conference_data or not conference_data.get('conferenceId'):
                continue
            
            processed_events.append({
                'id': event.get('id'),
                'summary': event.get('summary'),
                'conferenceId': conference_data.get('conferenceId'),
                'invitees': event.get('attendees', []),
                'attachments': event.get('attachments', [])
            })
        
        logger.info(f"Found {len(processed_events)} events with conference IDs.")
        return processed_events

    except RefreshError as e:
        logger.error(f"Google credentials have expired or been revoked: {e}. Please re-authenticate by deleting token.json and running again.")
        return None
    except Exception as e:
        logger.error(f"An error occurred with the Google Calendar API: {e}", exc_info=True)
        return None

def attach_document_to_event(creds, event_id, file_details):
    """Attaches a Google Doc to a calendar event using file details from Drive API."""
    try:
        service = build('calendar', 'v3', credentials=creds)
        
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        
        attachments = event.get('attachments', [])

        file_title = file_details.get('name')

        # Check if an attachment with the same title already exists
        if any(att.get('title') == file_title for att in attachments):
            logger.info(f"Attachment '{file_title}' already exists for event {event_id}. Skipping.")
            return None

        new_attachment = {
            'fileUrl': file_details['webViewLink'],
            'title': file_title,
            'mimeType': file_details.get('mimeType')
        }
        attachments.append(new_attachment)

        body = {
            'attachments': attachments
        }
        
        logger.info(f"Attaching document to event {event_id}... using alternateLink: {file_details.get('alternateLink')}")
        updated_event = service.events().patch(
            calendarId='primary',
            eventId=event_id,
            body=body,
            supportsAttachments=True
        ).execute()
        
        logger.info(f"Successfully attached document. New event version: {updated_event.get('etag')}")
        return True

    except Exception as e:
        logger.error(f"Failed to attach document to event {event_id}: {e}", exc_info=True)
        return False

def get_event_details(creds, event_id):
    """Fetches the full details of a single event for diagnostic purposes."""
    try:
        service = build('calendar', 'v3', credentials=creds)
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        logger.info(f"Successfully fetched details for event {event_id}")
        return event
    except Exception as e:
        logger.error(f"Failed to get details for event {event_id}: {e}", exc_info=True)
        return None
