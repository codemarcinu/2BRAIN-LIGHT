# 0. Bezpieczeństwo - Sprawdzenie roota
if [ "$EUID" -eq 0 ]; then
  echo "❌ BŁĄD: Nie uruchamiaj tego skryptu jako root!"
  echo "Zalecane: Utwórz dedykowanego użytkownika, np. 'sudo adduser brainbot'"
  exit 1
fi

echo "🚀 Rozpoczynam konfigurację 2Brain Lite..."

# 1. Instalacja zależności systemowych
echo "📦 Instaluję zależności systemowe..."
# Tylko te komendy wymagają sudo
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip poppler-utils ffmpeg screen logrotate

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

# 6. Konfiguracja Logrotate (opcjonalnie, wymaga sudo)
echo "📝 Konfiguruję rotację logów..."
if [ -f "config/logrotate.conf" ]; then
    # Podmiana ścieżki na aktualną w pliku konfiguracyjnym
    sed "s|__PROJECT_PATH__|$(pwd)|g" config/logrotate.conf > /tmp/2brain_logrotate
    sudo cp /tmp/2brain_logrotate /etc/logrotate.d/2brain_lite
    sudo chmod 644 /etc/logrotate.d/2brain_lite
    rm /tmp/2brain_logrotate
fi

echo "✅ Konfiguracja zakończona."
echo "Użyj './run_all.sh' aby uruchomić usługi w sesjach screen."
