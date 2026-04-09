import os
import time
import telebot
from google import genai
from dotenv import load_dotenv

# 1. SETUP KONFIGURASI
load_dotenv()

# Ambil maklumat dari Railway Variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# Inisialisasi Bot & AI Client
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

# 2. MUAT NAIK DATA LATIHAN (KNOWLEDGE BASE)
try:
    if os.path.exists("knowledge_base.txt"):
        with open("knowledge_base.txt", "r", encoding="utf-8") as file:
            training_data = file.read()
    else:
        training_data = "Sila rujuk pakar untuk maklumat lanjut."
except Exception as e:
    print(f"Ralat fail: {e}")
    training_data = "Data tidak tersedia."

# 3. ARAHAN SISTEM (SYSTEM PROMPT)
# Ganti bahagian ini sahaja dalam bot.py di GitHub
system_instruction = f"Anda pembantu SME. Jawab ringkas guna data ini: {training_data}. Jika tiada, balas: TRIGGER_FALLBACK"
Anda adalah pakar perunding digital untuk Micro SME & SME di Malaysia. 
Tugas anda: Jawab soalan berdasarkan data ini SAHAJA: {training_data}

PERATURAN:
1. Jika jawapan TIADA dalam data, balas: TRIGGER_FALLBACK
2. Gunakan bahasa yang sama dengan pengguna.
3. Jawapan mestilah ringkas, padat, dan profesional.
"""

# 4. PENGENDALI MESEJ (MESSAGE HANDLER)
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    # Tunjukkan status 'typing' di Telegram
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # Panggil Gemini 1.5 Flash (Lebih stabil untuk Free Tier)
        # Guna format nama model tanpa prefix 'models/' jika 404 berterusan
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            config={
                'system_instruction': system_instruction,
                'temperature': 0.7, # Tambah ini untuk kestabilan akaun billing
            },
            contents=message.text
        )
        ai_text = response.text.strip()

        # Semak jika AI tidak tahu jawapan
        if "TRIGGER_FALLBACK" in ai_text:
            bot.reply_to(message, "Maaf, saya tidak mempunyai maklumat tepat mengenai perkara ini. Saya akan maklumkan kepada pakar kami untuk membantu anda segera.")
            
            # Hantar notifikasi kepada Admin (jika ada ID)
            if ADMIN_CHAT_ID:
                alert_text = (
                    f"🚨 **SOALAN BARU PERLU BANTUAN**\n\n"
                    f"User ID: `{message.chat.id}`\n"
                    f"Nama: {message.from_user.first_name}\n"
                    f"Soalan: {message.text}\n\n"
                    f"*Sila reply pada mesej ini untuk menjawab.*"
                )
                bot.send_message(ADMIN_CHAT_ID, alert_text, parse_mode="Markdown")
        else:
            bot.reply_to(message, ai_text)

    except Exception as e:
        # Jika kena error 429 (Quota), bot akan balas mesra
        if "429" in str(e):
            print("Gemini Quota Exceeded (429).")
            bot.reply_to(message, "Maaf, sistem sedang menerima terlalu banyak soalan. Sila cuba lagi dalam 1 minit.")
        else:
            print(f"Gemini Error: {e}")
            bot.reply_to(message, "Sistem sedang dikemaskini. Sila cuba sebentar lagi.")

# 5. FUNGSI ADMIN BALAS PELAJAR (REPLY LOGIC)
@bot.message_handler(func=lambda message: message.reply_to_message and str(message.chat.id) == str(ADMIN_CHAT_ID))
def admin_reply_logic(message):
    try:
        # Ekstrak User ID dari mesej alert
        original_text = message.reply_to_message.text
        target_user_id = original_text.split("User ID: `")[1].split("`")[0]
        
        jawapan_pakar = f"👨‍🏫 **Jawapan Pakar:**\n\n{message.text}"
        bot.send_message(target_user_id, jawapan_pakar)
        bot.reply_to(message, "✅ Jawapan anda telah dihantar kepada pelajar.")
    except Exception as e:
        print(f"Admin Error: {e}")
        bot.reply_to(message, "Ralat: Pastikan anda 'Reply' pada mesej alert yang ada User ID.")

# 6. PENGURUSAN STARTUP
if __name__ == "__main__":
    print("--- MEMULAKAN SISTEM BOT ---")
    
    # Kita buang 'bot.log_out()' untuk elakkan Error 400
    try:
        bot.remove_webhook()
        print("Webhook cleared.")
    except:
        pass

    print("Menunggu Railway stabil (10 saat)...")
    time.sleep(10) 

    print("Bot kini AKTIF dan sedia menjawab!")
    
    # Gunakan infinity_polling dengan retry yang lebih selamat
    bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
