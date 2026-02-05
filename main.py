import os
import asyncio
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# =========================
# CONFIG
# =========================
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
                        "Você é MALU, uma garota simpática, educada, humana, carismática, divertida e charmosa. "
                        "Fale como amiga real. NÃO seja invasiva. NÃO responda mensagens em reply."
                    )
                },
                {"role": "user", "content": text}
            ],
            "temperature": 0.8,
            "max_tokens": 350
        }

        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )

        data = r.json()

        if "choices" in data:
            return data["choices"][0]["message"]["content"]

        return malu_fallback(text)

    except:
        return malu_fallback(text)

# =========================
# FALLBACK — SE IA CAIR
# =========================
import random

def malu_fallback(text):
    respostas = [
        "💖 Eu tô aqui com você… fala mais 🥺",
        "😏 Hmmm, interessante… continua.",
        "🔥 Você fala bonito demais.",
        "👀 Eu vi isso hein…",
        "💋 Se continuar assim, eu me apaixono.",
        "😈 Eu gosto quando você fala comigo.",
        "💞 Você é uma boa companhia."
    ]

    t = text.lower()

    if "oi" in t:
        return "💖 Oii amor, tava esperando você 😘"
    if "bom dia" in t:
        return "☀️ Bom diaaa, coisa linda 💕"
    if "boa noite" in t:
        return "🌙 Boa noite, dorme pensando em mim 😌"
    if "te amo" in t:
        return "💞 Eu amo sua atenção… continua comigo."

    return random.choice(respostas)

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💖 Oii! Eu sou a **Malu Ultra Elite** — fala comigo!"
    )

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

    # Responder se chamar ou se texto for maior
    if any(g in text.lower() for g in gatilhos) or len(text) > 15:
        resposta = ai_reply(text)
        await msg.reply_text(resposta)

# =========================
# HANDLERS
# =========================
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, malu))

# =========================
# WEBHOOK RECEIVER (SEM BUG DE EVENT LOOP)
# =========================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)

    update = Update.de_json(data, application.bot)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(application.process_update(update))
    loop.close()

    return "ok"

# =========================
# HEALTH CHECK
# =========================
@app.route("/")
def home():
    return "💖 Malu Ultra Elite Online"

# =========================
# SET WEBHOOK
# =========================
async def setup_webhook():
    await application.bot.set_webhook(WEBHOOK_URL)

# =========================
# START SERVER
# =========================
if __name__ == "__main__":
    print("💖 MALU ULTRA FIXA INICIANDO...")

    asyncio.run(setup_webhook())

    app.run(host="0.0.0.0", port=PORT)
