import os
import time
import telebot
from google import genai
from dotenv import load_dotenv

# 1. SETUP
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Guna v1 untuk elak 404 pada akaun Billing
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options={'api_version': 'v1'}
)

# 2. DATA
try:
    if os.path.exists("knowledge_base.txt"):
        with open("knowledge_base.txt", "r", encoding="utf-8") as file:
            training_data = file.read()
    else:
        training_data = "Data SME belum tersedia."
except:
    training_data = "Ralat data."

# 3. MESEJ HANDLER
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        # Teknik prompt gabungan (Paling selamat untuk Billing Tier 1)
        system_msg = f"Anda pakar SME. Rujuk data ini: {training_data}. Jika tiada, balas: TRIGGER_FALLBACK."
        full_prompt = f"ARAHAN: {system_msg}\n\nUSER: {message.text}"
        
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=full_prompt
        )
        bot.reply_to(message, response.text.strip().replace("TRIGGER_FALLBACK", "Maaf, saya perlu semak dengan pakar kami."))
    except Exception as e:
        print(f"Gemini Error: {e}")
        bot.reply_to(message, "Sistem sibuk. Sila cuba lagi.")

# 4. STARTUP (CLEAN START)
if __name__ == "__main__":
    print("--- MEMBERSIHKAN WEBHOOK OLD PROCESS ---")
    try:
        bot.remove_webhook()
        # Paksa Telegram lupakan bot lama
        bot.get_updates(offset=-1)
        time.sleep(5) 
    except:
        pass

    print("Bot is LIVE dengan Token Baru!")
    # Guna polling biasa, tanpa infinity untuk elak 409 berulang
    bot.polling(none_stop=True, skip_pending=True)
