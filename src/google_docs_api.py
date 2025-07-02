# This file will contain functions to interact with the Google Docs and Drive APIs.
from googleapiclient.discovery import build
from src.logger import logger

def create_google_doc(creds, doc_title, transcript_text, shared_drive_id=None, folder_id=None):
    """
    Creates a new Google Doc, optionally in a Shared Drive, and inserts text.
    Returns the file's ID.
    """
    try:
        # 1. Create the document using the Docs API to get a native Google Doc
        docs_service = build('docs', 'v1', credentials=creds)
        doc_body = {'title': doc_title}
        document = docs_service.documents().create(body=doc_body).execute()
        doc_id = document.get('documentId')
        logger.info(f"Successfully created Google Doc with title: '{doc_title}', ID: {doc_id}")

        # 2. If a shared_drive_id is provided, move the file to the specified folder or the drive's root.
        if shared_drive_id:
            drive_service = build('drive', 'v3', credentials=creds)
            # The target folder is either the specific folder_id or the shared_drive_id itself (root).
            target_parent_id = folder_id if folder_id else shared_drive_id
            logger.info(f"Moving document {doc_id} to parent folder {target_parent_id} in Shared Drive...")
            
            # Get current parents to remove them
            file = drive_service.files().get(fileId=doc_id, fields='parents', supportsAllDrives=True).execute()
            previous_parents = ",".join(file.get('parents'))

            drive_service.files().update(
                fileId=doc_id,
                addParents=target_parent_id,
                removeParents=previous_parents,
                supportsAllDrives=True
            ).execute()
            logger.info(f"Successfully moved document {doc_id} to Shared Drive {shared_drive_id}")

        # 3. Insert the transcript text into the document
        requests = [{
            'insertText': {
                'location': {'index': 1},
                'text': transcript_text
            }
        }]
        docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
        logger.info(f"Successfully inserted transcript into document {doc_id}.")

        return doc_id

    except Exception as e:
        logger.error(f"Failed during Google Doc creation/setup for '{doc_title}': {e}", exc_info=True)
        return None

def share_file_publicly(creds, file_id):
    """
    Makes a file (including one in a Shared Drive) publicly accessible ('anyone with link').
    Returns the file's metadata, including the webViewLink.
    """
    try:
        drive_service = build('drive', 'v3', credentials=creds)
        permission = {'type': 'anyone', 'role': 'reader'}
        
        drive_service.permissions().create(
            fileId=file_id,
            body=permission,
            supportsAllDrives=True  # Required for files in Shared Drives
        ).execute()
        logger.info(f"File {file_id} has been shared publicly.")

        # After sharing, get the necessary file details to return
        file_details = drive_service.files().get(
            fileId=file_id,
            fields='name, webViewLink, mimeType',
            supportsAllDrives=True  # Required for files in Shared Drives
        ).execute()
        
        logger.info(f"Returning details for shared file: {file_details.get('name')}")
        return file_details

    except Exception as e:
        logger.error(f"An error occurred while sharing file {file_id}: {e}", exc_info=True)
        return None

def delete_google_doc(creds, file_id):
    """Permanently deletes a file from Google Drive."""
    try:
        service = build('drive', 'v3', credentials=creds)
        service.files().delete(fileId=file_id, supportsAllDrives=True).execute()
        logger.info(f"Successfully deleted Google Doc with ID: {file_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete Google Doc with ID {file_id}: {e}", exc_info=True)
        return False
