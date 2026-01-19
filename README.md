# 2brain_lite (Mobile First Pivot)

Lekki, mobilny asystent osobisty. Bez zbędnego zarządzania magazynem. Skupiony na szybkim przechwytywaniu (Capture) i automatycznej analizie.

## Filozofia

1.  **Mobile First**: Interakcja głównie przez **Telegrama**.
2.  **Zero Friction**: Zdjęcia paragonów i luźne notatki głosowe/tekstowe.
3.  **Automatyzacja**: `Watcher` sam pilnuje folderów Google Drive.
4.  **High Level Finance**: Zamiast detali - ogólne kategorie i sumy.

## Moduły

*   **Finanse (`finanse.py`)**: Analizuje zdjęcia paragonów. Zapisuje sumę, sklep i kategorię do bazy SQL.
*   **Wiedza (`wiedza.py`)**: Przetwarza luźne pliki tekstowe na notatki Markdown (Obsidian) z tagami AI.
*   **Watcher (`watcher.py`)**: Nasłuchuje zmian na Google Drive i automatycznie zleca zadania.
*   **Bot (`bot.py`)**: Interfejs użytkownika. Wysyłasz zdjęcie -> Finanse. Wysyłasz tekst -> Wiedza.

## Instalacja

1.  Zainstaluj zależności:
    ```bash
    pip install -r requirements.txt
    ```
2.  Skonfiguruj `.env` (klucze API, ID folderu Drive, Token Telegrama).
3.  Upewnij się, że masz `google_key.json` (Service Account) i `credentials.json` (User OAuth).

## Uruchomienie

### 1. Watcher (W tle)
```bash
python watcher.py
```
Skanuje Google Drive co minutę.

### 2. Telegram Bot
```bash
python bot.py
```
Twój główny interfejs.

## Dokumentacja

👉 **[PODRECZNIK WDROŻENIA (Krok po Kroku)](docs_PODRECZNIK_WDROZENIA.md)** - Instrukcja dla osób nietechnicznych.
