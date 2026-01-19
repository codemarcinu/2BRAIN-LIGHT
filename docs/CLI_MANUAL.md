# 2brain_lite CLI Manual

Witaj w instrukcji **Hacker Terminal** dla `2brain_lite`. Jest to centrum dowodzenia do zarządzania finansami i wiedzą, wykorzystujące chmurowe AI oraz bazy danych.

## 🚀 Instalacja i Konfiguracja

1.  **Wymagania**:
    *   Python 3.10+
    *   Baza danych PostgreSQL (np. na Mikr.us)
    *   Klucz Google Cloud Vision API (JSON)
    *   Klucz OpenAI API

2.  **Zależności**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Zmienne Środowiskowe (.env)**:
    Upewnij się, że plik `.env` zawiera:
    *   `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS`, `DB_PORT`
    *   `OPENAI_API_KEY`
    *   `TELEGRAM_TOKEN`
    *   `ALLOWED_USER_ID` (twój ID na Telegramie)

## 🎮 Instrukcja Użycia

Uruchom CLI:
```bash
python cli.py
```

Nawigacja odbywa się za pomocą **Strzałek** i klawisza **Enter**.

### 💰 Moduł: Przetwórz Paragony (Finance)
*   **Wejście**: Umieść zdjęcia (`.jpg`, `.png`) w folderze `inputs/paragony`.
*   **Akcja**: Wybierz "💰 Przetwórz Paragony".
*   **Proces**:
    1.  **OCR**: Google Vision wyciąga surowy tekst ze zdjęcia.
    2.  **AI Parsing**: OpenAI (GPT-4o-mini) zamienia tekst na ustrukturyzowany JSON.
    3.  **Zapis**: Dane trafiają do bazy PostgreSQL.
    4.  **Archiwizacja**: Oryginalne zdjęcie trafia do `archive/`.

### 🧠 Moduł: Przetwórz Inbox (Knowledge)
*   **Wejście**: Umieść pliki tekstowe (`.txt`) lub PDF w `inputs/inbox`.
*   **Akcja**: Wybierz "🧠 Przetwórz Inbox".
*   **Proces**:
    1.  **AI Analysis**: OpenAI tworzy podsumowanie, wnioski i tagi.
    2.  **Markdown**: Generuje plik `.md` w folderze Obsidian (np. `./data/vault`).
    3.  **Archiwizacja**: Pliki źródłowe trafiają do `archive/`.

### 📊 Moduł: Raport Finansowy
*   **Akcja**: Wybierz "📊 Raport Finansowy".
*   **Proces**: Pobiera ostatnie 5 transakcji bezpośrednio z bazy danych i wyświetla je w czytelnej tabeli.

### ⚙️ Moduł: Status Systemu
*   **Akcja**: Wybierz "⚙️ Status Systemu".
*   **Proces**: Sprawdza, czy procesy Bota i Watchera działają w tle (na podstawie PID).

## 🔧 Rozwiązywanie problemów

*   **Błąd Bazy Danych**: Sprawdź połączenie z internetem oraz czy dane w `.env` są poprawne (Mikr.us wymaga czasem odświeżenia połączenia).
*   **Błąd AI**: Upewnij się, że klucz `OPENAI_API_KEY` jest aktywny i masz środki na koncie.
*   **Google Vision Error**: Sprawdź czy plik `google_key.json` (lub path w env) jest poprawny.
