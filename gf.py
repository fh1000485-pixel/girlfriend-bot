import os
import threading
import telebot
import requests
from flask import Flask

# ==============================
# ENVIRONMENT VARIABLES
# ==============================

BOT_TOKEN = os.environ["BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

# ==============================
# BOT SETUP
# ==============================

bot = telebot.TeleBot(BOT_TOKEN)

# User-wise conversation history
user_history = {}

# ==============================
# FLASK SERVER FOR RENDER
# ==============================

app = Flask(__name__)

@app.route("/")
def home():
    return "Faruk GF AI Bot is running ❤️", 200

@app.route("/health")
def health():
    return "OK", 200

# ==============================
# AI PERSONALITY
# ==============================

SYSTEM_PROMPT = """
You are Faruk GF, a friendly virtual girlfriend chatbot.

Talk naturally and warmly with the user.

IMPORTANT:
- Understand exactly what the user is talking about.
- Reply according to the current topic.
- Never give the same generic reply repeatedly.
- Remember recent conversation context.
- If the user changes the topic, follow the new topic.
- The user can speak Hindi, Hinglish, Urdu or English.
- Reply in the same language/style the user uses.
- Keep replies natural and conversational.
- Use emojis naturally, but don't overuse them.
- Do not claim to be a real human.
"""

# ==============================
# ASK AI
# ==============================

def ask_ai(user_id, message):

    if user_id not in user_history:
        user_history[user_id] = []

    user_history[user_id].append({
        "role": "user",
        "content": message
    })

    # Keep recent conversation
    user_history[user_id] = user_history[user_id][-20:]

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    data = {
        "model": "gpt-5.6-luna",
        "instructions": SYSTEM_PROMPT,
        "input": user_history[user_id]
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers=headers,
            json=data,
            timeout=60
        )

        if response.status_code != 200:
            print("OPENAI ERROR:")
            print(response.text)
            return "Sorry 😅 AI connection mein problem aa gayi. Thodi der baad try karo ❤️"

        result = response.json()

        reply = result.get("output_text", "")

        if not reply:
            for item in result.get("output", []):
                if item.get("type") == "message":
                    for content in item.get("content", []):
                        if content.get("type") == "output_text":
                            reply += content.get("text", "")

        if not reply:
            reply = "Hmm ❤️ Mujhe samajh nahi aaya, dobara batao."

        user_history[user_id].append({
            "role": "assistant",
            "content": reply
        })

        return reply

    except requests.exceptions.Timeout:
        return "AI ko response dene mein thoda time lag raha hai 😅 Dobara try karo ❤️"

    except Exception as e:
        print("AI ERROR:", e)
        return "Oops 😅 Kuch technical problem aa gayi."


# ==============================
# START
# ==============================

@bot.message_handler(commands=["start"])
def start(message):

    user_id = message.from_user.id
    name = message.from_user.first_name or "Friend"

    user_history[user_id] = []

    bot.send_message(
        message.chat.id,
        f"Hey {name} 🥰❤️\n\n"
        "Main Faruk GF hoon 💕\n\n"
        "Tum mujhse Hindi, Hinglish, Urdu ya English "
        "mein kisi bhi topic par baat kar sakte ho 😘\n\n"
        "Bolo, aaj kya baat karein? ❤️"
    )


# ==============================
# CLEAR MEMORY
# ==============================

@bot.message_handler(commands=["clear"])
def clear(message):

    user_history[message.from_user.id] = []

    bot.send_message(
        message.chat.id,
        "Chat memory clear kar di ❤️\n"
        "Ab fresh conversation start karte hain 🥰"
    )


# ==============================
# NORMAL CHAT
# ==============================

@bot.message_handler(func=lambda message: True)
def chat(message):

    if not message.text:
        return

    try:
        bot.send_chat_action(message.chat.id, "typing")

        reply = ask_ai(
            message.from_user.id,
            message.text
        )

        bot.send_message(
            message.chat.id,
            reply
        )

    except Exception as e:
        print("BOT ERROR:", e)

        bot.send_message(
            message.chat.id,
            "Oops 😅 Kuch technical problem aa gayi."
        )


# ==============================
# TELEGRAM BOT
# ==============================

def run_bot():
    print("================================")
    print("❤️ FARUK GF AI BOT STARTED")
    print("================================")

    bot.infinity_polling(
        timeout=60,
        long_polling_timeout=60,
        skip_pending=True
    )


# ==============================
# START BOTH SERVERS
# ==============================

if __name__ == "__main__":

    bot_thread = threading.Thread(
        target=run_bot,
        daemon=True
    )

    bot_thread.start()

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
