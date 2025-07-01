# This file will contain functions to interact with the Google Docs and Drive APIs.
from googleapiclient.discovery import build
from src.logger import logger

def create_document(creds, title):
    """Creates a new Google Doc and returns its ID."""
    try:
        service = build('docs', 'v1', credentials=creds)
        document = service.documents().create(body={'title': title}).execute()
        doc_id = document.get('documentId')
        logger.info(f"Successfully created Google Doc with title: '{title}', ID: {doc_id}")
        return doc_id
    except Exception as e:
        logger.error(f"Failed to create Google Doc: {e}", exc_info=True)
        return None

def insert_text(creds, document_id, text):
    """Inserts text into a Google Doc."""
    try:
        service = build('docs', 'v1', credentials=creds)
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': 1,  # Insert at the beginning of the document
                    },
                    'text': text
                }
            }
        ]
        service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
        logger.info(f"Successfully inserted transcript into document {document_id}.")
        return True
    except Exception as e:
        logger.error(f"Failed to insert text into document {document_id}: {e}", exc_info=True)
        return False

def share_document(creds, document_id, emails):
    """Shares a Google Doc with a list of email addresses."""
    try:
        drive_service = build('drive', 'v3', credentials=creds)
        batch = drive_service.new_batch_http_request()

        for email in emails:
            user_permission = {
                'type': 'user',
                'role': 'reader',
                'emailAddress': email
            }
            batch.add(drive_service.permissions().create(
                fileId=document_id,
                body=user_permission,
                fields='id',
                sendNotificationEmail=False # Set to True if you want users to be notified
            ))
        
        logger.info(f"Sharing document {document_id} with: {', '.join(emails)}")
        batch.execute()
        logger.info(f"Successfully shared document {document_id}.")
        return True
    except Exception as e:
        logger.error(f"Failed to share document {document_id}: {e}", exc_info=True)
        return False
