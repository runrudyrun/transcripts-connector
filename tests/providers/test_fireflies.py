# tests/providers/test_fireflies.py

import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set a dummy API key for testing
os.environ['FIREFLIES_API_KEY'] = 'test_key'

from src.providers import fireflies

class TestFirefliesApi(unittest.TestCase):

    @patch('src.providers.fireflies.requests.post')
    def test_get_meetings_success(self, mock_post):
        """Test successful retrieval of meetings via GraphQL."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': {
                'transcripts': [
                    {'id': 'fireflies_meeting_1', 'title': 'Fireflies Test Meeting', 'date': 1672531200000, 'conference': {'metadata': {'conferenceId': 'conf-123'}}}
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {'FIREFLIES_API_KEY': 'test_key'}):
            meetings = fireflies.get_meetings()
            self.assertEqual(len(meetings), 1)
            self.assertEqual(meetings[0]['id'], 'fireflies_meeting_1')
            self.assertEqual(meetings[0]['source'], 'fireflies')
            self.assertEqual(meetings[0]['conferenceId'], 'conf-123')

    @patch('src.providers.fireflies.requests.post')
    def test_get_transcript_by_meeting_id_success(self, mock_post):
        """Test successful retrieval of a transcript via GraphQL."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': {
                'transcript': {
                    'sentences': [
                        {'text': 'Hello world.'},
                        {'text': 'This is a test.'}
                    ]
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {'FIREFLIES_API_KEY': 'test_key'}):
            transcript = fireflies.get_transcript_by_meeting_id('fireflies_meeting_1')
            self.assertEqual(transcript, 'Hello world.\nThis is a test.')

if __name__ == '__main__':
    unittest.main()
