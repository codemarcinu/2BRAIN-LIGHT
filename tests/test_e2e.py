import pytest
import os
import sys
import time
import shutil
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import finanse
import wiedza

# Setup directories for E2E
TEST_INPUT_PARAGONY = "./tests/inputs/paragony"
TEST_INPUT_INBOX = "./tests/inputs/inbox"
TEST_ARCHIVE = "./tests/archive"
TEST_VAULT = "./tests/vault"

@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    # Setup
    os.makedirs(TEST_INPUT_PARAGONY, exist_ok=True)
    os.makedirs(TEST_INPUT_INBOX, exist_ok=True)
    os.makedirs(TEST_ARCHIVE, exist_ok=True)
    os.makedirs(TEST_VAULT, exist_ok=True)
    
    yield
    
    # Teardown
    shutil.rmtree("./tests/inputs")
    shutil.rmtree("./tests/archive")
    shutil.rmtree("./tests/vault")

def test_e2e_finance_flow_mocked():
    """
    Simulates placing a file, running batch process, and verifying connection calls.
    We Mock external APIs but use real file system behavior for the orchestrator.
    """
    
    # 1. Prepare environment
    test_file = os.path.join(TEST_INPUT_PARAGONY, "receipt_e2e.jpg")
    with open(test_file, 'w') as f:
        f.write("dummy image content")
        
    with patch('finanse.INPUT_DIR', TEST_INPUT_PARAGONY), \
         patch('finanse.ARCHIVE_DIR', TEST_ARCHIVE), \
         patch('finanse.get_text_from_image', return_value="OCR DATA"), \
         patch('finanse.parse_receipt_with_openai', return_value={"shop": "Test", "total": 100}), \
         patch('finanse.save_to_postgres', return_value=True) as mock_db:
         
        # 2. Run process
        count = finanse.process_batch(verbose=False)
        
        # 3. Verify
        assert count == 1
        mock_db.assert_called_once()
        
        # Check if file moved to archive
        assert not os.path.exists(test_file)
        assert len(os.listdir(TEST_ARCHIVE)) == 1

def test_e2e_knowledge_flow_mocked():
    """
    Simulates knowledge processing flow.
    """
    # 1. Prepare environment
    test_file = os.path.join(TEST_INPUT_INBOX, "note_e2e.txt")
    with open(test_file, 'w') as f:
        f.write("Important thought")

    with patch('wiedza.INBOX_DIR', TEST_INPUT_INBOX), \
         patch('wiedza.ARCHIVE_DIR', TEST_ARCHIVE), \
         patch('wiedza.VAULT_DIR', TEST_VAULT), \
         patch('openai.OpenAI') as MockOpenAI:
         
        mock_client = MockOpenAI.return_value
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = 'Summary'
        mock_client.chat.completions.create.return_value = mock_completion
         
        # 2. Run process
        count = wiedza.process_batch(verbose=False)
        
        # 3. Verify
        assert count == 1
        
        # Check inputs cleared
        assert not os.path.exists(test_file)
        
        # Check vault output created
        vault_files = os.listdir(TEST_VAULT)
        assert len(vault_files) == 1
        assert vault_files[0].startswith("AI_note_e2e")
        
        # Check content
        with open(os.path.join(TEST_VAULT, vault_files[0]), 'r') as f:
            content = f.read()
            assert "Summary" in content
            assert "Important thought" in content
