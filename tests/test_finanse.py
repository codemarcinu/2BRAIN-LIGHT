import pytest
from unittest.mock import MagicMock, patch
import os
import sys
import json

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import finanse

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("INPUT_DIR", "./inputs/paragony")
    monkeypatch.setenv("ARCHIVE_DIR", "./archive")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASS", "pass")
    monkeypatch.setenv("DB_PORT", "5432")

def test_get_text_from_image_no_text(mock_env):
    with patch('finanse.vision.ImageAnnotatorClient') as MockClient:
        mock_client = MockClient.return_value
        mock_client.text_detection.return_value.text_annotations = []
        
        with patch('builtins.open', new_callable=MagicMock) as mock_open:
            # Mock file read to return bytes
            mock_open.return_value.__enter__.return_value.read.return_value = b"dummy_content"
            text = finanse.get_text_from_image("dummy_path.jpg")
            assert text == ""

def test_get_text_from_image_success(mock_env):
    with patch('finanse.vision.ImageAnnotatorClient') as MockClient:
        mock_client = MockClient.return_value
        mock_annotation = MagicMock()
        mock_annotation.description = "PARAGON 123"
        mock_client.text_detection.return_value.text_annotations = [mock_annotation]
        
        with patch('builtins.open', new_callable=MagicMock) as mock_open:
            # Mock file read to return bytes
            mock_open.return_value.__enter__.return_value.read.return_value = b"dummy_content"
            text = finanse.get_text_from_image("dummy_path.jpg")
            assert text == "PARAGON 123"

def test_parse_receipt_with_ollama_success(mock_env):
    with patch('finanse.ollama.chat') as mock_chat:
        mock_chat.return_value = {
            'message': {
                'content': '{"date": "2023-01-01", "shop_name": "TestShop", "total_amount": 10.0, "category": "Jedzenie", "items": []}'
            }
        }
        
        data = finanse.parse_receipt_with_ollama("RAW TEXT")
        assert data['shop_name'] == "TestShop"
        assert data['total_amount'] == 10.0

def test_parse_receipt_with_ollama_markdown_strip(mock_env):
    with patch('finanse.ollama.chat') as mock_chat:
        mock_chat.return_value = {
            'message': {
                'content': '```json\n{"date": "2023-01-01", "shop_name": "TestShop", "total_amount": 10.0, "category": "Jedzenie", "items": []}\n```'
            }
        }
        
        data = finanse.parse_receipt_with_ollama("RAW TEXT")
        assert data['shop_name'] == "TestShop"

def test_process_batch_no_files(mock_env):
    with patch('os.listdir', return_value=[]):
        count = finanse.process_batch(verbose=False)
        assert count == 0

def test_process_batch_success(mock_env):
    with patch('os.listdir', return_value=['receipt.jpg']), \
         patch('finanse.get_text_from_image', return_value="RAW CONTENT"), \
         patch('finanse.parse_receipt_with_ollama', return_value={'shop_name': 'Test'}), \
         patch('finanse.save_to_postgres') as mock_save, \
         patch('shutil.move') as mock_move:
        
        count = finanse.process_batch(verbose=False)
        assert count == 1
        mock_save.assert_called_once()
        mock_move.assert_called_once()
