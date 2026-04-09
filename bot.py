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

# Inisialisasi Bot Telegram
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Inisialisasi Gemini Client menggunakan API v1 (Stable untuk Tier 1)
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
        training_data = "Maklumat kursus dan bantuan SME belum dimuat naik."
except Exception as e:
    print(f"Ralat membaca fail: {e}")
    training_data = "Data tidak tersedia buat masa ini."

# 3. ARAHAN SISTEM (Diringkaskan untuk prestasi Gemini 3.1)
system_instruction = f"Anda pakar SME Malaysia. Jawab guna data ini sahaja: {training_data}. Jika tiada jawapan, balas: TRIGGER_FALLBACK. Guna Bahasa Melayu profesional."

# 4. PENGENDALI MESEJ
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # MENGGUNAKAN MODEL GEMINI 3.1 FLASH
try:
        # Format terbaru untuk SDK google-genai
        response = client.models.generate_content(
            model="gemini-3.1-flash", # Gunakan 1.5-flash untuk kestabilan maksimum
            contents=message.text,
            config={
                'system_instruction': system_instruction,
                'temperature': 0.7
            }
        )
        ai_text = response.text.strip()
        ai_text = response.text.strip()

        if "TRIGGER_FALLBACK" in ai_text:
            bot.reply_to(message, "Maaf, saya perlu semak perkara ini dengan pakar kami. Mohon tunggu sebentar.")
            if ADMIN_CHAT_ID:
                alert = f"🚨 **SOALAN BARU**\nUser ID: `{message.chat.id}`\nSoalan: {message.text}"
                bot.send_message(ADMIN_CHAT_ID, alert)
        else:
            bot.reply_to(message, ai_text)

    except Exception as e:
        error_msg = str(e)
        print(f"Ralat Gemini: {error_msg}")
        
        if "404" in error_msg:
            bot.reply_to(message, "Sistem sedang mengemaskini model AI. Sila cuba lagi dalam seminit.")
        elif "429" in error_msg:
            bot.reply_to(message, "Had penggunaan dicapai. Sila tunggu sebentar.")
        else:
            bot.reply_to(message, "Maaf, sistem mengalami gangguan teknikal sementara.")

# 5. ADMIN REPLY LOGIC
@bot.message_handler(func=lambda message: message.reply_to_message and str(message.chat.id) == str(ADMIN_CHAT_ID))
def admin_reply(message):
    try:
        original_text = message.reply_to_message.text
        target_user_id = original_text.split("User ID: `")[1].split("`")[0]
        bot.send_message(target_user_id, f"👨‍🏫 **Jawapan Pakar:**\n\n{message.text}")
        bot.reply_to(message, "✅ Jawapan dihantar.")
    except Exception as e:
        bot.reply_to(message, "Ralat: Pastikan anda 'Reply' pada alert.")

# 6. STARTUP
if __name__ == "__main__":
    print("--- MEMULAKAN BOT (GEMINI 3.1 FLASH) ---")
    try:
        bot.remove_webhook()
        time.sleep(2)
    except:
        pass

    print("Bot is LIVE! Sedia menerima mesej.")
    bot.polling(non_stop=True, skip_pending=True)
