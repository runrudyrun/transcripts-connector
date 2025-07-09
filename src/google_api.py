import os
from datetime import datetime, timezone
from typing import List, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

from src.logger import logger

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive"
]

class GoogleApi:
    """A unified client for interacting with Google Calendar, Docs, and Drive APIs."""

    def __init__(self):
        self.creds = None
        self.drive_service = None
        self.docs_service = None
        self.calendar_service = None
        self.shared_drive_id = os.environ.get("GOOGLE_SHARED_DRIVE_ID")
        self.target_folder_id = os.environ.get("GOOGLE_TARGET_FOLDER_ID")

    def authenticate(self) -> bool:
        """Handles user authentication and token management."""
        if os.path.exists("token.json"):
            self.creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Failed to refresh token: {e}. Please re-authenticate.")
                    self.creds = None # Force re-authentication
            
            if not self.creds: # This block runs if creds are None or refresh failed
                client_id = os.environ.get("GOOGLE_CLIENT_ID")
                client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
                project_id = os.environ.get("GOOGLE_PROJECT_ID")

                if not client_id or not client_secret:
                    logger.critical("Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET")
                    return False

                client_config = {
                    "installed": {
                        "client_id": client_id, "project_id": project_id, "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
                    }
                }
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                self.creds = flow.run_local_server(port=8080)
            
            with open("token.json", "w") as token:
                token.write(self.creds.to_json())
        
        if self.creds:
            self.drive_service = build('drive', 'v3', credentials=self.creds)
            self.docs_service = build('docs', 'v1', credentials=self.creds)
            self.calendar_service = build('calendar', 'v3', credentials=self.creds)
            return True
        
        return False

    def get_concluded_events(self, time_min: datetime) -> List[Dict[str, Any]]:
        """Finds events that have concluded since the specified time."""
        try:
            now = datetime.now(timezone.utc)
            events_result = self.calendar_service.events().list(
                calendarId='primary',
                timeMin=time_min.isoformat(),
                timeMax=now.isoformat(),
                singleEvents=True,
                orderBy='startTime',
                fields='items(id,summary,start,end,attendees,attachments,conferenceData(conferenceId))'
            ).execute()
            
            events = events_result.get('items', [])
            concluded_events = []
            for event in events:
                end_time_str = event.get('end', {}).get('dateTime')
                if end_time_str:
                    end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                    if end_time < now:
                        concluded_events.append(event)
            return concluded_events
        except HttpError as error:
            logger.error(f'An error occurred with Google Calendar API: {error}')
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching events: {e}", exc_info=True)
            return []

    def has_attachment(self, attachments: List[Dict[str, Any]], title_prefix: str) -> bool:
        """Checks if an attachment with a given title prefix exists."""
        return any(att.get('title', '').startswith(title_prefix) for att in attachments)

    def create_and_attach_doc(self, event_id: str, doc_title: str, content: str):
        """Creates a Google Doc, moves it, inserts content, and attaches it to an event."""
        try:
            # 1. Create the document
            doc_body = {'title': doc_title}
            document = self.docs_service.documents().create(body=doc_body).execute()
            doc_id = document.get('documentId')
            logger.info(f"Successfully created Google Doc '{doc_title}' (ID: {doc_id})")

            # 2. Move to Shared Drive/Folder if specified
            if self.shared_drive_id:
                target_parent_id = self.target_folder_id or self.shared_drive_id
                file_metadata = self.drive_service.files().get(fileId=doc_id, fields='parents', supportsAllDrives=True).execute()
                previous_parents = ",".join(file_metadata.get('parents'))
                self.drive_service.files().update(
                    fileId=doc_id,
                    addParents=target_parent_id,
                    removeParents=previous_parents,
                    supportsAllDrives=True
                ).execute()
                logger.info(f"Moved document {doc_id} to parent {target_parent_id}")

            # 3. Insert content
            requests = [{'insertText': {'location': {'index': 1}, 'text': content}}]
            self.docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
            logger.info(f"Inserted content into document {doc_id}")

            # 4. Attach to calendar event
            clean_file_url = f"https://docs.google.com/document/d/{doc_id}/edit"
            new_attachment = {
                'fileUrl': clean_file_url,
                'title': doc_title,
                'mimeType': 'application/vnd.google-apps.document'
            }
            
            event = self.calendar_service.events().get(calendarId='primary', eventId=event_id).execute()
            attachments = event.get('attachments', [])
            attachments.append(new_attachment)
            
            body = {'attachments': attachments}
            self.calendar_service.events().patch(
                calendarId='primary', eventId=event_id, body=body, supportsAttachments=True
            ).execute()
            logger.info(f"Successfully attached document {doc_id} to event {event_id}")

        except Exception as e:
            logger.error(f"Failed during doc creation/attachment for '{doc_title}': {e}", exc_info=True)

    def list_transcript_files(self) -> List[Dict[str, Any]]:
        """Lists potential transcript files from the target Google Drive folder."""
        if not self.target_folder_id:
            logger.error("GOOGLE_TARGET_FOLDER_ID is not set. Cannot list files from Drive.")
            return []
        try:
            logger.info(f"Searching for transcript files in Google Drive folder: {self.target_folder_id}")
            query = (
                f"'{self.target_folder_id}' in parents and "
                f"(mimeType='text/plain' or mimeType='application/vnd.google-apps.document') and "
                f"trashed = false"
            )
            results = self.drive_service.files().list(
                q=query,
                pageSize=100, # Adjust as needed
                fields="files(id, name, createdTime, mimeType)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            files = results.get('files', [])
            logger.info(f"Found {len(files)} potential transcript files in Google Drive.")
            return files
        except HttpError as error:
            logger.error(f'An error occurred with Google Drive API while listing files: {error}')
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred while listing Drive files: {e}", exc_info=True)
            return []

    def get_drive_file_content(self, file_id: str, mime_type: str) -> str:
        """Fetches the text content of a file from Google Drive."""
        try:
            logger.info(f"Fetching content for file {file_id} with mimeType {mime_type}")
            if mime_type == 'application/vnd.google-apps.document':
                # Export Google Doc as plain text
                request = self.drive_service.files().export_media(fileId=file_id, mimeType='text/plain')
            else:
                # Download other file types directly
                request = self.drive_service.files().get_media(fileId=file_id)
            
            content_bytes = request.execute()
            return content_bytes.decode('utf-8')
        except HttpError as error:
            logger.error(f'An error occurred fetching file content for {file_id}: {error}')
            return ""
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching file content: {e}", exc_info=True)
            return ""

    def delete_google_doc(self, file_id: str) -> bool:
        """Deletes a Google Doc file by its ID."""
        try:
            self.drive_service.files().delete(fileId=file_id, supportsAllDrives=True).execute()
            logger.info(f"Successfully deleted Google Doc with ID: {file_id}")
            return True
        except HttpError as error:
            if error.resp.status == 404:
                logger.warning(f"Google Doc with ID {file_id} not found. Assuming already deleted.")
                return True
            logger.error(f"Failed to delete Google Doc {file_id}: {error}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred while deleting doc {file_id}: {e}", exc_info=True)
            return False

    def remove_attachment_from_event(self, event_id: str, attachment_title: str) -> bool:
        """Removes an attachment from a calendar event by its title."""
        try:
            event = self.calendar_service.events().get(calendarId='primary', eventId=event_id).execute()
            current_attachments = event.get('attachments', [])
            
            if not any(att.get('title') == attachment_title for att in current_attachments):
                logger.warning(f"Attachment '{attachment_title}' not found on event {event_id}. Nothing to remove.")
                return True

            updated_attachments = [att for att in current_attachments if att.get('title') != attachment_title]
            
            body = {'attachments': updated_attachments}
            self.calendar_service.events().patch(
                calendarId='primary', 
                eventId=event_id, 
                body=body, 
                supportsAttachments=True
            ).execute()
            
            logger.info(f"Successfully removed attachment '{attachment_title}' from event {event_id}")
            return True
        except HttpError as error:
            logger.error(f"Failed to remove attachment '{attachment_title}' from event {event_id}: {error}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred while removing attachment from event {event_id}: {e}", exc_info=True)
            return False
