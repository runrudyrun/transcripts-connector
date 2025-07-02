# src/providers/__init__.py

import os
import importlib
from ..logger import logger

# A mapping from provider name to module name
PROVIDER_MAP = {
    'tldv': 'src.providers.tldv',
    'fireflies': 'src.providers.fireflies',
}

def get_enabled_providers():
    """Reads the MEETING_PROVIDERS env var and returns a list of provider modules."""
    provider_names = os.getenv('MEETING_PROVIDERS', 'tldv').split(',')
    loaded_providers = []
    for name in provider_names:
        name = name.strip()
        if name in PROVIDER_MAP:
            try:
                module = importlib.import_module(PROVIDER_MAP[name])
                loaded_providers.append((name, module))
                logger.info(f"Successfully loaded provider: {name}")
            except ImportError:
                logger.error(f"Failed to load provider: {name}")
        else:
            logger.warning(f"Unknown provider specified: {name}")
    return loaded_providers

def get_all_meetings():
    """Fetches meetings from all enabled providers and merges them."""
    all_meetings = []
    for name, provider_module in get_enabled_providers():
        logger.info(f"Fetching meetings from {name}...")
        try:
            meetings = provider_module.get_meetings()
            if meetings and meetings.get('results'):
                # Add a 'source' field to each meeting for later identification
                for meeting in meetings['results']:
                    meeting['source'] = name
                all_meetings.extend(meetings['results'])
                logger.info(f"Found {len(meetings['results'])} meetings from {name}.")
            else:
                logger.warning(f"No meetings found or empty results from {name}.")
        except Exception as e:
            logger.error(f"Error fetching meetings from {name}: {e}")
    return all_meetings

def get_transcript(meeting):
    """Fetches a transcript from the appropriate provider based on the meeting's source."""
    source = meeting.get('source')
    meeting_id = meeting.get('id')
    if not source or not meeting_id:
        logger.error("Meeting object is missing 'source' or 'id'.")
        return None

    if source in PROVIDER_MAP:
        try:
            provider_module = importlib.import_module(PROVIDER_MAP[source])
            return provider_module.get_transcript_by_meeting_id(meeting_id)
        except (ImportError, AttributeError) as e:
            logger.error(f"Could not get transcript from {source}: {e}")
            return None
    else:
        logger.warning(f"Transcript fetch attempted for unknown provider: {source}")
        return None
