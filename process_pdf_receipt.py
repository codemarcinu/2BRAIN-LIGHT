import os
import json
from pdf2image import convert_from_path
from google.cloud import vision
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def get_text_from_pdf(pdf_path):
    print(f"Converting PDF to images: {pdf_path}")
    images = convert_from_path(pdf_path)
    client = vision.ImageAnnotatorClient()
    full_text = ""
    
    for i, image in enumerate(images):
        print(f"Processing page {i+1}...")
        # Save image to bytes
        import io
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        content = img_byte_arr.getvalue()
        
        vision_image = vision.Image(content=content)
        response = client.text_detection(image=vision_image)
        if response.text_annotations:
            full_text += response.text_annotations[0].description + "\n"
            
    return full_text

def parse_with_ai(text):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    from prompts import RECEIPT_SUMMARY_SYSTEM
    
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {'role': 'system', 'content': RECEIPT_SUMMARY_SYSTEM},
            {'role': 'user', 'content': f"PARAGON:\n{text}"},
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

if __name__ == "__main__":
    pdf_path = "inputs/paragony/2601176723143218.pdf"
    if os.path.exists(pdf_path):
        text = get_text_from_pdf(pdf_path)
        print("OCR Text extracted.")
        print(text[:500] + "...")
        
        data = parse_with_ai(text)
        print("AI Result:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"File not found: {pdf_path}")
