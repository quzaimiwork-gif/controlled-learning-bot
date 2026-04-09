import os
import time
import threading
import telebot
import traceback
from flask import Flask
from google import genai
from dotenv import load_dotenv

# 1. SETUP FLASK
load_dotenv()
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is alive!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 2. SETUP BOT & GEMINI
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, threaded=False)

# Cuba guna model 1.5 Flash jika 2.0 ada isu region
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options={'api_version': 'v1'}
)

try:
    with open("knowledge_base.txt", "r", encoding="utf-8") as f:
        training_data = f.read()
except:
    training_data = "Data tidak sedia."

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        # Kita cuba model 1.5 Flash (Paling stabil untuk semua region)
        prompt = f"Data: {training_data}\n\nSoalan: {message.text}"
        
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt
        )
        
        bot.reply_to(message, response.text.strip())
        
    except Exception as e:
        # INI PENTING: Ia akan cetak ralat penuh di Log Render
        print("--- GEMINI ERROR START ---")
        print(traceback.format_exc())
        print("--- GEMINI ERROR END ---")
        bot.reply_to(message, f"Sistem sibuk. Ralat: {str(e)[:50]}")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.remove_webhook()
    time.sleep(2)
    print("Bot Debug Version is LIVE!")
    bot.polling(non_stop=True, interval=1, timeout=20)
