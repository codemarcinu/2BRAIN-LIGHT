import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv
from openai import OpenAI
import finanse
import wiedza
import finanse
import wiedza
# import pantry (Removed)


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
    user_id = update.effective_user.id
    if ALLOWED_USER_ID == 0:
        logging.warning(f"⚠️ TELEGRAM_ALLOWED_USER_ID is not set (default 0). Blocking access for {user_id}")
        await update.message.reply_text("⛔ Bot nie jest skonfigurowany (Brak ALLOWED_USER_ID).")
        return False
        
    if user_id != ALLOWED_USER_ID:
        logging.warning(f"⛔ Nieautoryzowany dostęp: ID={user_id}, Username={update.effective_user.username}")
        await update.message.reply_text(f"⛔ Brak dostępu. Twój ID: {user_id}")
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
        
        # 2. Logic: Expense vs Note
        user_text_lower = text.lower()
        if "kupiłem" in user_text_lower or "wydałem" in user_text_lower:
             # Process as Expense
             await status_msg.edit_text("💸 Przetwarzam jako wydatek...")
             loop = asyncio.get_running_loop()
             result_msg = await loop.run_in_executor(None, finanse.process_expense_text, text)
             await update.message.reply_text(result_msg)
        else:
             # Process as Note/Knowledge
             await status_msg.edit_text("📝 Przetwarzam jako notatkę...")
             filename = f"voice_note_{update.message.id}.txt"
             txt_path = f"./inputs/inbox/{filename}"
             if not os.path.exists("./inputs/inbox"): os.makedirs("./inputs/inbox")
             
             with open(txt_path, "w", encoding="utf-8") as f:
                 f.write(text)
             
             loop = asyncio.get_running_loop()
             await loop.run_in_executor(None, wiedza.process_note, txt_path)
             
             import shutil
             if not os.path.exists("./archive"): os.makedirs("./archive")
             shutil.move(txt_path, f"./archive/{filename}")
             
             await update.message.reply_text("✅ Notatka zapisana w bazie wiedzy!")

    except Exception as e:
        await update.message.reply_text(f"❌ Błąd: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return

    photo_file = await update.message.photo[-1].get_file()
    filename = f"tele_{update.message.id}.jpg"
    file_path = f"./inputs/{filename}"
    
    if not os.path.exists("./inputs"): os.makedirs("./inputs")
    await photo_file.download_to_drive(file_path)
    
    keyboard = [
        [
            InlineKeyboardButton("💰 Paragon", callback_data=f"p:{filename}"),
            InlineKeyboardButton("🧠 Wiedza", callback_data=f"w:{filename}"),
        ],
        [InlineKeyboardButton("❌ Anuluj", callback_data=f"c:{filename}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🖼️ Co chcesz zrobić z tym obrazem?", reply_markup=reply_markup)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if ":" not in data: return
    action, filename = data.split(":", 1)
    temp_path = f"./inputs/{filename}"
    
    if not os.path.exists(temp_path):
        await query.edit_message_text("❌ Plik już nie istnieje lub został przetworzony.")
        return

    import shutil

    if action == "p": # PARAGON
        await query.edit_message_text("⏳ Analizuję paragon...")
        final_path = f"./inputs/paragony/{filename}"
        if not os.path.exists("./inputs/paragony"): os.makedirs("./inputs/paragony")
        shutil.move(temp_path, final_path)
        
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, finanse.process_receipt_image, final_path, True)
            await query.message.reply_text(result)
        except Exception as e:
            await query.message.reply_text(f"❌ Błąd finansów: {e}")
            
    elif action == "w": # WIEDZA
        await query.edit_message_text("🧠 Przetwarzam jako wiedzę (OCR)...")
        try:
            # Wykonujemy OCR na obrazku, żeby mieć tekst do notatki
            loop = asyncio.get_running_loop()
            text = await loop.run_in_executor(None, finanse.get_text_from_file, temp_path)
            
            if not text:
                await query.message.reply_text("⚠️ OCR nie wykrył tekstu na obrazku.")
                if os.path.exists(temp_path): os.remove(temp_path)
                return

            # Tworzymy tymczasowy plik tekstowy dla modułu wiedza
            txt_filename = filename.replace(".jpg", ".txt")
            txt_path = f"./inputs/inbox/{txt_filename}"
            if not os.path.exists("./inputs/inbox"): os.makedirs("./inputs/inbox")
            
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
            
            # Przetwarzamy jako notatkę
            await loop.run_in_executor(None, wiedza.process_note, txt_path)
            
            if not os.path.exists("./archive"): os.makedirs("./archive")
            shutil.move(txt_path, f"./archive/{txt_filename}")
            
            # Usuwamy oryginalny obrazek tymczasowy
            if os.path.exists(temp_path): os.remove(temp_path)
            
            await query.message.reply_text("✅ Tekst z obrazka dodany do bazy wiedzy!")
        except Exception as e:
            await query.message.reply_text(f"❌ Błąd wiedzy: {e}")
            
    elif action == "c": # CANCEL
        if os.path.exists(temp_path): os.remove(temp_path)
        await query.edit_message_text("❌ Anulowano.")

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
    safe_filename = os.path.basename(doc.file_name)
    file = await doc.get_file()
    path = f"./inputs/inbox/{safe_filename}"
    
    await file.download_to_drive(path)
    await update.message.reply_text(f"📥 Pobrałem {safe_filename}.")
    
    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, wiedza.process_note, path)
        
        import shutil
        shutil.move(path, f"./archive/{safe_filename}")
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
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    print("🤖 Bot (Voice Brain) wystartował!")
    application.run_polling()
