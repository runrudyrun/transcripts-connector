# This file will contain functions to interact with the Google Calendar API.
import datetime
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError
from src.logger import logger

def find_concluded_events(creds, days_ago=7):
    """Finds events that have concluded in the last specified number of days."""
    try:
        service = build('calendar', 'v3', credentials=creds)
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        time_min = (now_utc - datetime.timedelta(days=days_ago)).isoformat() + 'Z'
        time_max = now_utc.isoformat() + 'Z'

        logger.info(f"Searching for concluded events from the last {days_ago} days...")
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime',
            fields='items(id,summary,start,end,attendees,attachments,conferenceData(conferenceId))'
        ).execute()

        events = events_result.get('items', [])
        if not events:
            logger.info("No events found in the specified time range.")
            return []

        # Filter to ensure we only process events that have actually ended.
        concluded_events = []
        now_aware = datetime.datetime.now(datetime.timezone.utc)
        for event in events:
            end_time_str = event.get('end', {}).get('dateTime')
            if end_time_str:
                end_time = datetime.datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                if end_time < now_aware:
                    concluded_events.append(event)
        
        logger.info(f"Found {len(concluded_events)} concluded events to process.")
        return concluded_events

    except RefreshError as e:
        logger.error(f"Google credentials have expired or been revoked: {e}. Please re-authenticate by deleting token.json and running again.")
        return None
    except Exception as e:
        logger.error(f"An error occurred with the Google Calendar API: {e}", exc_info=True)
        return None

def attach_document_to_event(creds, event_id, file_id, file_details):
    """Attaches a Google Doc to a calendar event using a manually constructed URL."""
    try:
        service = build('calendar', 'v3', credentials=creds)
        
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        
        attachments = event.get('attachments', [])

        file_title = file_details.get('name')

        # Check if an attachment with the same title already exists
        if any(att.get('title') == file_title for att in attachments):
            logger.info(f"Attachment '{file_title}' already exists for event {event_id}. Skipping.")
            return None

        clean_file_url = f"https://docs.google.com/document/d/{file_id}/edit"
        logger.info(f"Using manually constructed clean URL for attachment: {clean_file_url}")

        new_attachment = {
            'fileUrl': clean_file_url,
            'title': file_title,
            'mimeType': file_details.get('mimeType')
        }
        attachments.append(new_attachment)

        body = {
            'attachments': attachments
        }
        
        updated_event = service.events().patch(
            calendarId='primary',
            eventId=event_id,
            body=body,
            supportsAttachments=True
        ).execute()
        
        logger.info(f"Successfully attached document. New event version: {updated_event.get('etag')}")
        return True

    except Exception as e:
        logger.error(f"An error occurred while attaching document to event {event_id}: {e}", exc_info=True)
        return None

def get_event_details(creds, event_id):
    """Fetches detailed information for a single event."""
    try:
        service = build('calendar', 'v3', credentials=creds)
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        return event
    except Exception as e:
        logger.error(f"Failed to fetch details for event {event_id}: {e}", exc_info=True)
        return None

def remove_attachment_from_event(creds, event_id, attachment_title):
    """Removes a specific attachment from a calendar event by its title."""
    try:
        service = build('calendar', 'v3', credentials=creds)
        
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        attachments = event.get('attachments', [])
        
        # Find and remove the attachment with the matching title
        updated_attachments = [att for att in attachments if att.get('title') != attachment_title]
        
        if len(updated_attachments) == len(attachments):
            logger.warning(f"Attachment with title '{attachment_title}' not found in event {event_id}. Nothing to remove.")
            return False

        body = {'attachments': updated_attachments}
        
        service.events().patch(
            calendarId='primary',
            eventId=event_id,
            body=body,
            supportsAttachments=True
        ).execute()
        
        logger.info(f"Successfully removed attachment '{attachment_title}' from event {event_id}.")
        return True

    except Exception as e:
        logger.error(f"Failed to remove attachment from event {event_id}: {e}", exc_info=True)
        return False
