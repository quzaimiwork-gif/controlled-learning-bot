import os
import telebot
from google import genai
from dotenv import load_dotenv

# 1. SETUP
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
# Using the NEW 2026 Client structure
client = genai.Client(api_key=GEMINI_API_KEY)

# 2. LOAD KNOWLEDGE
try:
    with open("knowledge_base.txt", "r", encoding="utf-8") as file:
        training_data = file.read()
except:
    training_data = "No training data."

# 3. SYSTEM PROMPT
system_instruction = f"""
You are a training assistant. ONLY answer using this data: {training_data}
If the answer is not there, reply EXACTLY: TRIGGER_FALLBACK
Mirror the user's language (English/Malay).
"""

# 4. HANDLERS
@bot.message_handler(func=lambda message: str(message.chat.id) != str(ADMIN_CHAT_ID))
def handle_student(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        # Use the latest generation method
    response = client.models.generate_content(
            model="gemini-2.0-flash", # Tukar ke versi 2.0
            config={'system_instruction': system_instruction},
            contents=message.text
        )
        ai_text = response.text.strip()

        if "TRIGGER_FALLBACK" in ai_text:
            bot.reply_to(message, "I'll check with the experts and get back to you!")
            bot.send_message(ADMIN_CHAT_ID, f"🚨 **Question Alert**\nUser: {message.chat.id}\nText: {message.text}\n\n*Reply to answer*")
        else:
            bot.reply_to(message, ai_text)
    except Exception as e:
        print(f"Gemini Error: {e}")

@bot.message_handler(func=lambda message: message.reply_to_message and str(message.chat.id) == str(ADMIN_CHAT_ID))
def handle_admin(message):
    try:
        # Extract user ID from text (Assumes format: User: 123456)
        target_id = message.reply_to_message.text.split("User: ")[1].split("\n")[0]
        bot.send_message(target_id, f"👨‍🏫 **Admin:** {message.text}")
        bot.reply_to(message, "Sent!")
    except:
        bot.reply_to(message, "Error replying.")

if __name__ == "__main__":
    import time
    print("--- MEMULAKAN HARD RESET ---")
    
    try:
        # 1. Paksa Telegram tutup semua sesi lama
        bot.log_out()
        print("Sesi lama telah di 'Log Out'.")
        time.sleep(5)
        
        # 2. Padam sebarang Webhook yang tersangkut
        bot.remove_webhook()
        print("Webhook dipadam.")
        time.sleep(5)
    except Exception as e:
        print(f"Nota: Sesi sedia ada sudah bersih. {e}")

    print("Menunggu Railway tamatkan proses lama (15 saat)...")
    time.sleep(15) 

    print("Bot kini AKTIF dan sedia menjawab!")
    try:
        # Guna polling biasa, bukan infinity untuk elakkan loop crash
        bot.polling(non_stop=True, skip_pending=True, interval=3)
    except Exception as e:
        print(f"Polling Error: {e}")
