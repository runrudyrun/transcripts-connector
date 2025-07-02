import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from datetime import timedelta

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import main
import main

class TestMainScript(unittest.TestCase):

    @patch('main.get_credentials')
    @patch('main.find_concluded_events')
    @patch('main.get_meetings', return_value={'results': []})
    def test_main_default_args(self, mock_get_meetings, mock_find_events, mock_get_creds):
        """Test that find_concluded_events is called with default timedelta (7 days)."""
        with patch('sys.argv', ['main.py']):
            main.main()
            mock_find_events.assert_called_once_with(mock_get_creds.return_value, time_delta=timedelta(days=7))

    @patch('main.get_credentials')
    @patch('main.find_concluded_events')
    @patch('main.get_meetings', return_value={'results': []})
    def test_main_with_days_arg(self, mock_get_meetings, mock_find_events, mock_get_creds):
        """Test that find_concluded_events is called with specified days."""
        with patch('sys.argv', ['main.py', '--days', '5']):
            main.main()
            mock_find_events.assert_called_once_with(mock_get_creds.return_value, time_delta=timedelta(days=5))

    @patch('main.get_credentials')
    @patch('main.find_concluded_events')
    @patch('main.get_meetings', return_value={'results': []})
    def test_main_with_hours_arg(self, mock_get_meetings, mock_find_events, mock_get_creds):
        """Test that find_concluded_events is called with specified hours."""
        with patch('sys.argv', ['main.py', '--hours', '12']):
            main.main()
            mock_find_events.assert_called_once_with(mock_get_creds.return_value, time_delta=timedelta(hours=12))

    @patch.dict(os.environ, {"IGNORE_KEYWORDS": "1:1,review"})
    @patch('main.get_credentials')
    @patch('main.find_concluded_events')
    @patch('main.get_meetings')
    @patch('main.get_transcript_by_meeting_id')
    @patch('main.get_highlights_by_meeting_id')
    @patch('main.create_google_doc')
    @patch('main.share_file_publicly')
    @patch('main.attach_document_to_event')
    def test_ignore_keywords_filtering(self, mock_attach_doc, mock_share_file, mock_create_doc, mock_get_highlights, mock_get_transcript, mock_get_meetings, mock_find_events, mock_get_creds):
        """Test that events with ignored keywords are filtered out and not processed."""
        mock_find_events.return_value = [
            {'summary': 'Project Sync', 'id': 'event1', 'conferenceData': {'conferenceId': 'conf1'}, 'attachments': []},
            {'summary': '1:1 with Bob', 'id': 'event2', 'conferenceData': {'conferenceId': 'conf2'}, 'attachments': []},
            {'summary': 'Performance Review', 'id': 'event3', 'conferenceData': {'conferenceId': 'conf3'}, 'attachments': []}
        ]
        mock_get_meetings.return_value = {
            'results': [
                {'id': 'meeting1', 'name': 'Meeting 1', 'extraProperties': {'conferenceId': 'conf1'}},
                {'id': 'meeting2', 'name': 'Meeting 2', 'extraProperties': {'conferenceId': 'conf2'}},
                {'id': 'meeting3', 'name': 'Meeting 3', 'extraProperties': {'conferenceId': 'conf3'}}
            ]
        }
        # Make sure the mocked functions return values so the logic proceeds
        mock_get_transcript.return_value = {'transcript': 'some text'}
        mock_get_highlights.return_value = {'highlights': [{'text': 'a note'}]}
        mock_create_doc.return_value = 'new_doc_id'
        mock_share_file.return_value = {'webViewLink': 'http://example.com', 'id': 'new_doc_id'}

        with patch('sys.argv', ['main.py']):
            main.main()

        # Check that TLDV API was only called for the non-ignored event
        mock_get_transcript.assert_called_once_with('meeting1')
        mock_get_highlights.assert_called_once_with('meeting1')

        # Check that Google Docs/Calendar APIs were also called for the non-ignored event
        self.assertEqual(mock_create_doc.call_count, 2)  # Transcript and Highlights
        self.assertEqual(mock_share_file.call_count, 2)
        self.assertEqual(mock_attach_doc.call_count, 2)

if __name__ == '__main__':
    unittest.main()

