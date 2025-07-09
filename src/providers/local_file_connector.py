import os
import json
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from src.logger import logger
from src.providers.base import BaseConnector, Meeting, Transcript, Note
from src.transcript_formatter import format_transcript

class LocalFileConnector(BaseConnector):
    """Connector for reading transcripts and notes from local files."""

    def __init__(self):
        # Get the raw path from environment variable, default to ./local_transcripts
        raw_path = os.environ.get("LOCAL_FILES_PATH", "./local_transcripts")
        # Expand the user's home directory if the tilde '~' is used
        self.path = os.path.expanduser(raw_path)
        
        if not os.path.isdir(self.path):
            logger.info(f"Local files path '{self.path}' not found, creating it.")
            os.makedirs(self.path)
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get_meetings(self, days: float) -> List[Meeting]:
        """Scans the local directory for transcript files modified within a given number of days."""
        meetings = []
        meetings_found_in_scan = 0
        time_threshold = datetime.now(tz=tz.tzlocal()) - timedelta(days=days)

        for filename in os.listdir(self.path):
            meetings_found_in_scan += 1
            file_path = os.path.join(self.path, filename)

            if not os.path.isfile(file_path):
                continue

            try:
                # Use file's modification time as the meeting start time
                mtime = os.path.getmtime(file_path)
                start_time = datetime.fromtimestamp(mtime, tz=tz.tzlocal())

                if start_time < time_threshold:
                    continue # Skip files that are too old

                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if not content:
                    continue

                # The 'original_data' now holds the raw content of the file
                meeting_data = {'raw_content': content}
                self._cache[filename] = meeting_data

                meeting = Meeting(
                    id=filename,
                    name=filename.rsplit('.', 1)[0], # Use filename as title
                    start_time=start_time,
                    original_data=meeting_data
                )
                meetings.append(meeting)
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")

        logger.info(f"Scanned {meetings_found_in_scan} files, found {len(meetings)} valid and recent meetings in {self.path}")
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
