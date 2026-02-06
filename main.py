import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN não encontrado")
if not GROQ_API_KEY:
    raise RuntimeError("❌ GROQ_API_KEY não encontrado")

client = Groq(api_key=GROQ_API_KEY)

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
# IA GROQ RESPONSE
# =========================
def ask_malu(user_id, text):
    history = "\n".join(memory.get(user_id, []))

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Histórico:\n{history}\n\nUsuário: {text}"}
    ]

    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        temperature=0.8,
        max_tokens=200,
    )

    return completion.choices[0].message.content.strip()

# =========================
# RESPONDER AUTOMÁTICO
# =========================
async def malu_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    user_id = update.message.from_user.id

    # Ignorar comandos
    if text.startswith("/"):
        return

    save_memory(user_id, text)

    try:
        reply = ask_malu(user_id, text)
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text("Deu um branco aqui 😅 tenta de novo.")

# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, malu_reply))

    print("✅ Malu está online...")
    app.run_polling()

if __name__ == "__main__":
    main()
