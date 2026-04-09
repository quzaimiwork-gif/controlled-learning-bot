import os
import time
import telebot
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Setup
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1'})

# Data Latihan
try:
    with open("knowledge_base.txt", "r", encoding="utf-8") as f:
        training_data = f.read()
except:
    training_data = "Data SME belum sedia."

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        # Gunakan prompt ringkas untuk jimat token
        full_prompt = f"Data: {training_data}\n\nSoalan: {message.text}"
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=full_prompt
        )
        bot.reply_to(message, response.text.strip())
    except Exception as e:
        print(f"Gemini Error: {e}")
        bot.reply_to(message, "Maaf, sistem sedang stabilkan sambungan. Cuba lagi dalam 5 saat.")

# BAHAGIAN STARTUP YANG LEBIH SELAMAT
if __name__ == "__main__":
    print("Mencuba untuk menyambung ke Telegram...")
    
    # 1. Padam sebarang Webhook yang mungkin tersangkut
    bot.remove_webhook()
    time.sleep(1)
    
    # 2. Loop kecil untuk elakkan crash 409 masa startup
    while True:
        try:
            print("Bot is LIVE!")
            bot.polling(non_stop=True, interval=2, timeout=20)
        except Exception as e:
            print(f"Conflict detected, retrying in 5s... Error: {e}")
            time.sleep(5)
