#!/bin/bash

# Nazwa pliku logów
LOG_FILE="app.log"

echo "🚀 Inicjalizacja 2Brain Lite Dashboard..."

# 1. Sprawdzenie .env
if [ ! -f ../.env ] && [ ! -f .env ]; then
    echo "❌ BŁĄD: Brak pliku .env!"
    exit 1
fi

# 2. Aktywacja VENV
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️ Brak venv! Tworzę..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Zawsze sprawdzamy zależności (szybkie, jeśli już są)
pip install -r requirements.txt

# 3. Uruchamianie procesów w tle
echo "🔄 Uruchamianie procesów tła..."

# Czyścimy stary log
echo "--- NOWA SESJA: $(date) ---" > $LOG_FILE

# Uruchamiamy Watchera
nohup python watcher.py >> $LOG_FILE 2>&1 &
WATCHER_PID=$!
echo "✅ Watcher PID: $WATCHER_PID"

# Uruchamiamy Bota
nohup python bot.py >> $LOG_FILE 2>&1 &
BOT_PID=$!
echo "✅ Bot PID: $BOT_PID"

# 4. Otwarcie okna z logami (Windows/WSL specyficzne)
# Używamy cmd.exe aby odpalić nowe okno, a w nim wsl tail, co jest bardziej niezawodne niż powershell na zasobach sieciowych
echo "📺 Otwieram okno logów..."
# Ścieżka wewnątrz WSL
WSL_LOG_PATH="$PWD/$LOG_FILE"
cmd.exe /c start cmd.exe /k "title 2Brain LOGS & echo ⏳ Podpinanie pod logi... & wsl tail -f $WSL_LOG_PATH" 2>/dev/null &

# 5. Uruchomienie CLI
echo "⌨️ Uruchamiam interfejs CLI..."
python cli.py

# 6. Sprzątanie po wyjściu z CLI
echo "🛑 Zamykanie systemu..."
kill $WATCHER_PID 2>/dev/null
kill $BOT_PID 2>/dev/null

echo "👋 Pa pa!"
