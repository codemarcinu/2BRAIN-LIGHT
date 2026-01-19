import os
import json
import psycopg2
from openai import OpenAI
from datetime import datetime, timedelta
from dotenv import load_dotenv
import prompts  # Importujemy nasze prompty

load_dotenv()

# Klient OpenAI (używamy gpt-4o-mini bo jest tani i świetny w JSON)
# Uwaga: Upewnij się, że OPENAI_API_KEY jest ustawiony w .env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"), database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"), password=os.getenv("DB_PASS"), port=os.getenv("DB_PORT")
    )

# --- 1. IMPORTOWANIE (Podczas skanowania paragonu) ---

def add_items_from_receipt(items_list, purchase_date_str):
    """Analizuje listę z paragonu i dodaje jedzenie do bazy"""
    print("🥦 AI analizuje trwałość produktów...")
    
    user_content = f"DATA ZAKUPU: {purchase_date_str}\nLISTA POZYCJI: {json.dumps(items_list)}"
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": prompts.ESTIMATE_EXPIRY_SYSTEM},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        products = result.get("products", []) # Zakładamy że AI zwróci klucz "products"
        
        conn = get_db()
        cur = conn.cursor()
        purchase_date = datetime.strptime(purchase_date_str, "%Y-%m-%d").date()
        
        added_count = 0
        for p in products:
            expiry = purchase_date + timedelta(days=p.get('days', 7))
            cur.execute("""
                INSERT INTO pantry (product_name, category, purchase_date, estimated_expiry)
                VALUES (%s, %s, %s, %s)
            """, (p['name'], p.get('category', 'Inne'), purchase_date, expiry))
            added_count += 1
            
        conn.commit()
        conn.close()
        return added_count

    except Exception as e:
        print(f"❌ Błąd OpenAI przy imporcie: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 0

# --- 2. POBIERANIE DANYCH ---

def get_expired_candidates():
    """Zwraca listę produktów przeterminowanych do weryfikacji"""
    conn = get_db()
    cur = conn.cursor()
    # Pobieramy wszystko co ma datę ważności <= DZISIAJ
    cur.execute("""
        SELECT id, product_name, estimated_expiry, category
        FROM pantry 
        WHERE status = 'IN_STOCK' AND estimated_expiry <= CURRENT_DATE
        ORDER BY estimated_expiry ASC
    """)
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "expiry": str(r[2]), "cat": r[3]} for r in rows]

def get_dashboard_stats():
    """Zwraca co mamy w lodówce"""
    conn = get_db()
    cur = conn.cursor()
    # Psujące się w ciągu 4 dni
    cur.execute("SELECT product_name, estimated_expiry FROM pantry WHERE status='IN_STOCK' AND estimated_expiry <= CURRENT_DATE + 4 ORDER BY estimated_expiry")
    expiring = cur.fetchall()
    # Cała reszta
    cur.execute("SELECT COUNT(*) FROM pantry WHERE status='IN_STOCK'")
    total_count = cur.fetchone()[0]
    conn.close()
    return expiring, total_count

# --- 3. CLEANUP (MAN IN THE LOOP) ---

def process_human_feedback(candidates, user_input):
    """Kluczowa funkcja: User mówi co zjadł, AI aktualizuje bazę"""
    
    # Przygotowanie danych dla AI
    candidates_json = json.dumps([{k: v for k, v in c.items()} for c in candidates], ensure_ascii=False)
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": prompts.CLEANUP_SYSTEM},
                {"role": "user", "content": f"LISTA: {candidates_json}\nKOMENTARZ: {user_input}"}
            ],
            response_format={"type": "json_object"}
        )
        
        actions = json.loads(response.choices[0].message.content).get("updates", [])
        
        conn = get_db()
        cur = conn.cursor()
        
        stats = {"consumed": 0, "trashed": 0, "extended": 0}
        
        for action in actions:
            p_id = action['id']
            status = action['status']
            
            if status in ['CONSUMED', 'TRASHED']:
                cur.execute("UPDATE pantry SET status=%s WHERE id=%s", (status, p_id))
                stats[status.lower()] += 1
                
            elif status == 'EXTEND':
                days = action.get('extend_days', 3)
                # Ustawiamy nową datę ważności = DZIŚ + days
                cur.execute("UPDATE pantry SET estimated_expiry = CURRENT_DATE + INTERVAL '%s days' WHERE id=%s", (days, p_id))
                stats["extended"] += 1
                
        conn.commit()
        conn.close()
        return stats

    except Exception as e:
        print(f"❌ Błąd HITL: {e}")
        return None

# --- 4. OBIAD (RAG-LITE) ---

def suggest_recipe():
    conn = get_db()
    cur = conn.cursor()
    
    # 1. Pobierz pilne
    cur.execute("SELECT product_name FROM pantry WHERE status='IN_STOCK' AND estimated_expiry <= CURRENT_DATE + 3")
    urgent = [r[0] for r in cur.fetchall()]
    
    # 2. Pobierz resztę (jako tło)
    cur.execute("SELECT product_name FROM pantry WHERE status='IN_STOCK' LIMIT 30")
    others = [r[0] for r in cur.fetchall()]
    conn.close()
    
    if not urgent and not others:
        return "Lodówka pusta. Zamów pizzę."

    user_msg = f"PILNE SKŁADNIKI: {', '.join(urgent)}\nPOZOSTAŁE: {', '.join(others)}"
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": prompts.DINNER_SYSTEM},
            {"role": "user", "content": user_msg}
        ]
    )
    return response.choices[0].message.content
