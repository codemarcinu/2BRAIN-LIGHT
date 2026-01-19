import pytest
import json
from unittest.mock import MagicMock, patch
from datetime import date, timedelta

# Importujemy nasz moduł
# Zakładamy, że tests/ jest w 2brain_lite/tests, a pantry.py w 2brain_lite/
# Pytest powinien dodać root dir do path, ale dla pewności:
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pantry

@pytest.fixture
def mock_db():
    with patch('pantry.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        yield mock_conn, mock_cur

@pytest.fixture
def mock_openai():
    with patch('pantry.client') as mock_client:
        yield mock_client

def test_add_items_from_receipt(mock_db, mock_openai):
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

    items = [{"name": "Mleko 3.2"}, {"name": "Ryż basmati"}]
    purchase_date = "2023-10-01"
    
    # Run
    added_count = pantry.add_items_from_receipt(items, purchase_date)
    
    # Assert
    assert added_count == 2
    assert mock_cur.execute.call_count == 2
    
    # Sprawdzamy czy inserty poszły (uproszczone)
    calls = mock_cur.execute.call_args_list
    assert "INSERT INTO pantry" in calls[0][0][0]
    assert "Mleko" in calls[0][0][1] # val arg 1
    assert "Ryż" in calls[1][0][1]

def test_get_dashboard_stats(mock_db):
    mock_conn, mock_cur = mock_db
    
    # Mock return values for two queries
    # 1. Expiring soon
    # 2. Total count
    mock_cur.fetchall.return_value = [("Ser", date(2023, 10, 5))]
    mock_cur.fetchone.return_value = [15]

    expiring, total = pantry.get_dashboard_stats()
    
    assert len(expiring) == 1
    assert expiring[0][0] == "Ser"
    assert total == 15

def test_process_human_feedback(mock_db, mock_openai):
    mock_conn, mock_cur = mock_db
    
    # Mock OpenAI response
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = json.dumps({
        "updates": [
            {"id": 1, "status": "CONSUMED"},
            {"id": 2, "status": "EXTEND", "extend_days": 5}
        ]
    })
    mock_openai.chat.completions.create.return_value = mock_completion

    candidates = [{"id": 1, "name": "Szynka"}, {"id": 2, "name": "Ogórek"}]
    user_input = "Szynkę zjadłem, ogórek jeszcze dobry"
    
    stats = pantry.process_human_feedback(candidates, user_input)
    
    assert stats["consumed"] == 1
    assert stats["extended"] == 1
    assert stats["trashed"] == 0
    
    # Verify DB updates
    assert mock_cur.execute.call_count == 2
    # Check first update (CONSUMED)
    args1 = mock_cur.execute.call_args_list[0][0]
    assert "UPDATE pantry SET status=%s" in args1[0]
    assert args1[1] == ("CONSUMED", 1)
    
    # Check second update (EXTEND)
    args2 = mock_cur.execute.call_args_list[1][0]
    assert "UPDATE pantry SET estimated_expiry" in args2[0]
    assert args2[1] == (5, 2)

def test_suggest_recipe(mock_db, mock_openai):
    mock_conn, mock_cur = mock_db
    
    # Mock DB returns
    # 1. Urgent
    # 2. Others
    mock_cur.fetchall.side_effect = [
        [("Jajka",), ("Śmietana",)], # Urgent
        [("Mąka",), ("Cukier",)]     # Others
    ]
    
    # Mock OpenAI
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = "Omlet biszkoptowy"
    mock_completion.choices[0].message.content = "Omlet biszkoptowy" 
    mock_openai.chat.completions.create.return_value = mock_completion # Fix return logic
    
    recipe = pantry.suggest_recipe()
    
    assert recipe == "Omlet biszkoptowy"
    # Ensure correct prompt context was constructed (checking args passed to OpenAI)
    call_args = mock_openai.chat.completions.create.call_args
    messages = call_args[1]['messages']
    user_content = messages[1]['content']
    assert "PILNE SKŁADNIKI: Jajka, Śmietana" in user_content
