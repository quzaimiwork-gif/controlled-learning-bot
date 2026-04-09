import os
import time
import telebot
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Konfigurasi
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, threaded=False)
client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1'})

# Ambil data
try:
    with open("knowledge_base.txt", "r", encoding="utf-8") as f:
        training_data = f.read()
except:
    training_data = "Data tidak tersedia."

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        full_prompt = f"Data: {training_data}\n\nSoalan: {message.text}"
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=full_prompt
        )
        bot.reply_to(message, response.text.strip())
    except Exception as e:
        print(f"Gemini Error: {e}")
        bot.reply_to(message, "Maaf, sila cuba sebentar lagi.")

if __name__ == "__main__":
    print("Mencuci sesi lama...")
    bot.remove_webhook()
    time.sleep(2)
    
    print("Bot is LIVE dengan Token Baru!")
    # Menggunakan parameter yang lebih ketat untuk mengelakkan ralat 409
    bot.polling(non_stop=True, skip_pending=True, timeout=60)
