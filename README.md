# Transcripts Connector

This tool automates the process of fetching meeting transcripts and AI Notes (highlights) from TLDV, creating formatted Google Docs for each, and attaching them to the corresponding Google Calendar event.

## Key Features

- **Dual Content Fetching**: Retrieves both full meeting transcripts and AI-generated notes (highlights) from TLDV.
- **Separate Document Generation**: Creates two distinct Google Docs for each meeting: one for the transcript and one for the AI Notes, allowing for organized access.
- **Flexible Event Fetching**: Scans Google Calendar for concluded events within a configurable time window using `--days` or `--hours` flags. Defaults to the last 7 days.
- **Configurable Filtering**: Uses a customizable list of keywords in the `.env` file (`IGNORE_KEYWORDS`) to exclude specific meetings (e.g., "1:1", "private") from processing.
- **Robust Matching Logic**: Implements a two-stage matching process to accurately pair calendar events with TLDV recordings, first by conference ID and then by time proximity.
- **Automated Sharing & Attachment**: Shares the generated Google Docs publicly (view-only) and attaches them to the calendar event.
- **Safe Cleanup Utility**: Includes a powerful command-line script (`cleanup_attachments.py`) to safely find and remove generated documents and their calendar attachments, with support for time window and prefix filtering.

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
    Create a `.env` file by copying the `.env.example` template. Fill in your credentials and customize the settings.
    ```dotenv
    # Google Credentials
    GOOGLE_CLIENT_ID=your_google_client_id
    GOOGLE_CLIENT_SECRET=your_google_client_secret

    # TLDV API Key
    TLDV_API_KEY=your_tldv_api_key

    # Optional: Google Shared Drive for storing documents
    SHARED_DRIVE_ID=your_google_shared_drive_id
    SHARED_DRIVE_FOLDER_ID=your_google_drive_folder_id

    # Keywords to ignore meetings (case-insensitive, comma-separated)
    IGNORE_KEYWORDS="1:1, 1-1, catch-up, private"
    ```

4.  **Authenticate with Google:**
    Run the main script for the first time. It will open a browser window for you to authorize the application. This creates a `token.json` file that stores your credentials for future runs.
    ```bash
    python main.py
    ```

## Usage

### Main Script (`main.py`)

Run the main connector to fetch transcripts and notes. You can specify a time window for fetching events.

- **Default Run (searches last 7 days):**
  ```bash
  python main.py
  ```

- **Custom Time Window:**
  Use `--days` or `--hours` to specify how far back to search for concluded meetings.
  ```bash
  # Search for meetings in the last 3 days
  python main.py --days 3

  # Search for meetings in the last 12 hours
  python main.py --hours 12
  ```

### Cleanup Script (`cleanup_attachments.py`)

This script removes documents and attachments created by the tool. It supports dry runs and flexible filtering.

- **Dry Run (shows what would be deleted):**
  It's highly recommended to perform a dry run first.
  ```bash
  # Check attachments from the last 7 days with the default prefix
  python cleanup_attachments.py --dry-run
  ```

- **Deletion Mode:**
  To permanently delete the files, run the script without the `--dry-run` flag. It will require confirmation.
  ```bash
  # Delete attachments from the last 30 days
  python cleanup_attachments.py --days 30

  # Delete attachments from the last 2 hours with a custom prefix
  python cleanup_attachments.py --hours 2 --prefix "AI Notes for"
  ```
