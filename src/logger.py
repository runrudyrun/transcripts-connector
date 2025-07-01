import logging
import sys

def setup_logger():
    """Sets up a basic logger."""
    logger = logging.getLogger("TranscriptConnector")
    logger.setLevel(logging.INFO)

    # Create a handler to write to stdout
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    # Add the handler to the logger
    if not logger.handlers:
        logger.addHandler(handler)

    return logger

logger = setup_logger()
