import os
import logging
import asyncio
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 8080))

if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN não encontrado")
if not GEMINI_API_KEY:
    raise RuntimeError("❌ GEMINI_API_KEY não encontrado")
if not WEBHOOK_URL:
    raise RuntimeError("❌ WEBHOOK_URL não encontrado")

logging.basicConfig(level=logging.INFO)

# ================= GEMINI =================
genai.configure(api_key=GEMINI_API_KEY)
MODEL_PRIORITY = ["models/gemini-1.5-flash"]

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
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                prompt,
                generation_config={"temperature": 0.85, "max_output_tokens": 300}
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

# ================= TELEGRAM =================
telegram_app = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Oi 😘 eu sou a Malu. Fala comigo.")

async def malu_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user_id = update.message.from_user.id
    chat_type = update.message.chat.type
    logging.info(f"💬 Msg recebida ({chat_type}): {text}")

    if text.startswith("/"):
        return

    # Responde em grupos somente se mencionado ou respondido
    if chat_type in ["group", "supergroup"]:
        bot_username = (context.bot.username or "").lower()
        mentioned_in_text = f"@{bot_username}" in text.lower()
        replied_to_bot = (
            update.message.reply_to_message
            and update.message.reply_to_message.from_user
            and update.message.reply_to_message.from_user.is_bot
        )
        if not mentioned_in_text and not replied_to_bot:
            return

    save_memory(user_id, text)
    reply = ask_malu(user_id, text)
    await update.message.reply_text(reply)

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, malu_reply))

# ================= FASTAPI =================
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "Malu online 😘"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}

# ================= STARTUP =================
async def setup():
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.delete_webhook(drop_pending_updates=True)
    await telegram_app.bot.set_webhook(url=WEBHOOK_URL, allowed_updates=["message"])
    print(f"✅ Webhook ativo: {WEBHOOK_URL}")

asyncio.run(setup())
