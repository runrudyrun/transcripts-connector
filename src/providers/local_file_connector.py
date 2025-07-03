import os
import json
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from src.logger import logger
from src.providers.base import BaseConnector, Meeting, Transcript, Note
from src.transcript_formatter import format_transcript

LOCAL_FILES_PATH = os.environ.get("LOCAL_FILES_PATH", "./local_transcripts")

class LocalFileConnector(BaseConnector):
    """Connector for reading transcripts and notes from local files."""

    def __init__(self):
        self.path = LOCAL_FILES_PATH
        if not os.path.isdir(self.path):
            logger.info(f"Local files path '{self.path}' not found, creating it.")
            os.makedirs(self.path)
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _parse_grain_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Parses a text file in the Grain/Zapier format using regex."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Could not read file {file_path}: {e}")
            return None

        # A comprehensive list of keys to correctly delimit sections.
        # We only use a few, but the others are needed as separators.
        known_keys = [
            "Recording ID", "Recording Title", "Owners", "Source", "Recording URL", "Tags",
            "Recording Summary Overview", "Recording Start Datetime", "Recording End Datetime",
            "Participants", "Transcript (Encoded JSON)"
        ]
        
        parsed_data = {}
        # Create a regex that looks for any of the known keys at the start of a line
        key_pattern = '|'.join(re.escape(key) for key in known_keys)
        # Split the content by these keys, keeping the keys as delimiters
        parts = re.split(f'^({key_pattern})$', content, flags=re.MULTILINE)

        if len(parts) < 3:
            return None # Not a valid file format

        # The result of split is ['', key1, value1, key2, value2, ...]
        # We iterate through it in chunks of 2
        for i in range(1, len(parts), 2):
            key = parts[i].strip()
            value = parts[i+1].strip()
            parsed_data[key] = value

        return parsed_data

    def get_meetings(self, days: float) -> List[Meeting]:
        """Scans the local directory for transcript files modified within a given number of days."""
        meetings = []
        meetings_found_in_scan = 0
        time_threshold = datetime.now() - timedelta(days=days)

        for filename in os.listdir(self.path):
            meetings_found_in_scan += 1
            file_path = os.path.join(self.path, filename)

            try:
                modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if modified_time < time_threshold:
                    continue  # Skip files that are too old
            except OSError as e:
                logger.warning(f"Could not get modification time for {filename}: {e}")
                continue

            if not filename.endswith(('.txt', '.md')):
                continue
            
            file_path = os.path.join(self.path, filename)
            parsed_data = self._parse_grain_file(file_path)

            if not parsed_data:
                logger.warning(f"Could not parse file: {filename}")
                continue

            self._cache[filename] = parsed_data # Cache the parsed data

            try:
                start_time_str = parsed_data["Recording Start Datetime"]
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                meeting = Meeting(
                    id=filename,  # Use filename as the unique ID
                    name=parsed_data.get("Recording Title", "Untitled Meeting"),
                    start_time=start_time,
                    original_data=parsed_data
                )
                meetings.append(meeting)
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping file {filename} due to missing or invalid data: {e}")

        logger.info(f"Scanned {meetings_found_in_scan} files, found {len(meetings)} valid and recent meetings in {self.path}")
        return meetings

    def get_transcript(self, meeting: Meeting) -> Optional[Transcript]:
        """Reads and formats a transcript from a local file."""
        data = meeting.original_data
        if not data or "Transcript (Encoded JSON)" not in data:
            return None

        try:
            transcript_json_str = data["Transcript (Encoded JSON)"]
            transcript_data = json.loads(transcript_json_str)

            # The format from Grain seems to be a list of dicts with 'speaker', 'text'.
            # Our formatter expects a specific structure, let's adapt.
            formatted_transcript_data = {'data': transcript_data}
            formatted_text = format_transcript(formatted_transcript_data, meeting.name)
            return Transcript(text=formatted_text, original_data=transcript_data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse or format transcript for {meeting.id}: {e}")
            return None

    def get_notes(self, meeting: Meeting) -> Optional[Note]:
        """Reads AI notes (summary) from a local file."""
        data = meeting.original_data
        if not data or "Recording Summary Overview" not in data:
            return None
        
        summary = data["Recording Summary Overview"]
        return Note(content=summary, original_data=data)
