#!/bin/bash
echo "🚀 Uruchamiam 2Brain Lite (Voice Brain)..."

# Sprawdź czy .env istnieje
if [ ! -f .env ]; then
    echo "❌ BŁĄD: Brak pliku .env! Skopiuj .env.example i wpisz klucze."
    read -p "Naciśnij ENTER aby wyjść..."
    exit 1
fi


# Aktywacja wirtualnego srodowiska
source venv/bin/activate

# Uruchom Watchera w tle
echo "👀 Uruchamiam Watchera (Google Drive)..."
python watcher.py > watcher.log 2>&1 &
WATCHER_PID=$!
echo "✅ Watcher działa w tle (PID: $WATCHER_PID). Logi w watcher.log"

# Uruchom Bota
echo "🤖 Uruchamiam Bota Telegram..."
python bot.py

# Po zamknięciu bota, zabij watchera
echo "🛑 Zatrzymuję Watchera..."
kill $WATCHER_PID
