import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN não encontrado")
if not GEMINI_API_KEY:
    raise RuntimeError("❌ GEMINI_API_KEY não encontrado")
if not WEBHOOK_URL:
    raise RuntimeError("❌ WEBHOOK_URL não encontrado")

logging.basicConfig(level=logging.INFO)

# ================= GEMINI CLIENT =================
client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_PRIORITY = ["gemini-1.5-flash"]

SYSTEM_PROMPT = """
Você é Malu, uma IA feminina, simpática, divertida, inteligente e levemente provocante.
Fale como uma garota brasileira real, natural, carismática e envolvente.
Responda curto quando possível.
Nunca diga que é um modelo de IA.
Nunca diga que é um bot.
Seja charmosa, leve, engraçada e um pouco provocante.
"""

memory = {}

def save_memory(user_id, text):
    memory.setdefault(user_id, [])
    memory[user_id].append(text)
    memory[user_id] = memory[user_id][-6:]

def generate_with_fallback(prompt):
    for model_name in MODEL_PRIORITY:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "temperature": 0.85,
                    "max_output_tokens": 300
                }
            )
            return response.text.strip()
        except Exception as e:
            logging.warning(f"⚠️ Falhou {model_name}: {e}")

    return "Buguei 😅 tenta de novo."

def ask_malu(user_id, text):
    history = "\n".join(memory.get(user_id, []))

    prompt = f"""{SYSTEM_PROMPT}

Histórico:
{history}

Usuário: {text}
Malu:
"""
    return generate_with_fallback(prompt)

# ================= BOT =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Oi 😘 eu sou a Malu. Fala comigo.")

async def malu_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user_id = update.message.from_user.id

    if text.startswith("/"):
        return

    save_memory(user_id, text)

    try:
        reply = ask_malu(user_id, text)
        await update.message.reply_text(reply)
    except Exception as e:
        logging.error(e)
        await update.message.reply_text("Buguei 😅 tenta de novo.")

# ================= TELEGRAM APP =================
telegram_app = Application.builder().token(TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, malu_reply))

# ================= EVENT LOOP GLOBAL =================
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# ================= FLASK =================
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Malu online 😘", 200

@flask_app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)

    asyncio.run_coroutine_threadsafe(
        telegram_app.process_update(update),
        loop
    )

    return "ok", 200

# ================= MAIN =================
async def setup():
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.set_webhook(url=WEBHOOK_URL)
    print(f"✅ Webhook ativo em: {WEBHOOK_URL}")

if __name__ == "__main__":
    loop.run_until_complete(setup())

    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)
