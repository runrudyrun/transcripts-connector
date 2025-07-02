# tests/test_provider_helpers.py

import unittest
from datetime import datetime

from src.provider_helpers import get_conference_id, get_start_time, get_meeting_name, get_meeting_id

class TestProviderHelpers(unittest.TestCase):

    def setUp(self):
        """Set up sample meeting objects for testing."""
        self.tldv_meeting = {
            'id': 'tldv123',
            'name': 'TLDV Test Meeting',
            'extraProperties': {'conferenceId': 'conf-tldv-123'},
            'recordingStartedAt': '2023-01-01T12:00:00Z',
            'source': 'tldv'
        }
        self.fireflies_meeting = {
            'id': 'ff456',
            'title': 'Fireflies Test Meeting',
            'conference': {'id': 'conf-ff-456'},
            'date': 1672574400000,  # Corresponds to 2023-01-01T12:00:00Z
            'source': 'fireflies'
        }

    def test_get_meeting_id(self):
        """Test that the correct meeting ID is extracted."""
        self.assertEqual(get_meeting_id(self.tldv_meeting), 'tldv123')
        self.assertEqual(get_meeting_id(self.fireflies_meeting), 'ff456')

    def test_get_meeting_name(self):
        """Test that the correct meeting name/title is extracted."""
        self.assertEqual(get_meeting_name(self.tldv_meeting), 'TLDV Test Meeting')
        self.assertEqual(get_meeting_name(self.fireflies_meeting), 'Fireflies Test Meeting')

    def test_get_conference_id(self):
        """Test that the correct conference ID is extracted."""
        self.assertEqual(get_conference_id(self.tldv_meeting), 'conf-tldv-123')
        self.assertEqual(get_conference_id(self.fireflies_meeting), 'conf-ff-456')

    def test_get_start_time(self):
        """Test that the start time is correctly parsed into a datetime object."""
        expected_time = datetime(2023, 1, 1, 12, 0, 0)
        # TLDV time is timezone-aware, so we make our expected time aware for comparison
        self.assertEqual(get_start_time(self.tldv_meeting).replace(tzinfo=None), expected_time)
        self.assertEqual(get_start_time(self.fireflies_meeting).replace(tzinfo=None), expected_time)

if __name__ == '__main__':
    unittest.main()
