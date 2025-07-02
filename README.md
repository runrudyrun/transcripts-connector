# Transcripts Connector

This tool automates the process of fetching meeting transcripts from TLDV, creating a formatted Google Doc, and attaching it to the corresponding Google Calendar event.

## Key Features

- **Fetches Past Events**: Scans Google Calendar for events that have concluded within the last 7 days.
- **Robust Matching Logic**: Implements a two-stage matching process to accurately pair calendar events with TLDV recordings:
  1.  Matches using the unique `conferenceId`.
  2.  For remaining items, matches by the closest time proximity (within a 5-minute window).
- **Confidentiality Filter**: Automatically skips processing for meetings that appear to be confidential (e.g., "1:1", "performance review") or have only two attendees.
- **Automated Document Creation**: Generates a new Google Doc for each matched transcript.
- **Standardized Titling**: All created documents are titled with the prefix `ANAIT: Transcript for {Event Name}` for easy identification and cleanup.
- **Public Sharing & Attachment**: Shares the Google Doc publicly (view-only) and attaches it to the calendar event.
- **Safe Cleanup Utility**: Includes a command-line script (`cleanup_attachments.py`) to safely remove generated documents and their corresponding calendar attachments.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd transcripts-connector
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables:**
    Create a `.env` file in the root directory and add your Google Cloud and TLDV credentials. You can use `.env.example` as a template.
    ```
    GOOGLE_CLIENT_ID=your_google_client_id
    GOOGLE_CLIENT_SECRET=your_google_client_secret
    TLDV_API_KEY=your_tldv_api_key
    SHARED_DRIVE_ID=your_google_shared_drive_id (Optional)
    SHARED_DRIVE_FOLDER_ID=your_google_drive_folder_id (Optional)
    ```

4.  **Authenticate with Google:**
    Run the main script for the first time. It will open a browser window for you to authorize the application. This will create a `token.json` file that stores your authentication credentials.
    ```bash
    python main.py
    ```

## Usage

### Main Script

To run the main connector process, execute:
```bash
python main.py
```

### Cleanup Script

The cleanup script helps you remove documents and attachments created by this tool. It has two modes:

1.  **Dry Run (Recommended first):**
    This command lists all the files and attachments that would be deleted, without actually deleting anything.
    ```bash
    python cleanup_attachments.py --dry-run
    ```

2.  **Deletion Mode:**
    To permanently delete the files and attachments found, run the script without the `--dry-run` flag. It will ask for your confirmation before proceeding.
    ```bash
    python cleanup_attachments.py
    ```
    You can also specify how many days back to search (default is 7):
    ```bash
    python cleanup_attachments.py --days 30
    ```
