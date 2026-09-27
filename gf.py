import telebot
import requests

# ==============================
# YOUR KEYS
# ==============================

BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"

# ==============================
# BOT SETUP
# ==============================

bot = telebot.TeleBot(BOT_TOKEN)

# User-wise conversation history
user_history = {}

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

    # Add user's message
    user_history[user_id].append({
        "role": "user",
        "content": message
    })

    # Keep last 20 messages
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

        # API error
        if response.status_code != 200:
            print("OPENAI ERROR:")
            print(response.text)

            return (
                "Sorry 😅 AI se connection mein "
                "problem aa gayi. Thodi der baad try karo ❤️"
            )

        result = response.json()

        # Get AI reply
        reply = result.get("output_text", "")

        if not reply:

            for item in result.get("output", []):
                if item.get("type") == "message":

                    for content in item.get("content", []):

                        if content.get("type") == "output_text":
                            reply += content.get("text", "")

        if not reply:
            reply = "Hmm ❤️ Mujhe samajh nahi aaya, dobara batao."

        # Save AI reply
        user_history[user_id].append({
            "role": "assistant",
            "content": reply
        })

        return reply

    except requests.exceptions.Timeout:

        return "AI ko response dene mein thoda time lag raha hai 😅 Dobara try karo ❤️"

    except Exception as e:

        print("ERROR:", e)

        return "Oops 😅 Kuch technical problem aa gayi."


# ==============================
# START COMMAND
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
# CLEAR CHAT
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
def chat(message):w
