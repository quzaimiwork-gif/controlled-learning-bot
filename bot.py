import os
import time
import telebot
from google import genai
from dotenv import load_dotenv

# 1. LOAD CONFIGURATION
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# Inisialisasi Bot dengan threaded=False untuk mengelakkan ralat 409 di Railway
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, threaded=False)

# Inisialisasi Gemini Client (API v1 Stable)
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options={'api_version': 'v1'}
)

# 2. LOAD KNOWLEDGE BASE
try:
    if os.path.exists("knowledge_base.txt"):
        with open("knowledge_base.txt", "r", encoding="utf-8") as file:
            training_data = file.read()
    else:
        training_data = "Maklumat SME tidak ditemui."
except Exception as e:
    print(f"Error loading knowledge base: {e}")
    training_data = "Data tidak tersedia."

# 3. MESSAGE HANDLER
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    # Papar status 'typing' di Telegram
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # Gunakan Gemini 3.1 Flash untuk kepantasan dan kebijaksanaan
        # Kita gabungkan arahan sistem terus ke dalam prompt untuk kestabilan payload
        prompt_gabungan = (
            f"ARAHAN SISTEM: Anda adalah pakar SME. Gunakan data ini sahaja: {training_data}. "
            f"Jika soalan tiada kaitan dengan data, balas: TRIGGER_FALLBACK.\n\n"
            f"SOALAN PENGGUNA: {message.text}"
        )
        
        response = client.models.generate_content(
            model="gemini-3.1-flash", 
            contents=prompt_gabungan
        )
        
        ai_text = response.text.strip()

        # Logik Fallback (Jika AI tak tahu jawapan)
        if "TRIGGER_FALLBACK" in ai_text:
            bot.reply_to(message, "Maaf, maklumat itu tiada dalam simpanan saya. Saya akan maklumkan kepada pakar kami untuk membantu anda segera.")
            if ADMIN_CHAT_ID:
                alert = f"🚨 **SOALAN BARU (Perlu Bantuan)**\nUser ID: `{message.chat.id}`\nSoalan: {message.text}"
                bot.send_message(ADMIN_CHAT_ID, alert)
        else:
            bot.reply_to(message, ai_text)

    except Exception as e:
        error_msg = str(e)
        print(f"
