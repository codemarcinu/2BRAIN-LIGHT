import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def create_tables():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT")
    )
    cur = conn.cursor()
    
    # Tabela Paragonów (zoptymalizowana pod przyszłe AI)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            id SERIAL PRIMARY KEY,
            date DATE,
            shop_name VARCHAR(255),
            total_amount DECIMAL(10, 2),
            category VARCHAR(100),
            items_json JSONB,
            raw_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Tabela: pantry (Spiżarnia + Lodówka)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pantry (
            id SERIAL PRIMARY KEY,
            product_name VARCHAR(255),
            category VARCHAR(100),
            purchase_date DATE,
            estimated_expiry DATE,
            status VARCHAR(50) DEFAULT 'IN_STOCK', -- IN_STOCK, CONSUMED, TRASHED
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Tabela 'receipts' została utworzona na serwerze Mikr.us.")

if __name__ == "__main__":
    create_tables()
