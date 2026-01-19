import os
import io
import time
import json
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import wiedza
from dotenv import load_dotenv

# Konfiguracja
load_dotenv()
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
DRIVE_FOLDER_ID = "1SzA0IQuKIvVF2lpUMwH00vpPQXD2PK0P"
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
HISTORY_FILE = "history.json"
INPUT_DIR = "./inputs/inbox"
SCAN_INTERVAL = 60  # Co ile sekund sprawdzać

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def authenticate():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            try:
                # Na lokalnej maszynie spróbuj standardowo
                creds = flow.run_local_server(port=0)
            except Exception:
                # Na serwerze (Headless)
                print("⚠️ Nie można uruchomić serwera lokalnego. Przełączam na tryb konsolowy.")
                creds = flow.run_console()
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
    return build('drive', 'v3', credentials=creds)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_history(history_set):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(list(history_set), f)

def download_file(service, file_id, file_name):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    
    # Save locally
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
        
    safe_name = os.path.basename(file_name)
    local_path = os.path.join(INPUT_DIR, safe_name)
    with open(local_path, "wb") as f:
        f.write(fh.getbuffer())
    return local_path

def main():
    try:
        service = authenticate()
        logging.info("✅ Polaczenie z Google Drive aktywne!")
    except Exception as e:
        logging.error(f"❌ Blad autoryzacji: {e}")
        return

    history = load_history()
    
    logging.info(f"👀 Obserwuje folder ID: {DRIVE_FOLDER_ID}")
    
    while True:
        try:
            # List files in folder
            query = f"'{DRIVE_FOLDER_ID}' in parents and trashed = false"
            results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
            items = results.get('files', [])

            new_files = [f for f in items if f['id'] not in history]
            
            if new_files:
                logging.info(f"⚡ Wykryto {len(new_files)} nowych plikow.")
                
                for file in new_files:
                    try:
                        file_id = file['id']
                        file_name = file['name']
                        
                        logging.info(f"📥 Pobieram: {file_name}")
                        local_path = download_file(service, file_id, file_name)
                        
                        # Process if it's a text file or just generally supported
                        # Wiedza processes .txt mostly, maybe expand later
                        if file_name.endswith('.txt') or file_name.endswith('.md'):
                            logging.info(f"🧠 Przetwarzam wiedze: {file_name}")
                            wiedza.process_note(local_path)
                            # Wiedza moves to archive, so file is gone from Inbox
                        else:
                            logging.warning(f"⚠️ Nieznany format dla wiedzy: {file_name} (Zapisano w Inbox)")
                        
                        history.add(file_id)
                        save_history(history)
                        
                    except Exception as e:
                        logging.error(f"❌ Blad przy pliku {file['name']}: {e}")
            
        except Exception as e:
            logging.error(f"❌ Blad petli glownej: {e}")
            
        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
