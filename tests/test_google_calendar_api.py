import unittest
from unittest.mock import patch
import os

# Add the src directory to the Python path to allow imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.google_calendar_api import get_calendar_events, get_event_attachments, attach_document_to_event

class TestGoogleCalendarApi(unittest.TestCase):

    def test_get_calendar_events(self):
        """Test that the stub for get_calendar_events returns a list of events."""
        # Since it's a stub, we just check if it returns a list as expected.
        events = get_calendar_events('dummy_creds')
        self.assertIsInstance(events, list)
        self.assertGreater(len(events), 0)
        self.assertIn('summary', events[0])
        self.assertIn('conferenceId', events[0])

    def test_get_event_attachments(self):
        """Test that the stub for get_event_attachments returns a list."""
        attachments = get_event_attachments('dummy_creds', 'dummy_event_id')
        self.assertIsInstance(attachments, list)

    def test_attach_document_to_event(self):
        """Test that the stub for attach_document_to_event returns True."""
        result = attach_document_to_event('dummy_creds', 'dummy_event_id', 'dummy_url')
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
