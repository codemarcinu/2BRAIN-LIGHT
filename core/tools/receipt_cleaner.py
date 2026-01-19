import os
import re
import json
from pathlib import Path
from datetime import datetime
from config import ProjectConfig
from utils.receipt_agents import detect_shop

# Import Pipeline (jeśli dostępny)
try:
    from core.pipelines.receipt_pipeline import AsyncReceiptPipeline
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False

class ReceiptSanitizer:
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        # Force async pipeline usage for this implementation
        self.pipeline = AsyncReceiptPipeline() if ASYNC_AVAILABLE else None

    def run_batch(self):
        """Skanuje folder wejsciowy i przetwarza paragony"""
        print(f"Scanning {self.vault_path}...")
        count = 0
        for file_path in self.vault_path.glob("**/*.md"):
            if self.sanitize_file(file_path):
                print(f"Processed: {file_path.name}")
                count += 1
        print(f"Total processed: {count}")

    def sanitize_file(self, file_path: Path) -> bool:
        # Odczyt pliku
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if "to-verify" not in content:
            print(f"Skipping {file_path.name}: 'to-verify' tag not found")
            return False
            
        if "## 📜 Oryginalny OCR" not in content:
            print(f"Skipping {file_path.name}: OCR section not found")
            return False

        # Wyciągnij OCR
        ocr_match = re.search(r'## 📜 Oryginalny OCR\s*\n(.*?)(?=\n#|\Z)', content, re.DOTALL)
        if not ocr_match: return False
        ocr_text = ocr_match.group(1).strip()
        shop = detect_shop(ocr_text)

        # Wywołanie Pipeline
        data = {}
        if self.pipeline:
            print(f"Processing receipt from {shop} via Pipeline...")
            try:
                result = self.pipeline.process_receipt_sync(ocr_text, shop)
                data = {
                    'items': result.get('items', []),
                    'date': result.get('date'),
                    'total': result.get('total_amount', 0),
                    'shop': shop
                }
            except Exception as e:
                print(f"Pipeline error: {e}")
                return False
        else:
            print("Pipeline unavailable.")
            return False

        # Aktualizacja treści notatki (Tabela Markdown + JSON)
        items = data.get('items', [])
        new_table = self._markdown_table_from_items(items)
        
        # Wstawienie tabeli (jeśli już jest sekcja Produkty, podmienia, jeśli nie - dodaje)
        if "## 🛒 Produkty" in content:
             # Prosta podmiana sekcji nie jest trywialna regexem bez usuwania reszty, 
             # więc po prostu dodamy tabelę pod spodem starej lub stworzymy nową sekcję
             pass
        else:
            # Wstawiamy przed Oryginalny OCR
            insert_point = content.find("## 📜 Oryginalny OCR")
            if insert_point != -1:
                content = content[:insert_point] + f"## 🛒 Produkty\n{new_table}\n\n" + content[insert_point:]
        
        # Wstawienie JSONa z danymi strukturalnymi na koniec (lub aktualizacja)
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        json_block = f"\n## 🛠️ Dane Strukturalne (JSON)\n```json\n{json_str}\n```\n"
        
        # Dodajemy na koniec pliku
        content += json_block
        
        # Zmiana tagów i statusu
        content = content.replace("#to-verify", "#manual-verify")
        # Jeśli był status
        content = re.sub(r'status:.*', 'status: waiting-for-user', content)
        
        # Zapis
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return True

    def _markdown_table_from_items(self, items):
        md = "| Produkt | Ilość | Cena jedn. | Suma | Kategoria |\n|---|---|---|---|---|\n"
        for item in items:
            md += f"| {item.get('nazwa', '')} | {item.get('ilosc', '')} | {item.get('cena_jedn', '')} | {item.get('suma', '')} | {item.get('kategoria', '')} |\n"
        return md

if __name__ == "__main__":
    sanitizer = ReceiptSanitizer(ProjectConfig.PARAGONY_DIR)
    sanitizer.run_batch()
