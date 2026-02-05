import os
import asyncio
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
PORT = int(os.getenv("PORT", 10000))

WEBHOOK_URL = f"https://malu2-0.onrender.com/{TOKEN}"

app = Flask(__name__)

application = Application.builder().token(TOKEN).build()

# =========================
# IA — MALU PERSONALIDADE
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
                {
                    "role": "system",
                    "content": (
                        "Você é MALU, uma garota simpática, educada, humana, divertida e carismática. "
                        "Fale como amiga real, SEM ser invasiva e SEM responder mensagens em reply."
                    )
                },
                {"role": "user", "content": text}
            ],
            "temperature": 0.7
        }

        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )

        return r.json()["choices"][0]["message"]["content"]

    except:
        return "💖 Ai… meu cérebro deu uma leve bugada 😅 tenta de novo?"

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💖 Oii! Eu sou a **Malu Ultra Elite** — fala comigo!")

# =========================
# CHAT MALU — SEM REPLY
# =========================
async def malu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    # NÃO RESPONDER REPLY
    if msg.reply_to_message:
        return

    text = msg.text
    if not text:
        return

    # Ignorar comandos
    if text.startswith("/"):
        return

    gatilhos = ["malu", "oi malu", "fala malu", "hey malu"]

    if any(g in text.lower() for g in gatilhos) or len(text) > 15:
        resposta = ai_reply(text)
        await msg.reply_text(resposta)

# =========================
# HANDLERS
# =========================
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, malu))

# =========================
# INIT APP LOOP
# =========================
async def init_app():
    await application.initialize()
    await application.bot.set_webhook(WEBHOOK_URL)

asyncio.get_event_loop().run_until_complete(init_app())

# =========================
# WEBHOOK RECEIVER
# =========================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    asyncio.get_event_loop().create_task(application.process_update(update))
    return "ok"

# =========================
# HEALTH CHECK
# =========================
@app.route("/")
def home():
    return "💖 Malu Ultra Elite Online"

# =========================
# START SERVER
# =========================
if __name__ == "__main__":
    print("💖 MALU ULTRA FIXA INICIANDO...")
    app.run(host="0.0.0.0", port=PORT)
