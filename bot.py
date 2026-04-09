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

# Inisialisasi Bot (threaded=False wajib untuk elak ralat 409 di Render/Railway)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, threaded=False)

# Inisialisasi Gemini Client (Guna API v1 Stable)
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options={'api_version': 'v1'}
)

# 2. MUAT NAIK DATA LATIHAN (Knowledge Base)
def load_knowledge():
    try:
        if os.path.exists("knowledge_base.txt"):
            with open("knowledge_base.txt", "r", encoding="utf-8") as file:
                return file.read()
        return "Data SME tidak ditemui."
    except Exception as e:
        print(f"Ralat baca fail: {e}")
        return "Data tidak tersedia."

training_data = load_knowledge()

# 3. PENGENDALI MESEJ (Chat Logic)
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # Prompt Gabungan untuk ketepatan maklumat
        prompt_gabungan = (
            f"ARAHAN SISTEM: Anda pakar SME Malaysia. Jawab berdasarkan data ini: {training_data}. "
            f"Jika soalan tiada kaitan atau tiada dalam data, balas: TRIGGER_FALLBACK.\n\n"
            f"SOALAN PENGGUNA: {message.text}"
        )
        
        # Menggunakan Gemini 2.0 Flash (Versi Padu & Laju)
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt_gabungan
        )
        
        ai_text = response.text.strip()

        if "TRIGGER_FALLBACK" in ai_text:
            bot.reply_to(message, "Maaf, saya tidak mempunyai maklumat tepat mengenai perkara itu. Saya akan maklumkan kepada admin untuk membantu anda.")
            if ADMIN_CHAT_ID:
                alert = f"🚨 **SOALAN UNTUK ADMIN**\nUser ID: `{message.chat.id}`\nSoalan: {message.text}"
                bot.send_message(ADMIN_CHAT_ID, alert)
        else:
            bot.reply_to(message, ai_text)

    except Exception as e:
        print(f"Gemini Error: {e}")
        bot.reply_to(message, "Maaf, saya mengalami gangguan teknikal sebentar. Sila cuba lagi.")

# 4. ADMIN REPLY (Balas terus kepada User)
@bot.message_handler(func=lambda message: message.reply_to_message and str(message.chat.id) == str(ADMIN_CHAT_ID))
def admin_reply(message):
    try:
        original_text = message.reply_to_message.text
        target_user_id = original_text.split("User ID: `")[1].split("`")[0]
        bot.send_message(target_user_id, f"👨‍🏫 **Jawapan Pakar:**\n\n{message.text}")
        bot.reply_to(message, "✅ Jawapan dihantar.")
    except Exception:
        bot.reply_to(message, "Gagal. Pastikan reply pada mesej alert sahaja.")

# 5. STARTUP (Anti-Conflict)
if __name__ == "__main__":
    print("--- MEMULAKAN BOT DI RENDER ---")
    
    # Cuci sesi lama
    bot.remove_webhook()
    time.sleep(2)
    
    print("Bot is LIVE!")
    
    # Gunakan polling yang tenang
    bot.polling(non_stop=True, interval=1, timeout=20)
