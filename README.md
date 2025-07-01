# Transcripts Connector

This service automatically fetches meeting transcripts from TLDV and attaches them to the corresponding Google Calendar events as Google Docs.

## Current Status

**This project is currently in development.** The core logic is implemented, but the integration with Google APIs (Calendar, Docs) is using stubs due to an ongoing OAuth `redirect_uri_mismatch` issue. The TLDV integration is functional.

## Features

- **TLDV Integration**: Fetches meeting lists and transcripts.
- **Google Calendar Integration (Stubbed)**: Fetches events and attaches documents.
- **Google Docs Integration (Stubbed)**: Creates documents, inserts text, and manages permissions.
- **Transcript Formatting**: Converts raw transcript data into a readable format.
- **Configuration**: Uses a `.env` file for managing API keys and settings.
- **Logging**: Centralized logging for clear and structured output.
- **Testing**: Unit tests for all API modules.

## Prerequisites

- Python 3.10+
- `pip` for package management

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd transcripts-connector
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure environment variables:**
    -   Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    -   Open the `.env` file and add your TLDV API key:
        ```
        TLDV_API_KEY="your_tldv_api_key_here"
        ```

## Usage

To run the main script, execute the following command from the root directory:

```bash
python3 main.py
```

The script will log its progress to the console.

## Running Tests

To run the unit tests, use the following command:

```bash
python3 -m unittest discover tests
```
