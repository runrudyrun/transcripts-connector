import unittest
import os

# Add the src directory to the Python path to allow imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.google_docs_api import create_document, insert_text, share_document

class TestGoogleDocsApi(unittest.TestCase):

    def test_create_document(self):
        """Test that the stub for create_document returns a dummy ID."""
        doc_id = create_document('dummy_creds', 'Test Title')
        self.assertEqual(doc_id, 'dummy_document_id')

    def test_insert_text(self):
        """Test that the stub for insert_text returns True."""
        result = insert_text('dummy_creds', 'dummy_doc_id', 'some text')
        self.assertTrue(result)

    def test_share_document(self):
        """Test that the stub for share_document returns True."""
        result = share_document('dummy_creds', 'dummy_doc_id', ['test@example.com'])
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
