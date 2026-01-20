import os
import time
import shutil
import json
import io
# import psycopg2 (Removed)
from core.database import SessionLocal, Receipt
from google.cloud import vision
from pdf2image import convert_from_path
# import ollama
from dotenv import load_dotenv
from datetime import datetime
from prompts import RECEIPT_SUMMARY_SYSTEM

load_dotenv()

INPUT_DIR = "./inputs/paragony"
ARCHIVE_DIR = "./archive"

def get_text_from_file(file_path):
    """Google Vision API - OCR (Images & PDFs)"""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        try:
            images = convert_from_path(file_path)
            client = vision.ImageAnnotatorClient()
            full_text = ""
            for image in images:
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='JPEG')
                content = img_byte_arr.getvalue()
                vision_image = vision.Image(content=content)
                response = client.text_detection(image=vision_image)
                if response.text_annotations:
                    full_text += response.text_annotations[0].description + "\n"
            return full_text
        except Exception as e:
            print(f"⚠️ Błąd OCR PDF: {e}")
            return ""
    else:
        try:
            client = vision.ImageAnnotatorClient()
            with open(file_path, "rb") as image_file:
                content = image_file.read()
            image = vision.Image(content=content)
            response = client.text_detection(image=image)
            texts = response.text_annotations
            if texts:
                return texts[0].description
            return ""
        except Exception as e:
            print(f"⚠️ Błąd OCR obrazu: {e}")
            return ""

# Alias for backward compatibility (tests and bot)
get_text_from_image = get_text_from_file

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
    session = SessionLocal()
    try:
        new_receipt = Receipt(
            date=data.get('date'),
            shop_name=data.get('shop', 'Nieznany'),
            total_amount=data.get('total', 0.0),
            category=data.get('category', 'Inne'),
            items_json=[], # No detailed items anymore
            raw_text=raw_text
        )
        session.add(new_receipt)
        session.commit()
        print(f"💰 [FINANSE] Zapisano: {data.get('shop')} | {data.get('total')} PLN | {data.get('category')}")
    except Exception as e:
        session.rollback()
        print(f"❌ Błąd zapisu do DB: {e}")
    finally:
        session.close()

def process_expense_text(text):
    """Przetwarza tekstowy opis wydatku (np. z Voice)"""
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    prompt = f"""
    Przeanalizuj tekst i wyciągnij informację o wydatku.
    Tekst: "{text}"
    Zwróć JSON: {{"shop": "Sklep", "total": 0.0, "category": "Kategoria", "date": "YYYY-MM-DD"}} (dzisiejsza data).
    Jeśli nie jesteś pewien, zgadnij lub ustaw "Nieznany".
    """
    
    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{'role': 'user', 'content': prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        if not data.get('date'): data['date'] = datetime.now().strftime("%Y-%m-%d")
        
        save_to_postgres(data, text)
        return f"✅ Dodano wydatek: {data.get('shop')} ({data.get('total')} PLN)"
    except Exception as e:
        return f"❌ Błąd dodawania wydatku: {e}"

def process_receipt_image(image_path, verbose=True):
    """Funkcja dostępna dla Bota i CLI"""
    if verbose: print(f"⚡ Analiza: {os.path.basename(image_path)}")
    
    # 1. OCR
    text = get_text_from_file(image_path)
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
        
    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf'))]
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
