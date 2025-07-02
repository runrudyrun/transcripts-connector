# src/providers/fireflies.py

import os
import requests
from ..logger import logger

API_KEY = os.environ.get("FIREFLIES_API_KEY")
GRAPHQL_URL = "https://api.fireflies.ai/graphql"

def _run_graphql_query(query):
    """Helper function to run a GraphQL query against the Fireflies API."""
    if not API_KEY:
        logger.error("FIREFLIES_API_KEY is not set.")
        return None

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(GRAPHQL_URL, headers=headers, json={'query': query})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error querying Fireflies GraphQL API: {e}")
        return None

def get_meetings():
    """Fetches a list of meetings (transcripts) from the Fireflies.ai API using GraphQL."""
    query = """
        query {
            transcripts {
                id
                title
                date
                conference(provider: "zoom") { 
                    metadata
                }
            }
        }
    """
    json_response = _run_graphql_query(query)
    if not json_response or 'data' not in json_response or not json_response['data'].get('transcripts'):
        logger.warning("No meetings found or error in Fireflies API response.")
        return []

    meetings = json_response['data']['transcripts']
    logger.info(f"Found {len(meetings)} meetings from Fireflies.ai.")
    for meeting in meetings:
        meeting['source'] = 'fireflies'
        # Attempt to extract conferenceId from metadata
        if meeting.get('conference') and meeting['conference'].get('metadata'):
            meeting['conferenceId'] = meeting['conference']['metadata'].get('conferenceId')
    return meetings

def get_transcript_by_meeting_id(meeting_id):
    """Fetches the transcript for a specific meeting by its ID using GraphQL."""
    query = f"""
        query {{
            transcript(id: \"{meeting_id}\") {{
                sentences {{
                    text
                }}
            }}
        }}
    """
    json_response = _run_graphql_query(query)
    if not json_response or 'data' not in json_response or not json_response['data'].get('transcript'):
        logger.error(f"Could not fetch transcript for meeting {meeting_id}.")
        return None

    sentences = json_response['data']['transcript'].get('sentences', [])
    full_transcript = "\n".join([sentence['text'] for sentence in sentences])
    logger.info(f"Successfully fetched and formatted transcript for meeting {meeting_id}.")
    return full_transcript
