import os
import logging
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("BOT_TOKEN")
GENAI_API_KEY = os.getenv("GENAI_API_KEY")

if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN não encontrado")
if not GENAI_API_KEY:
    raise RuntimeError("❌ GENAI_API_KEY não encontrado")

logging.basicConfig(level=logging.INFO)

# =========================
# PERSONALIDADE DA MALU
# =========================
SYSTEM_PROMPT = """
Você é Malu, uma IA feminina, simpática, divertida, inteligente e levemente provocante.
Fale de forma natural, amigável, brasileira e descontraída.
Responda curto quando possível.
Nunca diga que é um modelo de IA.
Nunca diga que é um bot.
Seja carismática e envolvente.
"""

# =========================
# MEMÓRIA SIMPLES
# =========================
memory = {}

def save_memory(user_id, text):
    memory.setdefault(user_id, [])
    memory[user_id].append(text)
    memory[user_id] = memory[user_id][-6:]

# =========================
# TELEGRAM BOT HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Oi 😘 eu sou a Malu. Pode falar comigo naturalmente."
    )

def ask_malu(user_id, text):
    history = "\n".join(memory.get(user_id, []))
    prompt = f"{SYSTEM_PROMPT}\nHistórico:\n{history}\n\nUsuário: {text}\nMalu:"

    response = genai.ChatCompletion.create(
        model="gemini-1.5",
        messages=[{"author":"user","content":prompt}],
        temperature=0.8,
        max_output_tokens=200,
        api_key=GENAI_API_KEY
    )

    return response.choices[0].message.content.strip()

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
        await update.message.reply_text("Deu um branco aqui 😅 tenta de novo.")

# =========================
# FLASK PING SERVER
# =========================
app_flask = Flask("ping_server")

@app_flask.route("/ping")
def ping():
    return "Malu está viva 😘", 200

def run_flask():
    app_flask.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# =========================
# MAIN TELEGRAM BOT
# =========================
def main():
    # Inicializa Telegram bot
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, malu_reply))

    # Start Flask server em outra thread
    Thread(target=run_flask).start()

    print("✅ Malu está online com Gemini Free e ping server...")
    app.run_polling()

if __name__ == "__main__":
    main()
