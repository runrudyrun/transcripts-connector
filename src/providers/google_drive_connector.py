import re
import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any

from src.providers.base import BaseConnector, Meeting, Transcript, Note
from src.google_api import GoogleApi
from src.logger import logger
from src.transcript_formatter import format_transcript

class GoogleDriveConnector(BaseConnector):
    """
    Connector for fetching transcripts from a specified Google Drive folder.
    It parses files in the Grain export format.
    """

    def __init__(self, google_api: GoogleApi):
        self.google_api = google_api
        self._cache: Dict[str, Dict[str, Any]] = {}



    def get_meetings(self, days: float) -> List[Meeting]:
        """Fetches and parses files from Google Drive to find recent meetings."""
        logger.info("Fetching and parsing files from GoogleDriveConnector...")
        files = self.google_api.list_transcript_files()
        
        meetings = []
        time_threshold = datetime.now(timezone.utc) - timedelta(days=days)

        for file in files:
            file_id = file['id']
            try:
                # The entire file content is now the 'transcript'
                content = self.google_api.get_drive_file_content(file_id, file['mimeType'])
                if not content:
                    continue

                # Use file's own metadata as a fallback for matching
                file_name = file.get('name', 'Untitled')
                # Google Drive API returns createdTime in RFC 3339 format
                created_time_str = file.get('createdTime')
                start_time = datetime.fromisoformat(created_time_str.replace('Z', '+00:00'))

                if start_time < time_threshold:
                    continue # Skip files that are too old
                
                # The 'original_data' now holds the raw content of the file
                meeting_data = {'raw_content': content}
                self._cache[file_id] = meeting_data

                meeting = Meeting(
                    id=file_id,
                    name=file_name.rsplit('.', 1)[0], # Use filename as title
                    start_time=start_time,
                    original_data=meeting_data
                )
                meetings.append(meeting)

            except Exception as e:
                logger.error(f"Failed to process file '{file.get('name')}' (ID: {file_id}): {e}", exc_info=True)
        
        logger.info(f"Found {len(meetings)} valid and recent meetings in Google Drive.")
        return meetings

    def get_transcript(self, meeting: Meeting) -> Optional[Transcript]:
        """Retrieves the raw transcript text from the cached data."""
        data = self._cache.get(meeting.id)
        if not data or 'raw_content' not in data:
            return None
        
        # The formatter is no longer needed here, as we pass raw text to the AI
        return Transcript(text=data['raw_content'], original_data=data)

    def get_notes(self, meeting: Meeting) -> Optional[Note]:
        """This connector does not generate separate notes from raw files."""
        return None
