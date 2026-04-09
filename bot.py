import os
import time
import telebot
from google import genai
from dotenv import load_dotenv

# 1. SETUP KONFIGURASI
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Guna API v1 untuk akaun Billing
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options={'api_version': 'v1'}
)

# 2. MUAT NAIK DATA LATIHAN
try:
    if os.path.exists("knowledge_base.txt"):
        with open("knowledge_base.txt", "r", encoding="utf-8") as file:
            training_data = file.read()
    else:
        training_data = "Data tidak tersedia."
except Exception:
    training_data = "Ralat data."

system_instruction = f"Anda pakar SME. Jawab guna data ini: {training_data}. Jika tiada, balas: TRIGGER_FALLBACK."

# 3. PENGENDALI MESEJ
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    bot.send_chat_action(message.chat.id, 'typing')
    
    # --- PASTIKAN SEMUA DI BAWAH INI MASUK KE DALAM (INDENTED) ---
    try:
        # Format gabungan untuk elakkan ralat 'Unknown name systemInstruction'
        prompt_gabungan = f"ARAHAN SISTEM: {system_instruction}\n\nSOALAN PENGGUNA: {message.text}"
        
        response = client.models.generate_content(
            model="gemini-3.1-flash",
            contents=prompt_gabungan
        )
        ai_text = response.text.strip()

        if "TRIGGER_FALLBACK" in ai_text:
            bot.reply_to(message, "Maaf, saya perlu semak dengan pakar kami sebentar.")
            if ADMIN_CHAT_ID:
                bot.send_message(ADMIN_CHAT_ID, f"🚨 Soalan: {message.text}\nUser ID: `{message.chat.id}`")
        else:
            bot.reply_to(message, ai_text)

    except Exception as e:
        print(f"Ralat: {e}")
        bot.reply_to(message, "Maaf, sistem sedang sibuk. Cuba lagi sebentar.")

# 4. ADMIN REPLY
@bot.message_handler(func=lambda message: message.reply_to_message and str(message.chat.id) == str(ADMIN_CHAT_ID))
def admin_reply(message):
    try:
        original_text = message.reply_to_message.text
        target_user_id = original_text.split("User ID: `")[1].split("`")[0]
        bot.send_message(target_user_id, f"👨‍🏫 **Jawapan Pakar:**\n\n{message.text}")
        bot.reply_to(message, "✅ Berjaya.")
    except Exception:
        bot.reply_to(message, "Gagal. Reply pada mesej alert sahaja.")

# 5. STARTUP
if __name__ == "__main__":
    print("--- SISTEM BERMULA ---")
    try:
        bot.remove_webhook()
        time.sleep(2)
    except:
        pass
    print("Bot is LIVE!")
    bot.polling(non_stop=True, skip_pending=True)
