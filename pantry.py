import os
import json
import psycopg2
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "psql01.mikr.us"),
        database=os.getenv("DB_NAME", "db_joanna114"),
        user=os.getenv("DB_USER", "joanna114"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT", "5432")
    )

def add_items_from_text(user_text):
    """
    Dodaje produkty na podstawie luźnego tekstu (np. z Voice Message).
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    prompt = f"""
    Użytkownik powiedział: "{user_text}".
    Wyciągnij z tego listę zakupionych/przyniesionych produktów spożywczych.
    Oszacuj ich datę ważności (days) i kategorię (Pieczywo, Nabiał, Warzywa, Mięso, Inne).
    Zwróć JSON: {{"products": [{{"name": "Chleb", "category": "Pieczywo", "days": 3}}]}}
    Jeśli nic nie znaleziono, zwróć pustą listę.
    """
    
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[{'role': 'user', 'content': prompt}],
        response_format={"type": "json_object"}
    )
    
    try:
        content = response.choices[0].message.content
        data = json.loads(content)
        products = data.get("products", [])
    except Exception as e:
        print(f"❌ Pantry AI Error: {e}")
        return 0
        
    if not products:
        return 0

    conn = get_db_connection()
    cur = conn.cursor()
    
    count = 0
    for p in products:
        cur.execute("""
            INSERT INTO pantry (product_name, category, purchase_date, estimated_expiry, status)
            VALUES (%s, %s, CURRENT_DATE, CURRENT_DATE + interval '%s days', 'IN_STOCK')
        """, (p['name'], p.get('category', 'Inne'), p.get('days', 7)))
        count += 1
        
    conn.commit()
    conn.close()
    return count

def get_all_stock():
    """Pobiera listę nazw produktów w lodówce"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT product_name FROM pantry WHERE status = 'IN_STOCK'")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]

def process_human_feedback(candidates, user_comment):
    """
    Analizuje luźny komentarz (np. 'zjadłem ser') w kontekście produktów w lodówce.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # candidates to lista słowników, ale tutaj uprościmy przekazując same nazwy
    # w realnym systemie ID są konieczne, ale Voice jest 'fuzzy'.
    
    prompt = f"""
    Twoim celem jest aktualizacja statusu produktów.
    Mamy w lodówce: {json.dumps(candidates, ensure_ascii=False)}
    Użytkownik powiedział: "{user_comment}"
    
    Zwróć JSON z listą akcji:
    {{"actions": [
       {{"name": "Ser", "action": "CONSUMED"}}, 
       {{"name": "Szynka", "action": "TRASHED"}}
    ]}}
    Użyj fuzzy matchingu. Jeśli nie ma pewności, pomiń.
    """
    
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[{'role': 'user', 'content': prompt}],
        response_format={"type": "json_object"}
    )
    
    stats = {"consumed": 0, "trashed": 0, "extended": 0}
    
    try:
        data = json.loads(response.choices[0].message.content)
        actions = data.get("actions", [])
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        for action in actions:
            # Tu jest uproszczenie: bierzemy pierwszy pasujący produkt. 
            # W SQL 'LIKE' lub trigram search byłby lepszy.
            cur.execute("""
                UPDATE pantry 
                SET status = %s 
                WHERE product_name ILIKE %s AND status = 'IN_STOCK'
            """, (action['action'], f"%{action['name']}%"))
            
            if cur.rowcount > 0:
                key = action['action'].lower()
                if key in stats: 
                    stats[key] += cur.rowcount
                elif key == 'trashed': # mapowanie jeśli inne
                     stats['trashed'] += cur.rowcount
                conn.commit() # commit per action for safety? No, outside loop better but here we verify rowcount
                
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"❌ Pantry Update Error: {e}")
        return None
        
    return stats
