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

## Architektura (Cloud Edition)
Projekt zoptymalizowany pod serwery o ograniczonych zasobach (np. **Mikr.us**):
- **Logic**: OpenAI GPT-4o-mini (bardzo niskie zużycie RAM).
- **OCR**: Google Vision API (Cloud).
- **Audio**: OpenAI Whisper (Cloud).
- **Baza**: PostgreSQL (Mikr.us psql01).
- **Zasoby**: Wymaga < 1GB RAM.

## Serwer Mikr.us (Wdrożenie)

1. **Połącz się przez SSH**: `ssh root@joanna114.mikrus.xyz -p10114`
2. **Uruchom skrypt konfiguracji**:
   ```bash
   chmod +x setup_mikrus.sh run_all.sh
   ./setup_mikrus.sh
   ```
3. **Konfiguracja**: Uzupełnij `.env` oraz wgraj `google_key.json` i `credentials.json`.
4. **Uruchomienie**: `./run_all.sh`

## Zarządzanie
- Lista usług: `screen -ls`
- Konsola bota: `screen -r brainbot` (Wyjście: `Ctrl+A, D`)
- CLI Admin: `python cli.py`
