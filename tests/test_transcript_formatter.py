import unittest
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.transcript_formatter import format_highlights

class TestTranscriptFormatter(unittest.TestCase):

    def test_format_highlights_success(self):
        """Test successful formatting of highlights."""
        highlights_data = {
            'highlights': [
                {'timestamp': 120, 'text': 'First key moment.'},
                {'timestamp': 305, 'text': 'Another important point.'}
            ]
        }
        expected_output = (
            "AI Notes (Highlights):\n\n"
            "- [00:02:00] First key moment.\n"
            "- [00:05:05] Another important point."
        )
        formatted_text = format_highlights(highlights_data)
        self.assertEqual(formatted_text, expected_output)

    def test_format_highlights_empty(self):
        """Test formatting with no highlights."""
        highlights_data = {'highlights': []}
        expected_output = "AI Notes (Highlights):\n\nNo highlights were generated for this meeting."
        formatted_text = format_highlights(highlights_data)
        self.assertEqual(formatted_text, expected_output)

    def test_format_highlights_none(self):
        """Test formatting with None as input."""
        formatted_text = format_highlights(None)
        self.assertIn("No highlights were generated", formatted_text)

    def test_format_highlights_missing_key(self):
        """Test formatting with missing 'highlights' key."""
        highlights_data = {'other_key': 'some_value'}
        formatted_text = format_highlights(highlights_data)
        self.assertIn("No highlights were generated", formatted_text)

if __name__ == '__main__':
    unittest.main()
