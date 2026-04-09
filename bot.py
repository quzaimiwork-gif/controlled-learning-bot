import os
import telebot
import google.generativeai as genai
from dotenv import load_dotenv

# 1. SETUP & CONFIGURATION
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# Initialize Telegram Bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)

# 2. LOAD KNOWLEDGE BASE
try:
    with open("knowledge_base.txt", "r", encoding="utf-8") as file:
        training_data = file.read()
except FileNotFoundError:
    training_data = "No training data available."

# 3. CONFIGURE SYSTEM PROMPT
# We prepare the instruction as a dictionary to avoid the "keyword argument" error
instruction_content = {
    "role": "system",
    "parts": [{"text": f"""
You are a specialized Training Assistant for our digital enablement program.
Your ONLY source of truth is the provided TRAINING DATA below. 

STRICT RULES:
1. If a user asks about something NOT in the data (e.g., whales, celebrities, general history), 
   you MUST NOT answer. Instead, reply EXACTLY with: TRIGGER_FALLBACK
2. Identify the user's language (English or Malay) and respond in that same language.
3. Be professional, warm, and encouraging.

TRAINING DATA:
{training_data}
"""}]
}

# Initialize the model without system_instruction in __init__ to prevent crashes
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# 4. STUDENT MESSAGE HANDLER
@bot.message_handler(func=lambda message: str(message.chat.id) != str(ADMIN_CHAT_ID))
def handle_student_message(message):
    user_id = message.chat.id
    user_text = message.text

    # Show "Typing..." in Telegram
    bot.send_chat_action(user_id, 'typing')

    try:
        # We start a chat and pass the system instruction as the first message
        chat = model.start_chat(history=[instruction_content])
        response = chat.send_message(user_text)
        ai_text = response.text.strip()

        # Check for fallback trigger
        if "TRIGGER_FALLBACK" in ai_text.upper():
            # Multilingual fallback message
            if any(word in user_text.lower() for word in ['apa', 'macam', 'nak', 'boleh', 'saya']):
                bot.reply_to(message, "Maaf, soalan ini di luar skop modul. Saya akan ajukan kepada admin dan mereka akan balas sebentar lagi!")
            else:
                bot.reply_to(message, "I'm not sure about that. I've forwarded your question to our experts to help you out!")
            
            # Alert the Admin (You)
            bot.send_message(
                ADMIN_CHAT_ID, 
                f"🚨 **NEW QUESTION**\nFrom: {message.from_user.first_name} (ID: {user_id})\nQuestion: {user_text}\n\n*Reply to this message to answer.*",
                parse_mode="Markdown"
            )
        else:
            bot.reply_to(message, ai_text)

    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "I'm having a little trouble connecting. Please try again in a moment!")

# 5. ADMIN REPLY HANDLER
@bot.message_handler(func=lambda message: message.reply_to_message and str(message.chat.id) == str(ADMIN_CHAT_ID))
def handle_admin_reply(message):
    try:
        # Extract student ID from the admin alert message
        original_text = message.reply_to_message.text
        target_user_id = original_text.split("(ID: ")[1].split(")")[0]
        
        # Send admin's message to the student
        bot.send_message(target_user_id, f"👨‍🏫 **Admin Reply:**\n{message.text}")
        bot.reply_to(message, "✅ Your answer has been sent to the student.")
    except Exception as e:
        bot.reply_to(message, "Error sending reply. Make sure you are replying to the bot's alert message.")

# 6. START BOT
print("Bot is live...")
bot.infinity_polling()
