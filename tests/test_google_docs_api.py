import unittest
import os

# Add the src directory to the Python path to allow imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import patch, MagicMock
import os

# Add the src directory to the Python path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.google_docs_api import create_google_doc, share_file_publicly

class TestGoogleDocsApi(unittest.TestCase):

    @patch('src.google_docs_api.build')
    def test_create_google_doc(self, mock_build):
        """Test the successful creation of a Google Doc."""
        mock_docs_service = MagicMock()
        mock_drive_service = MagicMock()

        # Mock the build function to return our service mocks
        def build_side_effect(serviceName, version, credentials):
            if serviceName == 'docs':
                return mock_docs_service
            elif serviceName == 'drive':
                return mock_drive_service
            return MagicMock()
        mock_build.side_effect = build_side_effect

        # Mock the Docs API call chain explicitly
        mock_create_request = MagicMock()
        mock_create_request.execute.return_value = {'documentId': 'doc123'}
        mock_docs_service.documents().create.return_value = mock_create_request

        # Mock the Drive API call chains
        mock_drive_service.files().get.return_value.execute.return_value = {'parents': ['old_parent']}
        mock_drive_service.files().update.return_value.execute.return_value = {}

        # Call the function under test
        doc_id = create_google_doc('dummy_creds', 'Test Doc', 'Hello', shared_drive_id='drive123')

        # Assertions
        self.assertEqual(doc_id, 'doc123')
        mock_docs_service.documents().create.assert_called_once_with(body={'title': 'Test Doc'})
        mock_docs_service.documents().batchUpdate.assert_called_once()
        mock_drive_service.files().update.assert_called_once()

    @patch('src.google_docs_api.build')
    def test_share_file_publicly(self, mock_build):
        """Test successfully making a file public."""
        mock_drive_service = MagicMock()
        mock_build.return_value = mock_drive_service

        mock_drive_service.permissions().create().execute.return_value = {'id': 'perm123'}
        mock_drive_service.files().get().execute.return_value = {'webViewLink': 'http://docs.google.com/123'}

        result = share_file_publicly('dummy_creds', 'file123')

        self.assertIn('webViewLink', result)
        self.assertEqual(result['webViewLink'], 'http://docs.google.com/123')

if __name__ == '__main__':
    unittest.main()
