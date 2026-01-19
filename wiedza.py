import os
import shutil
import ollama
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

INBOX_DIR = "./inputs/inbox"
VAULT_DIR = "C:/Sciezka/Do/Twojego/Obsidian/Inbox" # <-- ZMIEŃ NA SWOJĄ
ARCHIVE_DIR = "./archive"

def process_note(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    prompt = f"""
    Jesteś ekspertem od zarządzania wiedzą (PKM). Przeanalizuj poniższy tekst.
    1. Stwórz krótkie podsumowanie (TL;DR).
    2. Wypisz 3-5 kluczowych wniosków.
    3. Zaproponuj tagi w formacie YAML frontmatter.
    
    TEKST:
    {content}
    """
    
    # Używamy Bielika dla lepszej polszczyzny lub Qwena dla szybkości
    response = ollama.chat(model=os.getenv("OLLAMA_MODEL_POLISH"), messages=[
        {'role': 'user', 'content': prompt},
    ])
    
    ai_output = response['message']['content']
    
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
