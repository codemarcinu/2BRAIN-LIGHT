# 2brain_lite (Mobile First Pivot)

Lekki, mobilny asystent osobisty. Bez zbędnego zarządzania magazynem. Skupiony na szybkim przechwytywaniu (Capture) i automatycznej analizie.

## Filozofia

1.  **Mobile First**: Interakcja głównie przez **Telegrama**.
2.  **Zero Friction**: Zdjęcia paragonów i luźne notatki głosowe/tekstowe.
3.  **Automatyzacja**: `Watcher` sam pilnuje folderów Google Drive.
4.  **High Level Finance**: Zamiast detali - ogólne kategorie i sumy.

## Moduły

*   **Finanse (`finanse.py`)**: Analizuje zdjęcia paragonów przy użyciu Google Vision OCR i OpenAI (GPT-4o-mini). Zapisuje dane do bazy PostgreSQL.
*   **Wiedza (`wiedza.py`)**: Przetwarza pliki tekstowe/PDF na notatki Markdown z podsumowaniem AI i tagami.
*   **Spiżarnia (`pantry.py`)**: Zarządza zapasami jedzenia. Pozwala dodawać produkty głosowo i śledzić ich zużycie (Human Feedback).
*   **Watcher (`watcher.py`)**: Nasłuchuje zmian na dysku/folderach wejściowych i automatycznie wywołuje odpowiednie procesy.
*   **Bot (`bot.py`)**: Główny interfejs Telegram. Obsługuje zdjęcia, tekst i wiadomości głosowe.

## Instalacja

1.  Zainstaluj zależności:
    ```bash
    pip install -r requirements.txt
    ```
2.  Skonfiguruj `.env` (klucze API dla OpenAI, Telegrama i dane bazy PostgreSQL).
3.  Przygotuj `google_key.json` (Service Account) dla Google Vision OCR.

## Uruchomienie

### 1. Tryb Wszystko-w-jednym (Voice Brain)
Najprostszy sposób na start:
```bash
./start_voice_brain.sh
```
Uruchamia Watchera oraz Bota Telegrama w jednej sesji.

### 2. CLI (Narzędzia administratorskie)
```bash
python cli.py
```

## Dokumentacja

👉 **[INSTRUKCJA CLI](docs/CLI_MANUAL.md)**
👉 **[PRZETWARZANIE PARAGONÓW](docs/RECEIPT_PIPELINE.md)**
👉 **[PRZEWODNIK WDROŻENIA](docs/DEPLOYMENT_GUIDE.md)**
