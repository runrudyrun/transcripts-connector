import argparse
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from src.logger import logger
from src.google_api import GoogleApi

def find_attachments_to_clean(google_api: GoogleApi, time_min: datetime, prefix: str):
    """Finds events and attachments that match the script's naming convention."""
    logger.info(f"Searching for events since {time_min.strftime('%Y-%m-%d %H:%M')} to find attachments with prefix '{prefix}'...")
    events = google_api.get_concluded_events(time_min=time_min)
    if not events:
        logger.info("No recent events found.")
        return []

    items_to_clean = []
    for event in events:
        event_id = event.get('id')
        event_summary = event.get('summary')
        for attachment in event.get('attachments', []):
            title = attachment.get('title')
            if title and title.startswith(prefix):
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
    parser.add_argument("--days", type=float, default=0, help="Number of past days to search for events.")
    parser.add_argument("--hours", type=float, default=0, help="Number of past hours to search for events.")
    parser.add_argument("--prefix", type=str, default="Transcript for", help="The prefix of attachment titles to search for.")
    parser.add_argument("--dry-run", action='store_true', help="List attachments to be deleted without actually deleting them.")
    args = parser.parse_args()

    total_hours = args.days * 24 + args.hours
    if total_hours == 0:
        total_hours = 24 * 7 # Default to 7 days
        logger.info("No time window specified, defaulting to 7 days (168 hours).")
    
    time_min = datetime.now(timezone.utc) - timedelta(hours=total_hours)

    logger.info("--- Starting Attachment Cleanup Script ---")
    if args.dry_run:
        logger.info("Running in DRY-RUN mode. No files will be deleted.")
    
    load_dotenv()
    google_api = GoogleApi()
    if not google_api.authenticate():
        logger.critical("Failed to authenticate with Google. Exiting.")
        return

    items = find_attachments_to_clean(google_api, time_min, args.prefix)

    if not items:
        logger.info("No attachments matching the criteria were found.")
        return

    logger.info(f"Found {len(items)} attachments to potentially clean:")
    for item in items:
        logger.info(f"  - Event: '{item['event_summary']}' -> Attachment: '{item['attachment_title']}' (File ID: {item['file_id']})")

    if args.dry_run:
        logger.info("Dry-run finished. To delete these items, run the script again without the --dry-run flag.")
        return

    confirm = input("\nProceed with deleting these files and attachments? (y/n): ")
    if confirm.lower() != 'y':
        logger.info("Cleanup cancelled by user.")
        return

    logger.info("--- Starting Deletion ---")
    success_count = 0
    for item in items:
        logger.info(f"Processing: {item['attachment_title']}")
        doc_deleted = google_api.delete_google_doc(item['file_id'])
        if doc_deleted:
            attachment_removed = google_api.remove_attachment_from_event(item['event_id'], item['attachment_title'])
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

