from typing import List, Optional
from dateutil.parser import isoparse

from src.providers.base import BaseConnector, Meeting, Transcript, Note
from src.google_api import GoogleApi
from src.logger import logger

class GoogleDriveConnector(BaseConnector):
    """
    Connector for fetching transcripts from a specified Google Drive folder.
    """

    def __init__(self, google_api: GoogleApi):
        self.google_api = google_api

    def get_meetings(self, days: float) -> List[Meeting]:
        """
        Lists transcript files from the Google Drive folder and treats them as 'meetings'.
        The actual matching to calendar events is handled later by the Orchestrator.
        """
        logger.info("Fetching meetings from GoogleDriveConnector...")
        files = self.google_api.list_transcript_files()
        
        meetings = []
        for file in files:
            try:
                # The 'createdTime' from Drive API is in RFC 3339 format
                start_time = isoparse(file['createdTime'])
                
                meeting = Meeting(
                    id=file['id'],
                    name=file['name'],
                    start_time=start_time,
                    original_data={'mimeType': file['mimeType']} # Store mimeType for getting content later
                )
                meetings.append(meeting)

            except Exception as e:
                logger.error(f"Failed to process file '{file.get('name')}' (ID: {file.get('id')}): {e}", exc_info=True)
        
        logger.info(f"Found {len(meetings)} meetings (files) in Google Drive.")
        return meetings

    def get_transcript(self, meeting: Meeting) -> Optional[Transcript]:
        """
        Reads the content of the transcript file from Google Drive.
        """
        logger.info(f"Fetching transcript for meeting (file) '{meeting.name}' from Google Drive...")
        file_id = meeting.id
        mime_type = meeting.original_data.get('mimeType')

        if not mime_type:
            logger.error(f"Mime type missing for file ID {file_id}. Cannot fetch content.")
            return None

        content = self.google_api.get_drive_file_content(file_id, mime_type)
        
        if content:
            return Transcript(text=content, original_data={'file_id': file_id})
        
        return None

    def get_notes(self, meeting: Meeting) -> Optional[Note]:
        """
        Notes are not generated from raw files in this connector.
        The AIMapper could potentially be used for summarization in the future.
        """
        return None
