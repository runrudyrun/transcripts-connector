# src/tldv_api.py

import os
import requests
from src.logger import logger

API_BASE_URL = "https://pasta.tldv.io/v1alpha1"


def get_meetings():
    """Fetches all meetings from the TLDV API."""
    api_key = os.environ.get("TLDV_API_KEY")
    if not api_key:
        raise ValueError("Missing TLDV_API_KEY environment variable")

    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(f"{API_BASE_URL}/meetings", headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred while fetching TLDV meetings: {e}")
        return None


def get_transcript_by_meeting_id(meeting_id):
    """Fetches the transcript for a specific meeting by its ID."""
    api_key = os.environ.get("TLDV_API_KEY")
    if not api_key:
        raise ValueError("Missing TLDV_API_KEY environment variable")

    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(f"{API_BASE_URL}/meetings/{meeting_id}/transcript", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred while fetching TLDV transcript: {e}")
        return None


def get_highlights_by_meeting_id(meeting_id: str):
    """Fetches the highlights (AI Notes) for a given meeting ID from the tldv API."""
    api_key = os.environ.get("TLDV_API_KEY")
    if not api_key:
        raise ValueError("Missing TLDV_API_KEY environment variable")

    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }

    url = f"{API_BASE_URL}/meetings/{meeting_id}/highlights"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        logger.info(f"Successfully fetched highlights for meeting {meeting_id}.")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            logger.warning(f"No highlights found for meeting {meeting_id} (404 Not Found).")
        else:
            logger.error(f"HTTP error fetching highlights for {meeting_id}: {http_err}")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request failed while fetching highlights for {meeting_id}: {req_err}")
    return None


if __name__ == "__main__":
    # This is for testing purposes. 
    # Make sure to set your TLDV_API_KEY in the .env file.
    from dotenv import load_dotenv
    from transcript_formatter import format_transcript
    load_dotenv()
    
    logger.info("Fetching TLDV meetings...")
    meetings_data = get_meetings()
    if meetings_data and meetings_data.get('results'):
        meetings = meetings_data['results']
        logger.info(f"Successfully fetched {len(meetings)} meetings.")
        
        # Get transcript for the first meeting
        first_meeting_id = meetings[0].get('id')
        if first_meeting_id:
            logger.info(f"Fetching transcript for meeting ID: {first_meeting_id}...")
            transcript_data = get_transcript_by_meeting_id(first_meeting_id)
            if transcript_data:
                logger.info("Successfully fetched transcript.")
                # The format_transcript function no longer takes meeting_name
                formatted_transcript = format_transcript(transcript_data)
                logger.info("\n--- Formatted Transcript ---\n%s\n--------------------------", formatted_transcript)
            else:
                logger.error("Failed to fetch transcript.")
    else:
        logger.error("Failed to fetch meetings or no meetings found.")
