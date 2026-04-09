import os
import telebot
import google.generativeai as genai
from dotenv import load_dotenv

# Load local environment variables (if testing locally)
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)

# 1. Read the Curriculum
with open("knowledge_base.txt", "r", encoding="utf-8") as file:
    training_data = file.read()

# 2. Configure the Strict System Prompt
system_instruction = f"""
You are a specialized Training Assistant for our digital enablement program.
Your ONLY source of truth is the provided TRAINING DATA.
If a user asks a question not explicitly covered in the data, or asks general knowledge questions, reply EXACTLY with: TRIGGER_FALLBACK.
Identify the user's language (English or Malay) and respond in that same language.
Keep answers concise, professional, and encouraging.

TRAINING DATA:
{training_data}
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash", # Use the stable flash model
    system_instruction=system_instruction
)

# 3. Handle Incoming Student Messages
@bot.message_handler(func=lambda message: str(message.chat.id) != str(ADMIN_CHAT_ID))
def handle_student_message(message):
    user_id = message.chat.id
    user_text = message.text

    # Show "Bot is typing..."
    bot.send_chat_action(user_id, 'typing')

    try:
        response = model.generate_content(user_text)
        ai_text = response.text.strip()

        # Check if Gemini triggered the guardrail
        if "TRIGGER_FALLBACK" in ai_text:
            # Simple Malay detection for the automated response
            if any(word in user_text.lower() for word in ['apa', 'macam', 'nak', 'kenapa', 'boleh', 'saya']):
                bot.reply_to(message, "Maaf, soalan ini di luar skop modul asas. Saya akan ajukan soalan ini kepada pakar/admin kami, dan mereka akan balas di sini sebentar lagi!")
            else:
                bot.reply_to(message, "This is a bit outside the module scope. I've forwarded this to our human experts, and they will reply right here shortly!")
            
            # Forward the escalation to the Admin (You)
            bot.send_message(
                ADMIN_CHAT_ID, 
                f"🚨 **New Escalation**\nUser: {message.from_user.first_name} (ID: {user_id})\nQuestion: {user_text}\n\n*Reply directly to this message to answer the student.*",
                parse_mode="Markdown"
            )
        else:
            # Safe to send the AI answer
            bot.reply_to(message, ai_text)

    except Exception as e:
        bot.reply_to(message, "System error. Please try again later.")
        print(e)

# 4. Handle Your (Admin) Replies
@bot.message_handler(func=lambda message: message.reply_to_message and str(message.chat.id) == str(ADMIN_CHAT_ID))
def handle_admin_reply(message):
    try:
        # Extract the student's ID from your forwarded alert
        original_text = message.reply_to_message.text
        user_id_str = original_text.split("(ID: ")[1].split(")")[0]
        
        # Send your human answer back to the student
        bot.send_message(user_id_str, f"👨‍🏫 **Admin Reply:**\n{message.text}")
        bot.reply_to(message, "✅ Reply sent to student.")
        
        # (Optional Future Step): You could add code here to automatically append 
        # the Question & Answer to knowledge_base.txt
    except Exception as e:
        bot.reply_to(message, "Failed to send reply. Ensure you are replying directly to the escalation alert.")

print("Bot is running...")
bot.infinity_polling()
