import os
import time
import telebot
from google import genai
from dotenv import load_dotenv

# 1. SETUP PERALATAN
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

# 2. MUAT NAIK DATA LATIHAN (KNOWLEDGE BASE)
try:
    with open("knowledge_base.txt", "r", encoding="utf-8") as file:
        training_data = file.read()
except Exception as e:
    print(f"Ralat membaca fail: {e}")
    training_data = "Tiada data latihan tersedia buat masa ini."

# 3. ARAHAN SISTEM (SYSTEM PROMPT)
system_instruction = f"""
Anda adalah pembantu latihan digital untuk Micro SME & SME. 
HANYA jawab menggunakan data ini: {training_data}
Jika jawapan tiada dalam data, balas: TRIGGER_FALLBACK
Gunakan bahasa yang sama dengan pengguna (Malay/English).
Pastikan nada profesional dan ringkas.
"""

# 4. PENGENDALI MESEJ (MESSAGE HANDLER)
@bot.message_handler(func=lambda message: True) # Membolehkan semua orang (termasuk Admin) untuk test
def handle_messages(message):
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # Panggil Gemini 2.0 Flash
        response = client.models.generate_content(
            model="gemini-1.5-flash", # Tukar dari 2.0 ke 1.5
            config={'system_instruction': system_instruction},
            contents=message.text
        )
        ai_text = response.text.strip()

        # Logik jika soalan luar dari Knowledge Base
        if "TRIGGER_FALLBACK" in ai_text:
            bot.reply_to(message, "Maaf, saya akan semak dengan pakar kami dan kembali kepada anda segera!")
            # Beritahu Admin
            if ADMIN_CHAT_ID:
                bot.send_message(ADMIN_CHAT_ID, f"🚨 **Soalan Baru (Perlu Bantuan)**\nUser ID: {message.chat.id}\nSoalan: {message.text}")
        else:
            bot.reply_to(message, ai_text)

    except Exception as e:
        print(f"Gemini Error: {e}")
        bot.reply_to(message, "Sistem sedang dikemaskini. Sila cuba sebentar lagi.")

# 5. FUNGSI ADMIN UNTUK BALAS PELAJAR
@bot.message_handler(func=lambda message: message.reply_to_message and str(message.chat.id) == str(ADMIN_CHAT_ID))
def handle_admin_reply(message):
    try:
        # Mencari User ID daripada mesej alert
        original_msg = message.reply_to_message.text
        target_user_id = original_msg.split("User ID: ")[1].split("\n")[0]
        
        bot.send_message(target_user_id, f"👨‍🏫 **Jawapan Pakar:** {message.text}")
        bot.reply_to(message, "Jawapan telah dihantar kepada pelajar.")
    except Exception as e:
        print(f"Admin Reply Error: {e}")
        bot.reply_to(message, "Gagal menghantar jawapan. Pastikan anda 'Reply' pada mesej alert.")

# 6. PENGURUSAN RESTART & CONFLICT
if __name__ == "__main__":
    print("--- MEMULAKAN SISTEM BOT ---")
    
    try:
        bot.log_out() # Paksa tutup sesi lama di server Telegram
        time.sleep(5)
        bot.remove_webhook()
        print("Sesi lama telah dibersihkan.")
    except:
        pass

    print("Menunggu Railway stabil (10 saat)...")
    time.sleep(10) 

    print("Bot kini AKTIF dan sedia menjawab!")
    # Guna polling biasa dengan skip_pending untuk elakkan spam mesej lama
    bot.polling(non_stop=True, skip_pending=True)
