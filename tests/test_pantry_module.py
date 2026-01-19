import pytest
import json
from unittest.mock import MagicMock, patch
from datetime import date

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pantry

@pytest.fixture
def mock_db():
    with patch('pantry.get_db_connection') as mock_get_db:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        yield mock_conn, mock_cur

@pytest.fixture
def mock_openai():
    with patch('openai.OpenAI') as MockOpenAI:
        mock_client = MockOpenAI.return_value
        yield mock_client

def test_add_items_from_text(mock_db, mock_openai):
    mock_conn, mock_cur = mock_db
    
    # Mock OpenAI response
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = json.dumps({
        "products": [
            {"name": "Mleko", "days": 7, "category": "Nabiał"},
            {"name": "Ryż", "days": 365, "category": "Suche"}
        ]
    })
    mock_openai.chat.completions.create.return_value = mock_completion

    user_text = "Kupiłem mleko i ryż"
    
    # Run
    added_count = pantry.add_items_from_text(user_text)
    
    # Assert
    assert added_count == 2
    assert mock_cur.execute.call_count == 2
    
    calls = mock_cur.execute.call_args_list
    assert "INSERT INTO pantry" in calls[0][0][0]
    assert "Mleko" in calls[0][0][1]

def test_get_all_stock(mock_db):
    mock_conn, mock_cur = mock_db
    mock_cur.fetchall.return_value = [("Mleko",), ("Chleb",)]

    stock = pantry.get_all_stock()
    
    assert len(stock) == 2
    assert "Mleko" in stock
    assert "Chleb" in stock

def test_process_human_feedback(mock_db, mock_openai):
    mock_conn, mock_cur = mock_db
    
    # Mock OpenAI response
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = json.dumps({
        "actions": [
            {"name": "Mleko", "action": "CONSUMED"}
        ]
    })
    mock_openai.chat.completions.create.return_value = mock_completion
    mock_cur.rowcount = 1

    candidates = ["Mleko", "Chleb"]
    user_comment = "Wypiłem mleko"
    
    stats = pantry.process_human_feedback(candidates, user_comment)
    
    assert stats["consumed"] == 1
    assert mock_cur.execute.call_count == 1
    
    args = mock_cur.execute.call_args[0]
    assert "UPDATE pantry" in args[0]
    assert "CONSUMED" in args[1]
    assert "%Mleko%" in args[1]
