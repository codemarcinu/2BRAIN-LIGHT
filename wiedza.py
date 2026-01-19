import os
import shutil
# import ollama
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

VAULT_DIR = os.getenv("OBSIDIAN_VAULT_PATH") or os.getenv("VAULT_PATH") or "./data/vault"
INBOX_DIR = "./inputs/inbox"
ARCHIVE_DIR = "./archive"

if not os.path.exists(VAULT_DIR):
    try:
        os.makedirs(VAULT_DIR, exist_ok=True)
    except Exception as e:
        print(f"⚠️ Nie można utworzyć katalogu VAULT: {e}. Używam ./data/vault")
        VAULT_DIR = "./data/vault"
        os.makedirs(VAULT_DIR, exist_ok=True)


def process_note(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    content = ""
    
    if ext == '.pdf':
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    content += text + "\n"
        except Exception as e:
            print(f"❌ Błąd odczytu PDF: {e}")
            return
    else:
        # Default text handling
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            print(f"❌ Błąd kodowania pliku: {file_path}")
            return

    if not content.strip():
        print("⚠️ Pusta zawartość notatki.")
        return
        
    prompt = f"""
    Jesteś ekspertem od zarządzania wiedzą (PKM). Przeanalizuj poniższy tekst.
    1. Stwórz krótkie podsumowanie (TL;DR).
    2. Wypisz 3-5 kluczowych wniosków.
    3. Zaproponuj tagi w formacie YAML frontmatter.
    
    TEKST:
    {content}
    """
    
    # Używamy OpenAI (GPT-4o-mini) zamiast Ollamy
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {'role': 'user', 'content': prompt},
        ]
    )
    
    ai_output = response.choices[0].message.content
    
    # Tworzenie pliku .md
    filename = os.path.basename(file_path).replace('.txt', '.md')
    final_path = os.path.join(VAULT_DIR, f"AI_{filename}")
    
    with open(final_path, 'w', encoding='utf-8') as f:
        f.write(f"{ai_output}\n\n---\n### Źródło:\n{content}")
        
    print(f"🧠 Utworzono notatkę: {final_path}")

def process_batch(verbose=False):
    files = [f for f in os.listdir(INBOX_DIR) if f.endswith('.txt')]
    processed_count = 0
    
    if not files:
        if verbose: print("📭 Inbox pusty.")
        return 0

    for file in files:
        full_path = os.path.join(INBOX_DIR, file)
        process_note(full_path)
        shutil.move(full_path, os.path.join(ARCHIVE_DIR, file))
        processed_count += 1
        
    return processed_count

def main_loop():
    print("📚 Obserwuję Inbox...")
    while True:
        process_batch(verbose=True)
        time.sleep(5)

if __name__ == "__main__":
    main_loop()
