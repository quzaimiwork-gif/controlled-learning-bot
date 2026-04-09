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

# Inisialisasi Bot dengan threaded=False (Wajib untuk Railway)
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
    training_data = "Data tidak tersedia."

# 3. MESSAGE HANDLER
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # Gunakan Gemini 3.1 Flash
        prompt_gabungan = (
            f"ARAHAN SISTEM: Anda adalah pakar SME Malaysia. Gunakan data ini sahaja: {training_data}. "
            f"Jika soalan tiada kaitan dengan data, balas: TRIGGER_FALLBACK.\n\n"
            f"SOALAN PENGGUNA: {message.text}"
        )
        
        response = client.models.generate_content(
            model="gemini-3.1-flash", 
            contents=prompt_gabungan
        )
        
        ai_text = response.text.strip()

        if "TRIGGER_FALLBACK" in ai_text:
            bot.reply_to(message, "Maaf, maklumat itu tiada dalam simpanan saya. Saya akan hubungkan anda dengan pakar kami.")
            if ADMIN_CHAT_ID:
                alert = f"🚨 SOALAN BARU\nUser ID: `{message.chat.id}`\nSoalan: {message.text}"
                bot.send_message(ADMIN_CHAT_ID, alert)
        else:
            bot.reply_to(message, ai_text)

    except Exception as e:
        print(f"Ralat Gemini: {e}")
        bot.reply_to(message, "Maaf, sistem sedang sibuk. Sila cuba sebentar lagi.")

# 4. ADMIN REPLY LOGIC
@bot.message_handler(func=lambda message: message.reply_to_message and str(message.chat.id) == str(ADMIN_CHAT_ID))
def admin_reply_to_user(message):
    try:
        original_text = message.reply_to_message.text
        target_user_id = original_text.split("User ID: `")[1].split("`")[0]
        bot.send_message(target_user_id, f"👨‍🏫 **Jawapan Pakar:**\n\n{message.text}")
        bot.reply_to(message, "✅ Berjaya dihantar.")
    except Exception:
        bot.reply_to(message, "Ralat: Pastikan anda reply pada alert.")

# 5. SAFE STARTUP
if __name__ == "__main__":
    print("--- SISTEM BERMULA ---")
    
    bot.remove_webhook()
    time.sleep(2) 
    
    print("Bot is LIVE! Sedia menerima mesej.")
    
    # Gunakan polling yang lebih stabil
    bot.polling(non_stop=True, interval=1, timeout=20)
