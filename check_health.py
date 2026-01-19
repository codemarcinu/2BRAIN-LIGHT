import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def check_env():
    required_keys = [
        "OPENAI_API_KEY",
        "TELEGRAM_TOKEN",
        "DB_HOST", "DB_NAME", "DB_USER", "DB_PASS"
    ]
    print("📋 Checking environment variables...")
    missing = []
    for key in required_keys:
        val = os.getenv(key)
        if not val:
            missing.append(key)
        else:
            print(f"✅ {key} is set.")
    
    if missing:
        print(f"❌ Missing: {', '.join(missing)}")
    else:
        print("✅ All required environment variables are set.")

def check_db():
    print("\n🐘 Checking database connectivity...")
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "psql01.mikr.us"),
            database=os.getenv("DB_NAME", "db_joanna114"),
            user=os.getenv("DB_USER", "joanna114"),
            password=os.getenv("DB_PASS"),
            port=os.getenv("DB_PORT", "5432"),
            connect_timeout=5
        )
        print("✅ Database connection successful.")
        conn.close()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    check_env()
    check_db()
