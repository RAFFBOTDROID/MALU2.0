import os
import logging
import asyncio
from flask import Flask, request
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
    try:
        if not update.message or not update.message.text:
            return

        text = update.message.text.strip()
        user_id = update.message.from_user.id
        chat_type = update.message.chat.type

        logging.info(f"💬 Msg recebida ({chat_type}) de {update.message.from_user.username}: {text}")

        # Ignora comandos
        if text.startswith("/"):
            return

        # ================= GRUPO =================
        if chat_type in ["group", "supergroup"]:
            bot_username = (context.bot.username or "").lower()
            text_lower = text.lower()

            # Verifica se mencionou @botusername
            mentioned = f"@{bot_username}" in text_lower

            # Verifica se respondeu à Malu
            replied_to_bot = (
                update.message.reply_to_message
                and update.message.reply_to_message.from_user
                and update.message.reply_to_message.from_user.id == context.bot.id
            )

            if not mentioned and not replied_to_bot:
                logging.info("⛔ Ignorando mensagem do grupo (não mencionou nem respondeu ao bot)")
                return

        # ================= SALVAR MEMÓRIA =================
        save_memory(user_id, text)

        # ================= RESPONDER =================
        reply = ask_malu(user_id, text)
        logging.info(f"✅ Respondendo: {reply}")
        await update.message.reply_text(reply)

    except Exception:
        logging.exception("🔥 ERRO NA RESPOSTA")
        await update.message.reply_text("Buguei 😅 tenta de novo.")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, malu_reply))

# ================= EVENT LOOP =================
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# ================= FLASK =================
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Malu online 😘", 200

@flask_app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        logging.info("📩 Update recebido")
        update = Update.de_json(data, telegram_app.bot)
        asyncio.run_coroutine_threadsafe(telegram_app.process_update(update), loop)
    except Exception:
        logging.exception("🔥 ERRO COMPLETO NO WEBHOOK")
    return "ok", 200

# ================= STARTUP =================
async def setup():
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.delete_webhook(drop_pending_updates=True)
    await telegram_app.bot.set_webhook(url=WEBHOOK_URL, allowed_updates=["message"])
    print(f"✅ Webhook ativo: {WEBHOOK_URL}")

if __name__ == "__main__":
    loop.run_until_complete(setup())
    flask_app.run(host="0.0.0.0", port=PORT)
