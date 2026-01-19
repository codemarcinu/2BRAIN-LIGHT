import os
from google.cloud import vision
from dotenv import load_dotenv

load_dotenv()

def manual_pdf_ocr(pdf_path):
    print(f"Testing OCR on: {pdf_path}")
    client = vision.ImageAnnotatorClient()
    
    with open(pdf_path, "rb") as f:
        content = f.read()
    
    # Try sending it as a general image first (unlikely to work for PDF)
    try:
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        if response.text_annotations:
            print("OCR Success (as image):")
            print(response.text_annotations[0].description)
            return True
        else:
            print("OCR failed to find text (as image).")
    except Exception as e:
        print(f"Error as image: {e}")

    # For PDF, we need a different approach
    print("Trying document_text_detection for PDF...")
    try:
        # This requires gcs for large files, but for small files? 
        # Actually Google Vision's simple API doesn't support PDF at all.
        # It needs to be a GCS source for BatchAnnotateFiles.
        pass
    except Exception as e:
        print(f"Error for PDF: {e}")
    
    return False

if __name__ == "__main__":
    manual_pdf_ocr("inputs/paragony/2601176723143218.pdf")
