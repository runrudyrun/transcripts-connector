# This file will contain functions to interact with the Google Docs API.
from src.logger import logger

def create_document(creds, title):
    """Creates a new Google Doc and returns its ID."""
    logger.info(f"(Stub) Creating Google Doc with title: {title}")
    # TODO: Implement actual Google Docs API call
    return "dummy_document_id"


def insert_text(creds, document_id, text):
    """Inserts text into a Google Doc."""
    logger.info(f"(Stub) Inserting text into document: {document_id}")
    # print(text) # Uncomment to see the text that would be inserted
    # TODO: Implement actual Google Docs API call
    logger.info("(Stub) Text insertion complete.")
    return True

def share_document(creds, document_id, emails):
    """(Stub) Shares a Google Doc with a list of email addresses."""
    logger.info(f"(Stub) Sharing document {document_id} with: {', '.join(emails)}")
    # TODO: Implement actual Google Drive API call to modify permissions.
    logger.info("(Stub) Sharing complete.")
    return True
