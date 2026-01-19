import pytest
from unittest.mock import MagicMock, patch
import os
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import wiedza

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("INBOX_DIR", "./inputs/inbox")
    monkeypatch.setenv("VAULT_DIR", "./vault/inbox")
    monkeypatch.setenv("ARCHIVE_DIR", "./archive")
    monkeypatch.setenv("OLLAMA_MODEL_POLISH", "bielik")

def test_process_note_success(mock_env):
    with patch('builtins.open', new_callable=MagicMock) as mock_open, \
         patch('wiedza.ollama.chat') as mock_chat, \
         patch('os.path.exists', return_value=True):
        
        # Setup mocks
        mock_chat.return_value = {'message': {'content': 'AI Summary'}}
        file_handle = mock_open.return_value.__enter__.return_value
        file_handle.read.return_value = "Original Content"
        
        wiedza.process_note("dummy/path/note.txt")
        
        # Verify write happened with expected content
        # We expect 2 opens: read input, write output
        assert mock_open.call_count == 2
        
        # Verify content written to new file
        # The second open is for writing
        handle = mock_open.return_value.__enter__.return_value
        handle.write.assert_called_with("AI Summary\n\n---\n### Źródło:\nOriginal Content")

def test_process_batch_no_files(mock_env):
    with patch('os.listdir', return_value=[]):
        count = wiedza.process_batch(verbose=False)
        assert count == 0

def test_process_batch_success(mock_env):
    with patch('os.listdir', return_value=['note.txt']), \
         patch('wiedza.process_note') as mock_process, \
         patch('shutil.move') as mock_move:
        
        count = wiedza.process_batch(verbose=False)
        assert count == 1
        mock_process.assert_called_with(os.path.join(wiedza.INBOX_DIR, 'note.txt'))
        mock_move.assert_called_once()
