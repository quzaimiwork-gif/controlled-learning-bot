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
client = genai.Client(api_key=GEMINI_API_KEY)

# 2. MUAT NAIK DATA LATIHAN
try:
    if os.path.exists("knowledge_base.txt"):
        with open("knowledge_base.txt", "r", encoding="utf-8") as file:
            training_data = file.read()
    else:
        training_data = "Sila rujuk pakar."
except Exception as e:
    training_data = "Data tidak tersedia."

# 3. ARAHAN SISTEM (DIBETULKAN)
system_instruction = f"Anda pakar SME. Jawab guna data ini sahaja: {training_data}. Jika tiada jawapan, balas: TRIGGER_FALLBACK. Guna bahasa pengguna, ringkas dan profesional."

# 4. PENGENDALI MESEJ
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
# CUBAAN 2: Format spesifik
        response = client.models.generate_content(
            model = "gemini-2.0-flash",
            config={'system_instruction': system_instruction},
            contents=message.text
        )
        ai_text = response.text.strip()

        if "TRIGGER_FALLBACK" in ai_text:
            bot.reply_to(message, "Maaf, saya akan semak dengan pakar kami dan kembali kepada anda segera!")
            if ADMIN_CHAT_ID:
                bot.send_message(ADMIN_CHAT_ID, f"🚨 **Soalan Perlu Bantuan**\nUser: `{message.chat.id}`\nText: {message.text}")
        else:
            bot.reply_to(message, ai_text)

    except Exception as e:
        print(f"Gemini Error: {e}")
        bot.reply_to(message, "Maaf, sistem sedang sibuk. Sila cuba sebentar lagi.")

# 5. ADMIN REPLY
@bot.message_handler(func=lambda message: message.reply_to_message and str(message.chat.id) == str(ADMIN_CHAT_ID))
def admin_reply(message):
    try:
        original_text = message.reply_to_message.text
        target_user_id = original_text.split("User: `")[1].split("`")[0]
        bot.send_message(target_user_id, f"👨‍🏫 **Jawapan Pakar:**\n\n{message.text}")
        bot.reply_to(message, "✅ Berjaya dihantar.")
    except Exception as e:
        bot.reply_to(message, "Ralat: Reply pada mesej alert sahaja.")

# 6. PENGURUSAN STARTUP (ANTI-CONFLICT)
if __name__ == "__main__":
    print("--- MEMULAKAN SISTEM BOT ---")
    try:
        bot.remove_webhook()
        bot.get_updates(offset=-1) # Cuci mesej lama
    except:
        pass

    print("Menunggu Railway tamatkan proses lama (15 saat)...")
    time.sleep(15) 

    print("Bot kini AKTIF!")
    # Guna polling biasa untuk elakkan isu 409 yang berlarutan
    bot.polling(non_stop=True, skip_pending=True, interval=2)
