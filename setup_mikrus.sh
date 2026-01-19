#!/bin/bash

echo "🚀 Rozpoczynam konfigurację 2Brain Lite na Mikr.us..."

# 1. Instalacja zależności systemowych
echo "📦 Instaluję zależności systemowe..."
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip poppler-utils ffmpeg screen

# 2. Tworzenie wirtualnego środowiska
echo "🐍 Tworzę venv..."
python3 -m venv venv
source venv/bin/activate

# 3. Instalacja bibliotek Python
echo "📚 Instaluję wymagania..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Tworzenie struktury katalogów
echo "📁 Tworzę strukturę katalogów..."
mkdir -p inputs/paragony
mkdir -p inputs/inbox
mkdir -p archive
mkdir -p data/vault

# 5. Sprawdzenie plików kluczy
echo "🔑 Sprawdzam klucze..."
if [ ! -f "google_key.json" ]; then
    echo "⚠️  OSTRZEŻENIE: Brak pliku google_key.json"
fi

if [ ! -f ".env" ]; then
    echo "📝 INFO: Tworzę plik .env z szablonu. Uzupełnij go przed startem!"
    cp .env.example .env
fi

echo "✅ Konfiguracja zakończona."
echo "Użyj './run_all.sh' aby uruchomić usługi w sesjach screen."
