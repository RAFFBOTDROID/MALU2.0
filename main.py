import os
import requests
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
PORT = int(os.getenv("PORT", 10000))

WEBHOOK_URL = f"https://malu2-0.onrender.com/{TOKEN}"

bot = Bot(token=TOKEN)
app = Flask(__name__)

application = Application.builder().token(TOKEN).build()

# =========================
# IA GROQ — MALU
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
                        "Você é MALU, uma garota simpática, educada, engraçada, humana e carismática. "
                        "Você conversa naturalmente em grupos, SEM ser invasiva, SEM responder replies."
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
        return "💖 Ops… buguei um pouquinho, tenta de novo?"

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💖 Oi! Eu sou a **Malu Ultra Elite**. Me chama que eu respondo!")

# =========================
# CHAT MALU (SEM REPLY)
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

    # Malu só fala se chamarem ou conversa natural
    gatilhos = ["malu", "oi malu", "hey malu", "fala malu"]

    if any(g in text.lower() for g in gatilhos) or len(text) > 12:
        resposta = ai_reply(text)
        await msg.reply_text(resposta)

# =========================
# HANDLERS
# =========================
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, malu))

# =========================
# WEBHOOK ENDPOINT
# =========================
@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, bot)
    await application.process_update(update)
    return "ok"

# =========================
# HEALTH CHECK
# =========================
@app.route("/")
def home():
    return "💖 Malu Ultra Elite Online"

# =========================
# START SERVER + WEBHOOK
# =========================
if __name__ == "__main__":
    print("💖 MALU ULTRA FIXA INICIANDO")

    bot.set_webhook(WEBHOOK_URL)

    app.run(host="0.0.0.0", port=PORT)
