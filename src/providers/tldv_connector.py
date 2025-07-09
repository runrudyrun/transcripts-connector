import os
import requests
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from src.logger import logger
from src.providers.base import BaseConnector, Meeting, Transcript, Note
from src.transcript_formatter import format_transcript, format_highlights

API_BASE_URL = "https://pasta.tldv.io/v1alpha1"

class TldvConnector(BaseConnector):
    """Connector for the TLDV API."""

    def __init__(self):
        self.api_key = os.environ.get("TLDV_API_KEY")
        if not self.api_key:
            raise ValueError("Missing TLDV_API_KEY environment variable")
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def _make_request(self, url: str) -> Optional[Dict[str, Any]]:
        """Helper method to make GET requests to the TLDV API."""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 404:
                logger.warning(f"Resource not found at {url} (404 Not Found).")
            else:
                logger.error(f"HTTP error occurred for {url}: {http_err}")
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred while requesting {url}: {e}")
        return None

    def get_meetings(self, days: float) -> List[Meeting]:
        """Fetches meetings from the TLDV API within a specified number of past days."""
        from_date = datetime.now() - timedelta(days=days)
        url = f"{API_BASE_URL}/meetings?from_date={from_date.isoformat()}"
        meetings_data = self._make_request(url)
        if not meetings_data or 'results' not in meetings_data:
            return []

        meetings = []
        for meeting_data in meetings_data['results']:
            start_time_str = meeting_data.get('happenedAt')
            if not start_time_str:
                continue

            # The date format is like 'Wed Jul 02 2025 14:19:45 GMT+0000 (Coordinated Universal Time)'
            # We need to parse it correctly.
            try:
                # Strip the timezone name part like '(Coordinated Universal Time)'
                cleaned_str = start_time_str.split('(')[0].strip()
                start_time = datetime.strptime(cleaned_str, "%a %b %d %Y %H:%M:%S GMT%z")
            except ValueError:
                logger.warning(f"Could not parse date: {start_time_str}")
                continue
            
            meetings.append(
                Meeting(
                    id=meeting_data.get('id'),
                    name=meeting_data.get('name'),
                    start_time=start_time,
                    original_data=meeting_data
                )
            )
        return meetings

    def get_transcript(self, meeting: Meeting) -> Optional[Transcript]:
        """
        Fetches and formats the transcript for a specific meeting.
        """
        transcript_data = self._make_request(f"{API_BASE_URL}/meetings/{meeting.id}/transcript")
        if not transcript_data:
            return None

        formatted_text = format_transcript(transcript_data, meeting.name)
        return Transcript(text=formatted_text, original_data=transcript_data)

    def get_notes(self, meeting: Meeting) -> Optional[Note]:
        """
        Fetches and formats the highlights (AI Notes) for a specific meeting.
        """
        highlights_data = self._make_request(f"{API_BASE_URL}/meetings/{meeting.id}/highlights")
        if not highlights_data:
            return None

        formatted_content = format_highlights(highlights_data)
        if not formatted_content:
            return None
        return Note(content=formatted_content, original_data=highlights_data)
