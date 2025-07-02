import argparse
import os
from dotenv import load_dotenv
from src.logger import logger
from src.google_auth import get_credentials
from src.google_calendar_api import find_concluded_events, remove_attachment_from_event
from src.google_docs_api import delete_google_doc

ATTACHMENT_PREFIX = "[ANAIT]__Transcript for"

def find_attachments_to_clean(creds, days):
    """Finds events and attachments that match the script's naming convention."""
    logger.info(f"Searching for events in the last {days} days to find attachments to clean...")
    events = find_concluded_events(creds, days_ago=days)
    if not events:
        logger.info("No recent events found.")
        return []

    items_to_clean = []
    for event in events:
        event_id = event.get('id')
        event_summary = event.get('summary')
        for attachment in event.get('attachments', []):
            title = attachment.get('title')
            if title and title.startswith(ATTACHMENT_PREFIX):
                # Extract file ID from the URL
                file_url = attachment.get('fileUrl', '')
                file_id = file_url.split('/d/')[1].split('/')[0] if '/d/' in file_url else None
                if file_id:
                    items_to_clean.append({
                        'event_id': event_id,
                        'event_summary': event_summary,
                        'attachment_title': title,
                        'file_id': file_id
                    })
    return items_to_clean

def main():
    """Main function to handle the cleanup process."""
    parser = argparse.ArgumentParser(description="Clean up attachments created by the transcript connector.")
    parser.add_argument("--days", type=int, default=7, help="Number of past days to search for events.")
    parser.add_argument("--dry-run", action='store_true', help="List attachments to be deleted without actually deleting them.")
    args = parser.parse_args()

    logger.info("--- Starting Attachment Cleanup Script ---")
    if args.dry_run:
        logger.info("Running in DRY-RUN mode. No files will be deleted.")
    
    load_dotenv()
    creds = get_credentials()
    if not creds:
        return

    items = find_attachments_to_clean(creds, args.days)

    if not items:
        logger.info("No attachments matching the criteria were found.")
        return

    logger.info(f"Found {len(items)} attachments to potentially clean:")
    for item in items:
        logger.info(f"  - Event: '{item['event_summary']}' -> Attachment: '{item['attachment_title']}' (File ID: {item['file_id']})")

    if args.dry_run:
        logger.info("Dry-run finished. To delete these items, run the script again without the --dry-run flag.")
        return

    # Deletion logic with confirmation
    confirm = input("\nProceed with deleting these files and attachments? (y/n): ")
    if confirm.lower() != 'y':
        logger.info("Cleanup cancelled by user.")
        return

    logger.info("--- Starting Deletion ---")
    success_count = 0
    for item in items:
        logger.info(f"Processing: {item['attachment_title']}")
        # 1. Delete the Google Doc file
        doc_deleted = delete_google_doc(creds, item['file_id'])
        if doc_deleted:
            # 2. Remove the attachment from the event
            attachment_removed = remove_attachment_from_event(creds, item['event_id'], item['attachment_title'])
            if attachment_removed:
                logger.info(f"  -> Successfully deleted doc and removed attachment for '{item['event_summary']}'.")
                success_count += 1
            else:
                logger.error(f"  -> Deleted Google Doc {item['file_id']}, but FAILED to remove attachment from event {item['event_id']}.")
        else:
            logger.error(f"  -> FAILED to delete Google Doc {item['file_id']}. Skipping attachment removal.")

    logger.info(f"--- Cleanup Finished. Successfully deleted {success_count}/{len(items)} items. ---")

if __name__ == "__main__":
    main()
