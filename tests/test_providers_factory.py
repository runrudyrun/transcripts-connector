# tests/test_providers_factory.py

import unittest
from unittest.mock import patch, MagicMock
import os

from src.providers import get_all_meetings, get_transcript

class TestProviderFactory(unittest.TestCase):

    @patch.dict(os.environ, {'MEETING_PROVIDERS': 'tldv,fireflies'})
    @patch('src.providers.importlib.import_module')
    def test_get_all_meetings(self, mock_import_module):
        """Test fetching meetings from multiple enabled providers."""
        # Mock the tldv module
        mock_tldv = MagicMock()
        mock_tldv.get_meetings.return_value = {'results': [{'id': 'tldv1', 'name': 'TLDV Meeting'}]}

        # Mock the fireflies module
        mock_fireflies = MagicMock()
        mock_fireflies.get_meetings.return_value = {'results': [{'id': 'ff1', 'title': 'Fireflies Meeting'}]}

        # import_module will return a different mock depending on the input
        def import_side_effect(module_name):
            if 'tldv' in module_name:
                return mock_tldv
            if 'fireflies' in module_name:
                return mock_fireflies
            raise ImportError
        mock_import_module.side_effect = import_side_effect

        meetings = get_all_meetings()

        self.assertEqual(len(meetings), 2)
        self.assertEqual(meetings[0]['source'], 'tldv')
        self.assertEqual(meetings[1]['source'], 'fireflies')
        # Check that the original get_meetings functions were called
        mock_tldv.get_meetings.assert_called_once()
        mock_fireflies.get_meetings.assert_called_once()

    @patch('src.providers.importlib.import_module')
    def test_get_transcript(self, mock_import_module):
        """Test fetching a transcript from the correct provider based on source."""
        mock_tldv = MagicMock()
        mock_tldv.get_transcript_by_meeting_id.return_value = {'transcript': 'tldv transcript'}
        mock_import_module.return_value = mock_tldv

        meeting = {'id': 'tldv1', 'source': 'tldv'}
        transcript = get_transcript(meeting)

        self.assertIsNotNone(transcript)
        self.assertEqual(transcript['transcript'], 'tldv transcript')
        mock_tldv.get_transcript_by_meeting_id.assert_called_once_with('tldv1')

if __name__ == '__main__':
    unittest.main()
