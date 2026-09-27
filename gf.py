import os
import threading
import requests
import telebot
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Recent conversation for each user
histories = {}

SYSTEM_PROMPT = """
You are Faruk GF, an intelligent ChatGPT-style Telegram assistant.

Your job is to understand what the user actually wants and answer helpfully.

IMPORTANT:
- Answer the current question directly.
- Use previous messages when they are relevant.
- If the user changes topic, follow the new topic.
- Never give a generic reply when a specific answer is possible.
- Do not repeat the same answer unnecessarily.
- You can help with general questions, explanations, writing, coding,
  ideas, translations, calculations, and casual conversation.
- Understand Hindi, Hinglish, Urdu and English.
- Reply naturally in the language/style the user uses.
- Keep casual answers concise, but explain properly when the question
  needs detail.
- You are an AI assistant; don't claim to be a real human.
- You can have a warm, friendly personality, but usefulness comes first.
"""

def ask_ai(user_id, message):
    history = histories.setdefault(user_id, [])

    history.append({
        "role": "user",
        "parts": [{"text": message}]
    })

    # Keep recent context
    history[:] = history[-20:]

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{GEMINI_MODEL}:generateContent"
    )

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }

    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": history,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 800
        }
    }

    try:
        r = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=60
        )

        print("GEMINI STATUS:", r.status_code)

        if r.status_code != 200:
            print("GEMINI ERROR:", r.text)

            # Don't keep a failed request in memory
            if history and history[-1]["role"] == "user":
                history.pop()

            return "😕 Abhi AI response nahi aa paaya. Thodi der baad try karo."

        data = r.json()

        candidates = data.get("candidates", [])

        if not candidates:
            print("EMPTY CANDIDATES:", data)

            if history and history[-1]["role"] == "user":
                history.pop()

            return "😕 Mujhe abhi proper response nahi mila."

        parts = candidates[0].get("content", {}).get("parts", [])

        answer = "".join(
            part.get("text", "")
            for part in parts
        ).strip()

        if not answer:
            print("EMPTY ANSWER:", data)

            if history and history[-1]["role"] == "user":
                history.pop()

            return "😕 Reply generate nahi ho paya."

        history.append({
            "role": "model",
            "parts": [{"text": answer}]
        })

        return answer

    except requests.exceptions.Timeout:
        if history and history[-1]["role"] == "user":
            history.pop()
        return "⏳ AI response mein thoda time lag raha hai. Dobara try karo."

    except Exception as e:
        print("AI EXCEPTION:", repr(e))

        if history and history[-1]["role"] == "user":
            history.pop()

        return "😕 Technical problem aa gayi. Dobara try karo."


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "Hey 👋❤️ Main Faruk GF hoon.\n\n"
        "Mujhse kisi bhi topic par baat karo — questions, coding, "
        "writing, ideas ya normal chat. Main context ke according reply karungi. 😊\n\n"
        "Chat reset: /clear"
    )


@bot.message_handler(commands=["clear"])
def clear(message):
    histories.pop(message.from_user.id, None)
    bot.reply_to(message, "🧹 Recent chat memory clear ho gayi.")


@bot.message_handler(func=lambda message: True)
def chat(message):
    if not message.text:
        return

    user_id = message.from_user.id

    # Telegram typing indicator
    try:
        bot.send_chat_action(message.chat.id, "typing")
    except Exception:
        pass

    answer = ask_ai(user_id, message.text)

    bot.reply_to(message, answer)


@app.route("/")
def home():
    return "Faruk GF AI is running ❤️"


@app.route("/health")
def health():
    return "OK"


def run_bot():
    print("================================")
    print("❤️ FARUK GF AI BOT STARTED")
    print("Model:", GEMINI_MODEL)
    print("================================")

    bot.infinity_polling(
        timeout=60,
        long_polling_timeout=60
    )


if __name__ == "__main__":
    threading.Thread(
        target=run_bot,
        daemon=True
    ).start()

    port = int(os.getenv("PORT", "10000"))

    app.run(
        host="0.0.0.0",
        port=port
    )
