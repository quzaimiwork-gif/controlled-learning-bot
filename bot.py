import os
import time
import threading
import telebot
from flask import Flask
from google import genai
from dotenv import load_dotenv

# 1. SETUP FLASK (Untuk Render Health Check)
load_dotenv()
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running!", 200

def run_flask():
    # Render secara automatik beri port melalui environment variable PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 2. SETUP BOT & GEMINI
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, threaded=False)
client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1'})

# Ambil data SME
try:
    with open("knowledge_base.txt", "r", encoding="utf-8") as f:
        training_data = f.read()
except:
    training_data = "Data tidak tersedia."

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        # Gunakan Gemini 2.0 Flash (Paling Padu & Laju)
        prompt = f"Data: {training_data}\n\nSoalan: {message.text}"
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        bot.reply_to(message, response.text.strip())
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Maaf, sistem sedang sibuk sedikit. Cuba lagi dalam 5 saat.")

# 3. RUN (Flask + Polling)
if __name__ == "__main__":
    # Jalankan Flask dalam thread berasingan supaya tidak ganggu bot
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Cuci sesi Telegram lama
    bot.remove_webhook()
    time.sleep(2)
    
    print("Bot is LIVE on Render Web Service!")
    # Mula polling
    bot.polling(non_stop=True, interval=1, timeout=20)
