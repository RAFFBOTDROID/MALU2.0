import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("BOT_TOKEN")
GENAI_API_KEY = os.getenv("GENAI_API_KEY")  # API Key do Google Gemini Free

if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN não encontrado")
if not GENAI_API_KEY:
    raise RuntimeError("❌ GENAI_API_KEY não encontrado")

genai.api_key = GENAI_API_KEY

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
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Oi 😘 eu sou a Malu. Pode falar comigo naturalmente."
    )

# =========================
# IA GEMINI RESPONSE
# =========================
def ask_malu(user_id, text):
    history = "\n".join(memory.get(user_id, []))

    # Mensagem completa
    prompt = f"{SYSTEM_PROMPT}\nHistórico:\n{history}\n\nUsuário: {text}\nMalu:"

    response = genai.chat.create(
        model="gemini-1.5",  # Modelo gratuito Gemini Free
        messages=[{"author": "user", "content": prompt}],
        temperature=0.8,
        max_output_tokens=200
    )

    # O retorno do Gemini Free vem em response.last
    return response.last if hasattr(response, "last") else response.output[0].content

# =========================
# RESPONDER AUTOMÁTICO
# =========================
async def malu_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user_id = update.message.from_user.id

    # Ignorar comandos
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
# MAIN
# =========================
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, malu_reply))

    print("✅ Malu está online com Gemini Free...")
    app.run_polling()

if __name__ == "__main__":
    main()
