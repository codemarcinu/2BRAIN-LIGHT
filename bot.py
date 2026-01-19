import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
from openai import OpenAI
import finanse
import wiedza
import pantry

# Konfiguracja
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
try:
    ALLOWED_USER_ID = int(os.getenv("TELEGRAM_ALLOWED_USER_ID", "0"))
except ValueError:
    ALLOWED_USER_ID = 0

OPENAI_CLIENT = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def check_auth(update: Update):
    if update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text(f"⛔ Brak dostępu. Twój ID: {update.effective_user.id}")
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Cześć! Jestem Twoim Asystentem 2Brain Lite (Voice Edition).\n"
        "🎤 Mów do mnie -> Zarządzaj spiżarnią/zakupami.\n"
        "📸 Wyślij zdjęcie -> Finanse.\n"
        "📝 Wyślij tekst/plik -> Wiedza."
    )

async def transcribe_audio(file_path):
    """Whisper API"""
    with open(file_path, "rb") as audio_file:
        transcription = OPENAI_CLIENT.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file,
            language="pl"
        )
    return transcription.text

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return

    user = update.message.from_user
    status_msg = await update.message.reply_text("🎤 Słucham...")

    voice_file = await update.message.voice.get_file()
    file_path = f"voice_{user.id}.ogg"
    await voice_file.download_to_drive(file_path)

    try:
        # 1. Transkrypcja
        text = await transcribe_audio(file_path)
        await status_msg.edit_text(f"🗣️ \"{text}\"")
        
        # 2. Logika Pantry (Router)
        # Pobieramy stan lodówki jako kontekst dla mądrzejszej decyzji
        all_items = pantry.get_all_stock()
        candidates = [{"name": item} for item in all_items]
        
        # Próbujemy najpierw sprawdzić, czy to nie jest komenda sprzątania/zużycia
        stats = pantry.process_human_feedback(candidates, text)
        
        response_msg = ""
        # Jeśli wykryto jakieś akcje na istniejących produktach
        if stats and sum(stats.values()) > 0:
            response_msg += (
                f"✅ Zaktualizowano:\n"
                f"😋 Zjedzone: {stats['consumed']}\n"
                f"🗑️ Wyrzucone: {stats['trashed']}\n"
                f"📅 Przedłużone: {stats['extended']}\n"
            )
        
        # Jeśli nic nie usunięto, albo tekst brzmi jak zakupy ("Kupiłem...")
        # To próbujemy dodać nowe produkty.
        # Sprytny hack: jeśli 'process_human_feedback' nic nie zrobił, to na 99% są to zakupy.
        if not stats or sum(stats.values()) == 0:
            added = pantry.add_items_from_text(text)
            if added > 0:
                response_msg += f"🛒 Dodano {added} nowych produktów."
            elif not response_msg:
                response_msg = "🤔 Nie zrozumiałem intencji (ani sprzątanie, ani zakupy)."

        await update.message.reply_text(response_msg)

    except Exception as e:
        await update.message.reply_text(f"❌ Błąd: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return

    photo_file = await update.message.photo[-1].get_file()
    file_path = f"./inputs/paragony/telegram_{update.message.id}.jpg"
    
    await photo_file.download_to_drive(file_path)
    await update.message.reply_text("⏳ Analizuję paragon...")
    
    try:
        # Wrapper to run sync function in threadpool
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, finanse.process_receipt_image, file_path, True)
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"❌ Błąd: {e}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return

    text = update.message.text
    filename = f"note_telegram_{update.message.id}.txt"
    path = f"./inputs/inbox/{filename}"
    
    if not os.path.exists("./inputs/inbox"): os.makedirs("./inputs/inbox")

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    
    await update.message.reply_text("📝 Notatka zapisana. Przetwarzam...")
    
    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, wiedza.process_note, path)
        
        import shutil
        shutil.move(path, f"./archive/{filename}")
        await update.message.reply_text("✅ Notatka w Obsidiana!")
    except Exception as e:
        await update.message.reply_text(f"❌ Błąd wiedzy: {e}")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    
    doc = update.message.document
    file = await doc.get_file()
    path = f"./inputs/inbox/{doc.file_name}"
    
    await file.download_to_drive(path)
    await update.message.reply_text(f"📥 Pobrałem {doc.file_name}.")
    
    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, wiedza.process_note, path)
        
        import shutil
        shutil.move(path, f"./archive/{doc.file_name}")
        await update.message.reply_text("✅ Dodano do bazy wiedzy.")
    except Exception as e:
        await update.message.reply_text(f"❌ Błąd: {e}")

if __name__ == '__main__':
    if not TELEGRAM_TOKEN:
        print("❌ Brak TELEGRAM_TOKEN w .env")
        exit(1)
        
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    print("🤖 Bot (Voice Brain) wystartował!")
    application.run_polling()
