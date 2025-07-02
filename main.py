import argparse
from dotenv import load_dotenv

from src.logger import logger
from src.providers.tldv_connector import TldvConnector
from src.providers.local_file_connector import LocalFileConnector
from src.google_api import GoogleApi
from src.orchestrator import Orchestrator

# A simple factory to select the connector
CONNECTORS = {
    "tldv": TldvConnector,
    "local": LocalFileConnector,
}

def main():
    """Main function to orchestrate the transcript processing workflow."""
    parser = argparse.ArgumentParser(description="Fetch transcripts and attach them to Google Calendar events.")
    parser.add_argument("--days", type=int, default=7, help="Number of past days to search for meetings.")
    parser.add_argument("--connector", type=str, default="tldv", choices=CONNECTORS.keys(), help="The connector to use for fetching meetings.")
    args = parser.parse_args()

    try:
        load_dotenv()

        # --- Dependency Setup ---
        connector_class = CONNECTORS.get(args.connector)
        if not connector_class:
            logger.critical(f"Invalid connector specified: {args.connector}")
            return
        
        connector = connector_class()
        google_api = GoogleApi()

        # --- Orchestration ---
        orchestrator = Orchestrator(connector, google_api)
        orchestrator.run(days=args.days)

    except Exception as e:
        logger.critical(f"An unexpected error occurred in the main function: {e}", exc_info=True)


if __name__ == "__main__":
    main()
