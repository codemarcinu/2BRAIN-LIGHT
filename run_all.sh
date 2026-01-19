#!/bin/bash

# Przejdź do katalogu projektu (tam gdzie jest ten skrypt)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

if [ ! -f ".env" ]; then
    echo "❌ BŁĄD: Brak pliku .env w $DIR. Skopiuj .env.example i uzupełnij klucze!"
    exit 1
fi

# Zabij istniejące sesje jeśli istnieją
screen -S brainbot -X quit 2>/dev/null
screen -S brainwatcher -X quit 2>/dev/null

echo "🤖 Startuję Telegram Bot..."
screen -dmS brainbot bash -c "source venv/bin/activate && python bot.py"

echo "👀 Startuję Google Drive Watcher..."
screen -dmS brainwatcher bash -c "source venv/bin/activate && python watcher.py"

echo "✨ Usługi uruchomione w tle (screen)."
echo "Użyj 'screen -ls' aby zobaczyć procesy."
echo "Użyj 'screen -r brainbot' aby wejść do konsoli bota."
