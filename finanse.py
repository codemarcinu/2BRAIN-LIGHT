import os
import time
import shutil
import json
import psycopg2
from google.cloud import vision
# import ollama
from dotenv import load_dotenv
from datetime import datetime
from prompts import RECEIPT_SUMMARY_SYSTEM

load_dotenv()

INPUT_DIR = "./inputs/paragony"
ARCHIVE_DIR = "./archive"

def get_text_from_image(image_path):
    """Google Vision API - OCR"""
    try:
        client = vision.ImageAnnotatorClient()
        with open(image_path, "rb") as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        texts = response.text_annotations
        if texts:
            return texts[0].description
        return ""
    except Exception as e:
        print(f"⚠️ Błąd OCR: {e}")
        return ""

def parse_receipt_with_openai(ocr_text):
    """OpenAI (GPT-4o-mini) - Text to JSON Summary"""
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {'role': 'system', 'content': RECEIPT_SUMMARY_SYSTEM},
            {'role': 'user', 'content': f"PARAGON:\n{ocr_text}"},
        ],
        response_format={"type": "json_object"}
    )
    
    try:
        clean_json = response.choices[0].message.content
        return json.loads(clean_json)
    except Exception as e:
        print(f"❌ Błąd parsowania AI (OpenAI): {e}")
        return None

def save_to_postgres(data, raw_text):
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "psql01.mikr.us"),
            database=os.getenv("DB_NAME", "db_joanna114"),
            user=os.getenv("DB_USER", "joanna114"),
            password=os.getenv("DB_PASS"),
            port=os.getenv("DB_PORT", "5432")
        )
        cur = conn.cursor()
        
        # Schema expects items_json, so we pass empty list to satisfy it
        # The prompt returns keys: shop, date, total, category, currency
        
        cur.execute("""
            INSERT INTO receipts (date, shop_name, total_amount, category, items_json, raw_text)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data.get('date'),
            data.get('shop', 'Nieznany'),
            data.get('total', 0.0),
            data.get('category', 'Inne'),
            json.dumps([]), # No detailed items anymore
            raw_text
        ))
        
        conn.commit()
        conn.close()
        print(f"💰 [FINANSE] Zapisano: {data.get('shop')} | {data.get('total')} PLN | {data.get('category')}")
    except Exception as e:
        print(f"❌ Błąd zapisu do DB: {e}")

def process_receipt_image(image_path, verbose=True):
    """Funkcja dostępna dla Bota i CLI"""
    if verbose: print(f"⚡ Analiza: {os.path.basename(image_path)}")
    
    # 1. OCR
    text = get_text_from_image(image_path)
    if not text:
        return "⚠️ OCR nie odczytał tekstu."
        
    # 2. AI Summary
    data = parse_receipt_with_openai(text)
    if not data:
        return "⚠️ AI nie zrozumiało paragonu."
    
    # 3. Save
    save_to_postgres(data, text)
    
    return f"✅ Dodano: {data.get('shop')} ({data.get('total')} PLN) [{data.get('category')}]"

def process_batch(verbose=False):
    """Batch processing folderu"""
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
        
    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    processed_count = 0
    
    for file in files:
        full_path = os.path.join(INPUT_DIR, file)
        result_msg = process_receipt_image(full_path, verbose)
        if verbose: print(result_msg)
        
        if "✅" in result_msg:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if not os.path.exists(ARCHIVE_DIR):
                os.makedirs(ARCHIVE_DIR)
            shutil.move(full_path, os.path.join(ARCHIVE_DIR, f"{timestamp}_{file}"))
            processed_count += 1
            
    return processed_count

def main_loop():
    print("👀 [FINANSE] Obserwuję folder inputs/paragony...")
    while True:
        process_batch(verbose=True)
        time.sleep(10)

if __name__ == "__main__":
    main_loop()
