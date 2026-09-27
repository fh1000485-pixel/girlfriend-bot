import os
import threading
import requests
import telebot
from flask import Flask

BOT_TOKEN = os.environ["BOT_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

user_history = {}

SYSTEM_PROMPT = """
You are Faruk GF, a friendly virtual girlfriend chatbot.

Rules:
- Understand the user's current topic and reply directly to it.
- Never repeat generic replies.
- Remember recent conversation context.
- Follow topic changes naturally.
- Support Hindi, Hinglish, Urdu and English.
- Reply in the same language/style as the user.
- Keep replies natural, friendly and conversational.
- Use emojis naturally, but don't overuse them.
- Never claim to be a real human.
"""

def ask_gemini(user_id, message):
    history = user_history.setdefault(user_id, [])

    history.append({
        "role": "user",
        "parts": [{"text": message}]
    })

    # Keep recent conversation only
    history[:] = history[-12:]

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-2.5-flash:generateContent"
    )

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }

    data = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": history
    }

    response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=60
    )

    if response.status_code != 200:
        print("GEMINI ERROR:", response.status_code, response.text)
        return "Sorry 😅 Abhi AI se connection mein problem aa gayi. Thodi der baad try karo ❤️"

    result = response.json()

    try:
        reply = result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        print("GEMINI RESPONSE ERROR:", result)
        return "Sorry 😅 Mujhe reply generate karne mein problem hui ❤️"

    history.append({
        "role": "model",
        "parts": [{"text": reply}]
    })

    return reply


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "Hey 🥰❤️ Main Faruk GF hoon!\n"
        "Mujhse normally baat karo, main tumhari baat ke according reply karungi."
    )


@bot.message_handler(commands=["clear"])
def clear(message):
    user_history.pop(message.from_user.id, None)
    bot.reply_to(message, "Chat memory clear ho gayi 🧹❤️")


@bot.message_handler(func=lambda message: True)
def chat(message):
    try:
        reply = ask_gemini(message.from_user.id, message.text)
        bot.reply_to(message, reply)
    except Exception as e:
        print("BOT ERROR:", repr(e))
        bot.reply_to(
            message,
            "Sorry 😅 Kuch technical problem aa gayi. Thodi der baad try karo ❤️"
        )


@app.route("/")
def home():
    return "Faruk GF is running ❤️"


@app.route("/health")
def health():
    return "OK"


def run_bot():
    print("❤️ FARUK GF GEMINI BOT STARTED")
    bot.infinity_polling(
        timeout=60,
        long_polling_timeout=60
    )


if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
