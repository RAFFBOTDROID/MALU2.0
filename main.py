import os
import asyncio
import openai
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN não definido")

if not OPENAI_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY não definida")

openai.api_key = OPENAI_KEY

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
Responda naturalmente.
"""

# ======================
# IA RESPONSE
# ======================
async def gerar_resposta_ia(msg):
    try:
        res = await asyncio.to_thread(
            openai.ChatCompletion.create,
            model="gpt-4",
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

    # Ignorar comandos
    if text.startswith("/"):
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
# STARTUP
# ======================
async def setup_webhook():
    url = os.getenv("RENDER_EXTERNAL_URL")
    if url:
        await application.bot.set_webhook(f"{url}/{TOKEN}")
        print("✅ Webhook configurado:", url)

def run():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(application.initialize())
    loop.run_until_complete(setup_webhook())

    app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    run()
