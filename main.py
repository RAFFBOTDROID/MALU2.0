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
                        "Você é MALU, uma garota simpática, humana, divertida, carismática e educada. "
                        "Responda como pessoa real, SEM parecer robô, SEM ser invasiva."
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
        return "💖 Oops… buguei um pouquinho 😅 tenta de novo?"

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💖 Oii! Eu sou a **Malu Ultra Elite** — fala comigo!")

# =========================
# CHAT MALU — HUMANA
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

    # Anti-spam
    bloquear = ["http", "www", ".com", "promo", "cupom"]
    if any(b in t for b in bloquear):
        return

    # Chance humana (não flooda)
    import random
    if random.random() > 0.35:
        return

    resposta = ai_reply(text)
    await msg.reply_text(resposta)

# =========================
# HANDLERS
# =========================
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, malu))

# =========================
# WEBHOOK — SEM ERRO LOOP
# =========================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)

    async def process():
        await application.initialize()
        await application.process_update(Update.de_json(data, application.bot))

    asyncio.run(process())
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
async def setup():
    await application.initialize()
    await application.bot.set_webhook(WEBHOOK_URL)

if __name__ == "__main__":
    print("💖 MALU ULTRA FIXA INICIANDO...")
    asyncio.run(setup())
    app.run(host="0.0.0.0", port=PORT)
