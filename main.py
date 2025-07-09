import argparse
from dotenv import load_dotenv

from src.logger import logger
from src.providers.tldv_connector import TldvConnector
from src.providers.local_file_connector import LocalFileConnector
from src.providers.google_drive_connector import GoogleDriveConnector
from src.google_api import GoogleApi
from src.orchestrator import Orchestrator

# A simple factory to select the connector
CONNECTORS = {
    "tldv": TldvConnector,
    "local": LocalFileConnector,
    "gdrive": GoogleDriveConnector,
}

def main():
    """Main function to orchestrate the transcript processing workflow."""
    parser = argparse.ArgumentParser(description="Fetch transcripts and attach them to Google Calendar events.")
    parser.add_argument(
        "--hours",
        type=int,
        default=168,  # 7 days * 24 hours
        help="Number of past hours to search for meetings."
    )
    parser.add_argument("--connector", type=str, default="tldv", choices=CONNECTORS.keys(), help="The connector to use for fetching meetings.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without attaching any documents to calendar events."
    )
    args = parser.parse_args()

    try:
        load_dotenv()

        # --- Setup ---
        logger.info(f"Using {args.connector} connector.")
        connector_class = CONNECTORS.get(args.connector)
        if not connector_class:
            raise ValueError(f"Invalid connector specified: {args.connector}")

        google_api = GoogleApi()

        # Instantiate connector based on its needs
        if args.connector == "gdrive":
            connector = connector_class(google_api=google_api)
        else:
            connector = connector_class()

        # --- Orchestration ---
        orchestrator = Orchestrator(connector, google_api)
        days_to_process = args.hours / 24.0
        logger.info(f"Processing meetings from the last {args.hours} hours ({days_to_process:.2f} days).")
        orchestrator.run_cli(days=days_to_process, dry_run=args.dry_run)

    except Exception as e:
        logger.critical(f"An unexpected error occurred in the main function: {e}", exc_info=True)


if __name__ == "__main__":
    main()
