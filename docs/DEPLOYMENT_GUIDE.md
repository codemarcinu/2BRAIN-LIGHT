# Przewodnik Wdrożenia (Manual Deployment)

Ten dokument opisuje krok po kroku jak postawić `2brain_lite` od zera.

## Krok 1: Klonowanie i Środowisko
1. Pobierz repozytorium.
2. Stwórz wirtualne środowisko:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/WSL
   # lub
   .\venv\Scripts\activate  # Windows
   ```
3. Zainstaluj biblioteki:
   ```bash
   pip install -r requirements.txt
   ```

## Krok 2: Pozyskanie Kluczy API
1. **OpenAI**: Załóż konto na platformie OpenAI, wygeneruj API KEY i doładuj środki.
2. **Telegram**: Napisz do `@BotFather` na Telegramie, stwórz nowego bota i odbierz TOKEN.
3. **Google Cloud**: 
   - Stwórz projekt w Google Cloud Console.
   - Włącz "Cloud Vision API".
   - Stwórz "Service Account", pobierz klucz w formacie JSON i nazwij go `google_key.json` w głównym folderze projektu.

## Krok 3: Konfiguracja .env
Skopiuj przykład poniżej do pliku `.env`:
```env
# AI & Telegram
OPENAI_API_KEY="sk-..."
TELEGRAM_TOKEN="123456789:ABCDEF..."
ALLOWED_USER_ID="Twoje_ID_Telegram"

# Database (PostgreSQL)
DB_HOST="psql01.mikr.us"
DB_NAME="db_xxx"
DB_USER="user_xxx"
DB_PASS="haslo"
DB_PORT="5432"

# Paths
VAULT_PATH="./data/vault"
```

## Krok 4: Inicjalizacja Bazy Danych
Uruchom skrypt, który stworzy tabelę `receipts` oraz `pantry`:
```bash
python db_setup.py
```

## Krok 5: Uruchomienie
Uruchom aplikację za pomocą skryptu startowego:
```bash
chmod +x start_voice_brain.sh
./start_voice_brain.sh
```

## Jak testować?
1. Wyślij do bota na Telegramie zdjęcie paragonu -> Powinieneś dostać potwierdzenie zapisu.
2. Wyślij wiadomość głosową: "Kupiłem mleko i jajka" -> Powinny zostać dodane do spiżarni.
3. Napisz: "Zjadłem jajka" -> Bot powinien zaktualizować status w bazie danych.
