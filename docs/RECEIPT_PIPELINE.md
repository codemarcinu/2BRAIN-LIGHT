# Receipt Processing (Lite)

System do automatycznego przetwarzania paragonów w wersji "Lite". Skoncentrowany na szybkości i integracji z bazą danych PostgreSQL.

## Przepływ pracy (Pipeline)

1.  **Obraz**: Użytkownik przesyła zdjęcie (przez Telegram lub wrzuca do `inputs/paragony`).
2.  **OCR (Vision API)**: System wysyła obraz do Google Cloud Vision. Uzyskuje pełny tekst paragonu.
3.  **Parsowanie AI (OpenAI)**: 
    *   Prompt systemowy (`prompts.py`) instruuje model GPT-4o-mini, jak wyciągnąć kluczowe dane.
    *   Wyciągane pola: `shop` (sklep), `total` (kwota), `date` (data), `category` (lista zakupów / kategoria główna).
    *   Wymuszany format: JSON.
4.  **Baza Danych**: Wyniki są zapisywane w tabeli `receipts` w PostgreSQL.
5.  **Archiwizacja**: Przetworzony plik obrazu jest przenoszony do folderu `archive/` z dodanym znacznikiem czasu.

## Kluczowe Pliki

*   `finanse.py`: Główny moduł procesujący.
*   `prompts.py`: Zawiera prompt `RECEIPT_SUMMARY_SYSTEM`.
*   `db_setup.py`: Skrypt do inicjalizacji tabel w Postgresie.

## Konfiguracja .env

Wymagane zmienne dla tego modułu:
```env
# Google Vision
GOOGLE_APPLICATION_CREDENTIALS="path/to/google_key.json"

# OpenAI
OPENAI_API_KEY="sk-..."

# Database
DB_HOST="psql01.mikr.us"
DB_NAME="db_name"
DB_USER="user"
DB_PASS="password"
```

## Obsługiwane Typy Danych

Aplikacja dąży do uproszczenia finansów, dlatego zapisuje główne kategorie oraz sumy. Szczegółowe pozycje z paragonu są zapisywane jako tekst surowy (`raw_text`) w bazie, aby umożliwić późniejszą analizę, jeśli będzie potrzebna.
