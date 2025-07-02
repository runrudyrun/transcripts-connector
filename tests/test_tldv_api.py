import unittest
from unittest.mock import patch, MagicMock
import os
import requests

# Add the src directory to the Python path to allow imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tldv_api import get_meetings, get_transcript_by_meeting_id, get_highlights_by_meeting_id

class TestTldvApi(unittest.TestCase):

    @patch.dict(os.environ, {"TLDV_API_KEY": "test_key"})
    @patch('src.tldv_api.requests.get')
    def test_get_meetings_success(self, mock_get):
        """Test successful fetching of meetings."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'results': [{'id': '1', 'name': 'Meeting 1'}]}
        mock_get.return_value = mock_response

        meetings = get_meetings()
        self.assertIsNotNone(meetings)
        self.assertEqual(len(meetings['results']), 1)
        self.assertEqual(meetings['results'][0]['name'], 'Meeting 1')

    @patch.dict(os.environ, {"TLDV_API_KEY": "test_key"})
    @patch('src.tldv_api.requests.get')
    def test_get_meetings_failure(self, mock_get):
        """Test failure in fetching meetings."""
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        meetings = get_meetings()
        self.assertIsNone(meetings)

    @patch.dict(os.environ, {"TLDV_API_KEY": "test_key"})
    @patch('src.tldv_api.requests.get')
    def test_get_transcript_success(self, mock_get):
        """Test successful fetching of a transcript."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'transcript': 'Hello world'}
        mock_get.return_value = mock_response

        transcript = get_transcript_by_meeting_id('123')
        self.assertIsNotNone(transcript)
        self.assertEqual(transcript['transcript'], 'Hello world')

    @patch.dict(os.environ, {"TLDV_API_KEY": "test_key"})
    @patch('src.tldv_api.requests.get')
    def test_get_transcript_failure(self, mock_get):
        """Test failure in fetching a transcript."""
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        transcript = get_transcript_by_meeting_id('123')
        self.assertIsNone(transcript)

    @patch.dict(os.environ, {"TLDV_API_KEY": "test_key"})
    @patch('src.tldv_api.requests.get')
    def test_get_highlights_success(self, mock_get):
        """Test successful fetching of highlights."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'highlights': [{'timestamp': 10, 'text': 'Important point'}]}
        mock_get.return_value = mock_response

        highlights = get_highlights_by_meeting_id('123')
        self.assertIsNotNone(highlights)
        self.assertEqual(len(highlights['highlights']), 1)
        self.assertEqual(highlights['highlights'][0]['text'], 'Important point')

    @patch.dict(os.environ, {"TLDV_API_KEY": "test_key"})
    @patch('src.tldv_api.requests.get')
    def test_get_highlights_failure(self, mock_get):
        """Test failure in fetching highlights."""
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        highlights = get_highlights_by_meeting_id('123')
        self.assertIsNone(highlights)

    def test_missing_api_key(self):
        """Test that a ValueError is raised if the API key is missing."""
        # Ensure the environment variable is not set for this test
        if 'TLDV_API_KEY' in os.environ:
            del os.environ['TLDV_API_KEY']
        
        with self.assertRaises(ValueError):
            get_meetings()
        with self.assertRaises(ValueError):
            get_transcript_by_meeting_id('123')
        with self.assertRaises(ValueError):
            get_highlights_by_meeting_id('123')

if __name__ == '__main__':
    unittest.main()
