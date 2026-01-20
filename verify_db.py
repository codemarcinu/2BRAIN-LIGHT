from core.database import SessionLocal
import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

def test_db():
    print("Testing DB connection...")
    try:
        session = SessionLocal()
        result = session.execute("SELECT 1").scalar()
        print(f"✅ DB Connection successful! Result: {result}")
        session.close()
    except Exception as e:
        print(f"❌ DB Connection failed: {e}")

if __name__ == "__main__":
    test_db()
