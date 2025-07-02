import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from datetime import timedelta

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cleanup_attachments

class TestCleanupScript(unittest.TestCase):

    def setUp(self):
        """Set up common mock data for tests."""
        self.mock_events = [
            {
                'id': 'event1',
                'summary': 'Test Event 1',
                'attachments': [
                    {'title': 'Transcript for Test Event 1', 'fileUrl': 'https://docs.google.com/document/d/file1/edit'},
                    {'title': 'Some other file', 'fileUrl': 'https://docs.google.com/document/d/otherfile1/edit'}
                ]
            },
            {
                'id': 'event2',
                'summary': 'Test Event 2',
                'attachments': [
                    {'title': 'AI Notes for Test Event 2', 'fileUrl': 'https://docs.google.com/document/d/file2/edit'}
                ]
            }
        ]

    @patch('cleanup_attachments.get_credentials')
    @patch('cleanup_attachments.find_concluded_events')
    @patch('cleanup_attachments.delete_google_doc')
    @patch('cleanup_attachments.remove_attachment_from_event')
    def test_dry_run(self, mock_remove, mock_delete, mock_find_events, mock_get_creds):
        """Test that --dry-run finds files but does not delete them."""
        mock_find_events.return_value = self.mock_events
        with patch('sys.argv', ['cleanup_attachments.py', '--dry-run']):
            cleanup_attachments.main()

        # Assert that find was called but delete/remove were not
        mock_find_events.assert_called_once()
        mock_delete.assert_not_called()
        mock_remove.assert_not_called()

    @patch('builtins.input', return_value='y')
    @patch('cleanup_attachments.get_credentials')
    @patch('cleanup_attachments.find_concluded_events')
    @patch('cleanup_attachments.delete_google_doc', return_value=True)
    @patch('cleanup_attachments.remove_attachment_from_event', return_value=True)
    def test_deletion_flow(self, mock_remove, mock_delete, mock_find_events, mock_get_creds, mock_input):
        """Test the full deletion flow when user confirms."""
        mock_find_events.return_value = [self.mock_events[0]] # Only use the first event
        with patch('sys.argv', ['cleanup_attachments.py', '--prefix', 'Transcript for']):
            cleanup_attachments.main()
        
        mock_delete.assert_called_once_with(mock_get_creds.return_value, 'file1')
        mock_remove.assert_called_once_with(mock_get_creds.return_value, 'event1', 'Transcript for Test Event 1')

    @patch('builtins.input', return_value='n')
    @patch('cleanup_attachments.get_credentials')
    @patch('cleanup_attachments.find_concluded_events')
    @patch('cleanup_attachments.delete_google_doc')
    @patch('cleanup_attachments.remove_attachment_from_event')
    def test_user_cancel_deletion(self, mock_remove, mock_delete, mock_find_events, mock_get_creds, mock_input):
        """Test that deletion is cancelled if the user inputs 'n'."""
        mock_find_events.return_value = self.mock_events
        with patch('sys.argv', ['cleanup_attachments.py']):
            cleanup_attachments.main()

        mock_delete.assert_not_called()
        mock_remove.assert_not_called()

    @patch('cleanup_attachments.get_credentials')
    @patch('cleanup_attachments.find_attachments_to_clean')
    def test_custom_args(self, mock_find_attachments, mock_get_creds):
        """Test that custom --prefix, --days, and --hours are passed correctly."""
        mock_find_attachments.return_value = []
        with patch('sys.argv', ['cleanup_attachments.py', '--prefix', 'AI Notes for', '--days', '3', '--hours', '5']):
            cleanup_attachments.main()

        expected_timedelta = timedelta(days=3, hours=5)
        mock_find_attachments.assert_called_once_with(mock_get_creds.return_value, expected_timedelta, 'AI Notes for')

    @patch('cleanup_attachments.get_credentials')
    @patch('cleanup_attachments.find_concluded_events')
    def test_no_attachments_found(self, mock_find_events, mock_get_creds):
        """Test the script's behavior when no matching attachments are found."""
        mock_find_events.return_value = [] # No events means no attachments
        with patch('sys.argv', ['cleanup_attachments.py', '--dry-run']):
            with self.assertLogs('TranscriptConnector', level='INFO') as cm:
                cleanup_attachments.main()
                # Check for the specific log message
                self.assertTrue(any("No attachments matching the criteria were found." in log for log in cm.output))

if __name__ == '__main__':
    unittest.main()
