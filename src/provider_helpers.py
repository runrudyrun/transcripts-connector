# src/provider_helpers.py

from datetime import datetime, timezone
from .logger import logger

def get_conference_id(meeting):
    """Extracts the conference ID from a meeting object from any provider."""
    source = meeting.get('source')
    if source == 'tldv':
        return meeting.get('extraProperties', {}).get('conferenceId')
    elif source == 'fireflies':
        # Fireflies API response for 'id' within 'organizer_email' might be the meeting link
        # or a specific conference ID. This needs verification with actual API docs.
        # Assuming it's in a 'conference' object for now.
        return meeting.get('conference', {}).get('id')
    return None

def get_start_time(meeting):
    """Extracts the start time (as a datetime object) from a meeting object."""
    source = meeting.get('source')
    try:
        if source == 'tldv':
            start_str = meeting.get('recordingStartedAt')
            if start_str:
                return datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        elif source == 'fireflies':
            # Fireflies uses a Unix timestamp in milliseconds for the 'date' field.
            start_timestamp = meeting.get('date')
            if start_timestamp:
                return datetime.fromtimestamp(int(start_timestamp) / 1000, tz=timezone.utc)
    except (ValueError, TypeError) as e:
        logger.error(f"Could not parse start time for meeting {meeting.get('id')} from {source}: {e}")
    return None

def get_meeting_name(meeting):
    """Extracts the meeting name/title from a meeting object."""
    source = meeting.get('source')
    if source == 'tldv':
        return meeting.get('name')
    elif source == 'fireflies':
        return meeting.get('title')
    return 'Unknown Meeting'

def get_meeting_id(meeting):
    """Extracts the unique ID of the meeting object."""
    # Both tldv and fireflies seem to use 'id' for their primary identifier.
    return meeting.get('id')
