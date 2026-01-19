# Receipt Processing Pipeline

System do inteligentnego przetwarzania paragonów, łączący tradycyjne metody (Cache, Fuzzy Matching) z modelami językowymi (LLM).

## Architektura

System zorganizowany jest w architekturę potokową (Pipeline):

1.  **Input**: Tekst OCR z pliku Markdown (sekcja `## 📜 Oryginalny OCR`).
2.  **Preprocessing**: Wykrycie sklepu (`detect_shop`) i czyszczenie tekstu przez dedykowanego agenta (np. `BiedronkaAgent`).
3.  **Cache Lookup**: Sprawdzenie czy linia z paragonu była już wcześniej rozpoznana.
4.  **Fuzzy Matching**: Dla nieznanych linii, próba dopasowania do bazy znanych produktów (`product_taxonomy.json`) używając biblioteki `rapidfuzz`.
5.  **AI Fallback** (Opcjonalne): Jeśli pokrycie rozpoznanych produktów jest niskie (<30%), wysyłane jest zapytanie do LLM (Gemini/Ollama) o strukturyzację danych.
6.  **Normalization**: Ujednolicenie nazw i kategorii (np. "MASLO EX" -> "Masło Ekstra" [NABIAŁ]).
7.  **Output**: Aktualizacja pliku Markdown o tabelę produktów i blok JSON.

## Struktura Katalogów

*   `core/pipelines/` - Główna logika potoku (`AsyncReceiptPipeline`).
*   `core/tools/` - Narzędzia uruchomieniowe (`receipt_cleaner.py`).
*   `utils/` - Biblioteki pomocnicze:
    *   `receipt_cache.py`: Obsługa pamięci podręcznej.
    *   `taxonomy.py`: Obsługa bazy produktów i wzorców.
    *   `receipt_agents/`: Fabryka agentów dla poszczególnych sieci sklepów.
*   `adapters/` - Adaptery do zewnętrznych API (Google Gemini, Ollama).
*   `config/` - Pliki konfiguracyjne i dane statyczne (`product_taxonomy.json`).

## Konfiguracja

Plik konfiguracyjny: `config.py`

*   `RECEIPT_AI_PROVIDER`: `google` lub `ollama`.
*   `GOOGLE_API_KEY`: Klucz API do Gemini (wymagany jeśli provider to google).
*   `PRODUCT_TAXONOMY_PATH`: Ścieżka do pliku JSON z taksonomią.

## Użycie

Aby przetworzyć paragony oznaczone tagiem `#to-verify` w katalogu `inputs/paragony`:

```bash
python core/tools/receipt_cleaner.py
```

## Rozszerzanie Taksonomii

Aby dodać nowe produkty, edytuj `config/product_taxonomy.json`:

```json
{ 
  "ocr": "NAZWA Z PARAGONU", 
  "name": "Pełna Nazwa Produktu", 
  "cat": "KATEGORIA", 
  "unit": "szt" 
}
```

Klucz `ocr` powinien być pisany wielkimi literami (UPPERCASE).
