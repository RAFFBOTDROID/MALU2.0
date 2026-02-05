import os
import requests
import openai
from flask import Flask, request

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
PORT = int(os.getenv("PORT", 10000))

openai.api_key = OPENAI_KEY

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

# ================= UTIL =================

def send_message(chat_id, text, reply_to=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_to:
        payload["reply_to_message_id"] = reply_to

    requests.post(f"{API_URL}/sendMessage", json=payload)


def malu_ai_response(user_text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é MALU ULTRA, uma IA feminina, carismática, inteligente, sarcástica quando necessário, divertida e protetora."},
                {"role": "user", "content": user_text}
            ],
            temperature=0.8,
            max_tokens=400
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return "💖 Estou aqui, mas minha IA teve um pequeno erro técnico agora. Tenta de novo, amor."


# ================= WEBHOOK =================

@app.route("/", methods=["GET"])
def home():
    return "💖 MALU ULTRA FIXA ONLINE"


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" in data:
        msg = data["message"]

        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")
        msg_id = msg.get("message_id")

        if text.startswith("/start"):
            send_message(chat_id, "💖 Oi! Eu sou a *MALU ULTRA FIXA*. Fala comigo 😘", msg_id)
            return "ok"

        if text.startswith("/ping"):
            send_message(chat_id, "🏓 Pong! MALU está viva 😈", msg_id)
            return "ok"

        if text.strip() != "":
            reply = malu_ai_response(text)
            send_message(chat_id, reply, msg_id)

    return "ok"


# ================= AUTO SET WEBHOOK =================

def set_webhook():
    url = os.getenv("RENDER_EXTERNAL_URL")
    if url:
        hook_url = f"{url}/{BOT_TOKEN}"
        requests.get(f"{API_URL}/setWebhook?url={hook_url}")
        print("✅ Webhook configurado:", hook_url)


if __name__ == "__main__":
    set_webhook()
    print("💖 MALU ULTRA FIXA INICIANDO...")
    app.run(host="0.0.0.0", port=PORT)
