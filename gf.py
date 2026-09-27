import os
import threading
import requests
import telebot
from flask import Flask, request

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Render automatically provides this; fallback is your current Render URL.
WEBHOOK_URL = os.getenv(
    "WEBHOOK_URL",
    "https://faruk-gf.onrender.com"
)

GEMINI_MODEL = "gemini-2.5-flash"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Recent conversation memory
histories = {}

SYSTEM_PROMPT = """
You are Faruk GF, a ChatGPT-style intelligent Telegram AI assistant.

Understand what the user actually means and answer the current question.

Rules:
- Give relevant answers instead of generic replies.
- Remember recent conversation context.
- Follow topic changes naturally.
- Help with general questions, coding, writing, translation,
  ideas, explanations and casual conversation.
- Understand Hindi, Hinglish, Urdu and English.
- Reply naturally in the user's language/style.
- Be friendly and conversational.
- Do not claim to be a real human.
"""


def ask_gemini(user_id, message):

    history = histories.setdefault(user_id, [])

    history.append({
        "role": "user",
        "parts": [{"text": message}]
    })

    # Keep recent conversation
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
            "parts": [
                {"text": SYSTEM_PROMPT}
            ]
        },
        "contents": history,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 800
        }
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=60
        )

        print("GEMINI STATUS:", response.status_code)

        if response.status_code != 200:
            print("GEMINI ERROR:", response.text)

            # Remove failed user message
            if history and history[-1]["role"] == "user":
                history.pop()

            return "AI error: Gemini request failed."

        data = response.json()

        candidates = data.get("candidates", [])

        if not candidates:
            print("GEMINI EMPTY:", data)

            if history and history[-1]["role"] == "user":
                history.pop()

            return "AI ne koi response nahi diya."

        parts = candidates[0].get(
            "content", {}
        ).get("parts", [])

        answer = ""

        for part in parts:
            text = part.get("text")
            if text:
                answer += text

        answer = answer.strip()

        if not answer:
            print("GEMINI EMPTY TEXT:", data)

            if history and history[-1]["role"] == "user":
                history.pop()

            return "AI response empty tha."

        history.append({
            "role": "model",
            "parts": [{"text": answer}]
        })

        return answer

    except Exception as e:

        print("GEMINI EXCEPTION:", repr(e))

        if history and history[-1]["role"] == "user":
            history.pop()

        return "AI connection error."


# =========================
# TELEGRAM COMMANDS
# =========================

@bot.message_handler(commands=["start"])
def start(message):

    bot.reply_to(
        message,
        "Hey 👋❤️ Main Faruk GF hoon.\n\n"
        "Tum mujhse kisi bhi topic par baat kar sakte ho — "
        "questions, coding, writing, ideas ya normal chat. 😊\n\n"
        "/clear — chat memory clear"
    )


@bot.message_handler(commands=["clear"])
def clear(message):

    histories.pop(message.from_user.id, None)

    bot.reply_to(
        message,
        "🧹 Recent conversation memory clear ho gayi."
    )


@bot.message_handler(func=lambda message: True)
def chat(message):

    if not message.text:
        return

    try:
        bot.send_chat_action(
            message.chat.id,
            "typing"
        )
    except Exception:
        pass

    answer = ask_gemini(
        message.from_user.id,
        message.text
    )

    bot.reply_to(
        message,
        answer
    )


# =========================
# WEBHOOK
# =========================

@app.route("/", methods=["GET"])
def home():
    return "Faruk GF AI is LIVE ❤️"


@app.route("/health", methods=["GET"])
def health():
    return "OK"


@app.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():

    try:
        update = telebot.types.Update.de_json(
            request.get_data().decode("utf-8")
        )

        # Process in background so Telegram gets HTTP 200 quickly
        threading.Thread(
            target=bot.process_new_updates,
            args=([update],),
            daemon=True
        ).start()

        return "OK", 200

    except Exception as e:

        print("WEBHOOK ERROR:", repr(e))

        return "ERROR", 500


def set_webhook():

    webhook = WEBHOOK_URL.rstrip("/") + "/telegram-webhook"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"

    try:

        response = requests.post(
            url,
            json={
                "url": webhook,
                "drop_pending_updates": True
            },
            timeout=20
        )

        print("WEBHOOK SET:", response.status_code)
        print("WEBHOOK RESPONSE:", response.text)

    except Exception as e:

        print("WEBHOOK SET ERROR:", repr(e))


# =========================
# START SERVER
# =========================

if __name__ == "__main__":

    print("================================")
    print("❤️ FARUK GF AI WEBHOOK BOT")
    print("Model:", GEMINI_MODEL)
    print("================================")

    #
