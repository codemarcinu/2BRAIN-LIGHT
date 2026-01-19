import os
import pantry
import time
import shutil
import json
import psycopg2
from google.cloud import vision
import ollama
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

INPUT_DIR = "./inputs/paragony"
ARCHIVE_DIR = "./archive"

def get_text_from_image(image_path):
    """Google Vision API - OCR"""
    client = vision.ImageAnnotatorClient()
    with open(image_path, "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        return texts[0].description
    return ""

def parse_receipt_with_ollama(ocr_text):
    """Ollama (Qwen) - Text to JSON"""
    prompt = f"""
    Masz poniżej treść paragonu z OCR. Wyciągnij z niego dane w formacie JSON.
    Pola: date (YYYY-MM-DD), shop_name, total_amount (jako float), category (Jedzenie, Chemia, Elektronika, Inne), 
    items (lista produktów, gdzie każdy element to obiekt: {"name": "Nazwa", "price": 10.50, "quantity": 1, "total": 10.50}).
    
    TREŚĆ PARAGONU:
    {ocr_text}
    
    Zwróć TYLKO czysty JSON, bez Markdowna.
    """
    
    response = ollama.chat(model=os.getenv("OLLAMA_MODEL_LOGIC"), messages=[
        {'role': 'user', 'content': prompt},
    ])
    
    try:
        clean_json = response['message']['content'].strip()
        # Czasem modele dodają ```json na początku, usuwamy to
        if clean_json.startswith("```"):
            clean_json = clean_json.split("\n", 1)[1].rsplit("\n", 1)[0]
        return json.loads(clean_json)
    except Exception as e:
        print(f"❌ Błąd parsowania JSON przez Ollama: {e}")
        return None

def save_to_postgres(data, raw_text):
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT")
    )
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO receipts (date, shop_name, total_amount, category, items_json, raw_text)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        data.get('date'),
        data.get('shop_name'),
        data.get('total_amount'),
        data.get('category'),
        json.dumps(data.get('items')),
        raw_text
    ))
    
    conn.commit()
    conn.close()
    print(f"💰 Zapisano w bazie: {data.get('shop_name')} na kwotę {data.get('total_amount')}")

def process_batch(verbose=False):
    """Przetwarza wszystkie pliki w folderze jednorazowo"""
    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    processed_count = 0
    
    if not files:
        if verbose: print("📭 Brak nowych paragonów.")
        return 0

    for file in files:
        full_path = os.path.join(INPUT_DIR, file)
        if verbose: print(f"⚡ Przetwarzam: {file}")
        
        # 1. OCR
        text = get_text_from_image(full_path)
        if not text:
            if verbose: print("⚠️ Nie wykryto tekstu.")
            continue
            
        # 2. AI Parse
        data = parse_receipt_with_ollama(text)
        
        # 3. Save & Archive
        if data:
            save_to_postgres(data, text)
            
            # ---> INTEGRACJA PANTRY
            if 'items' in data and data['items']:
                 print(f"🥦 Przekazuję {len(data['items'])} produktów do modułu Smart Pantry...")
                 count = pantry.add_items_from_receipt(data['items'], data['date'])
                 print(f"✅ Dodano {count} produktów do spiżarni.")
            # <--- KONIEC INTEGRACJI
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.move(full_path, os.path.join(ARCHIVE_DIR, f"{timestamp}_{file}"))
            processed_count += 1
            
    return processed_count

def main_loop():
    """Stara pętla do watchera"""
    print("👀 Obserwuję folder z paragonami...")
    while True:
        process_batch(verbose=True)
        time.sleep(5)

if __name__ == "__main__":
    main_loop()
