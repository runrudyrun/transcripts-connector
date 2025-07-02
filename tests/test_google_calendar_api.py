import unittest
from unittest.mock import patch, MagicMock
import os
import datetime

# Add the src directory to the Python path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.google_calendar_api import find_concluded_events, attach_document_to_event

class TestGoogleCalendarApi(unittest.TestCase):

    @patch('src.google_calendar_api.build')
    def test_find_concluded_events(self, mock_build):
        """Test successful retrieval of concluded calendar events."""
        mock_service = MagicMock()
        mock_events_list = MagicMock()
        mock_service.events.return_value = mock_events_list
        mock_build.return_value = mock_service

        # Mock the API response
        now = datetime.datetime.now(datetime.timezone.utc)
        event_end_time = (now - datetime.timedelta(hours=1)).isoformat()
        mock_events_list.list.return_value.execute.return_value = {
            'items': [
                {'summary': 'Test Event', 'id': '123', 'end': {'dateTime': event_end_time}}
            ]
        }

        events = find_concluded_events('dummy_creds', days_ago=1)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['summary'], 'Test Event')

    @patch('src.google_calendar_api.build')
    def test_attach_document_to_event(self, mock_build):
        """Test successfully attaching a document to an event."""
        mock_service = MagicMock()
        mock_events_patch = MagicMock()
        mock_service.events.return_value = mock_events_patch
        mock_build.return_value = mock_service

        # Mock the get and patch API calls
        mock_events_patch.get.return_value.execute.return_value = {'attachments': []}
        mock_events_patch.patch.return_value.execute.return_value = {'id': 'event123'}

        file_details = {'fileId': 'file123', 'title': 'My Transcript', 'fileUrl': 'http://example.com'}
        result = attach_document_to_event('dummy_creds', 'event123', 'file123', file_details)

        self.assertIsNotNone(result)
        mock_events_patch.patch.assert_called_once()

if __name__ == '__main__':
    unittest.main()
