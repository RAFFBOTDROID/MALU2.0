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
                        "Você é MALU, uma garota simpática, educada, humana, divertida e carismática. "
                        "Fale como amiga real. NÃO responda mensagens em reply. NÃO seja invasiva."
                    )
                },
                {"role": "user", "content": text}
            ],
            "temperature": 0.8,
            "max_tokens": 300
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
# FALLBACK SE IA CAIR
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

    t = text.lower()

    # Ignorar mensagens muito curtas
    if len(t) < 4:
        return

    # Chance de resposta para não floodar
    import random
    chance = 0.35  # 35% chance de responder
    if random.random() > chance:
        return

    # Ignorar mensagens automáticas/spam
    bloquear = ["http", "www", ".com", "promo", "cupom"]
    if any(b in t for b in bloquear):
        return

    resposta = ai_reply(text)
    await msg.reply_text(resposta)


# =========================
# HANDLERS
# =========================
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, malu))

# =========================
# WEBHOOK RECEIVER (FIX DEFINITIVO)
# =========================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)

    async def process():
        await application.initialize()
        await application.process_update(update)

    asyncio.run(process())

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
    await application.initialize()
    await application.bot.set_webhook(WEBHOOK_URL)

# =========================
# START SERVER
# =========================
if __name__ == "__main__":
    print("💖 MALU ULTRA FIXA INICIANDO...")

    asyncio.run(setup_webhook())

    app.run(host="0.0.0.0", port=PORT)
