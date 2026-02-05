import os
import requests
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters

TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
PORT = int(os.getenv("PORT", 10000))

bot = Bot(token=TOKEN)
app = Flask(__name__)

dispatcher = Dispatcher(bot, None, workers=0)

# =========================
# IA GROQ
# =========================
def ai_reply(text):
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama3-70b-8192",
            "messages": [
                {"role": "system", "content": "Você é Malu Elite, uma IA elegante, carismática e inteligente."},
                {"role": "user", "content": text}
            ],
            "temperature": 0.7
        }
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
        return r.json()["choices"][0]["message"]["content"]
    except:
        return "⚠️ Minha IA falhou agora, tenta de novo 💖"

# =========================
# NÃO RESPONDER REPLY
# =========================
def ignore_replies(update, context):
    if update.message.reply_to_message:
        return

# =========================
# START
# =========================
def start(update, context):
    update.message.reply_text("💖 Oi! Eu sou a **Malu Ultra Elite**!")

# =========================
# CHAT IA
# =========================
def chat(update, context):
    msg = update.message.text

    # Ignorar replies
    if update.message.reply_to_message:
        return

    if msg.startswith("/"):
        return

    resposta = ai_reply(msg)
    update.message.reply_text(resposta)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

# =========================
# WEBHOOK ENDPOINT
# =========================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, bot)
    dispatcher.process_update(update)
    return "ok"

# =========================
# HEALTH CHECK
# =========================
@app.route("/")
def index():
    return "Malu Ultra Elite Online"

# =========================
# RUN
# =========================
if __name__ == "__main__":
    webhook_url = f"https://SEU_APP.onrender.com/{TOKEN}"
    bot.set_webhook(webhook_url)
    app.run(host="0.0.0.0", port=PORT)
