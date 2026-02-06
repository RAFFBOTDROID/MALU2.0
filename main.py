import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 8443))  # PTB webhook padrão

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
            model = genai.models.get(model_name)
            response = model.generate_text(
                prompt,
                temperature=0.85,
                max_output_tokens=300
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

        logging.info(f"💬 Msg recebida ({chat_type}): {text}")

        # Ignora comandos
        if text.startswith("/"):
            return

        # Grupos: só responde se mencionado ou respondido
        if chat_type in ["group", "supergroup"]:
            bot_username = (context.bot.username or "").lower()
            mentioned = f"@{bot_username}" in text.lower()
            replied_to_bot = (
                update.message.reply_to_message
                and update.message.reply_to_message.from_user
                and update.message.reply_to_message.from_user.is_bot
            )
            if not mentioned and not replied_to_bot:
                return

        save_memory(user_id, text)
        reply = ask_malu(user_id, text)
        await update.message.reply_text(reply)

    except Exception:
        logging.exception("🔥 ERRO NA RESPOSTA")
        await update.message.reply_text("Buguei 😅 tenta de novo.")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, malu_reply))

# ================= START WEBHOOK =================
if __name__ == "__main__":
    telegram_app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )
