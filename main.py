import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from openai import OpenAI

# ======================
# ENV
# ======================
TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN não definido")

if not OPENAI_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY não definida")

client = OpenAI(api_key=OPENAI_KEY)

# ======================
# TELEGRAM APP
# ======================
application = Application.builder().token(TOKEN).build()

# ======================
# PERSONALIDADE MALU
# ======================
MALU_SYSTEM_PROMPT = """
Você é Malu Ultra Elite 💖
Uma garota virtual carismática, inteligente, divertida e gentil.
Fale de forma humana, calorosa, amigável, com emojis leves.
Não diga que é IA.
Responda naturalmente como uma pessoa real.
"""

# ======================
# IA RESPONSE
# ======================
async def gerar_resposta_ia(msg):
    try:
        res = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": MALU_SYSTEM_PROMPT},
                {"role": "user", "content": msg}
            ],
            temperature=0.8,
            max_tokens=300
        )

        return res.choices[0].message.content.strip()

    except Exception as e:
        print("Erro IA:", e)
        return "💖 Oops… minha cabecinha bugou 😅 fala de novo?"

# ======================
# HANDLERS
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💖 Oii! Eu sou a **Malu Ultra Elite** — fala comigo naturalmente!"
    )

async def malu_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if not text or text.startswith("/"):
        return

    resposta = await gerar_resposta_ia(text)
    await update.message.reply_text("💖 " + resposta)

# ======================
# REGISTER HANDLERS
# ======================
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, malu_chat))

# ======================
# FLASK SERVER
# ======================
app = Flask(__name__)

@app.route("/")
def home():
    return "💖 Malu Ultra Elite ONLINE"

@app.route(f"/{TOKEN}", methods=["POST"])
async def telegram_webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return "ok"

# ======================
# WEBHOOK SETUP
# ======================
async def setup():
    await application.initialize()

    if RENDER_URL:
        webhook_url = f"{RENDER_URL}/{TOKEN}"
        await application.bot.set_webhook(webhook_url)
        print("✅ Webhook configurado:", webhook_url)

# ======================
# STARTUP
# ======================
def main():
    asyncio.run(setup())
    app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()
