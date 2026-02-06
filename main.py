import os
import requests
import nest_asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from flask import Flask
import threading

# Permite rodar corrotinas em loops já existentes
nest_asyncio.apply()

# --- CONFIGURAÇÃO ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "meta-llama/llama-3.2-3b-instruct:free"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# --- FUNÇÃO DE CHAMADA À API ---
def gerar_resposta_ia(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Você é a Manu, um bot alegre, simpático, carinhoso e natural."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 200,
        "temperature": 0.7
    }
    try:
        response = requests.post(OPENROUTER_URL, json=data, headers=headers, timeout=20)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
    except:
        pass
    return "Desculpa, deu um errinho 😅 tente novamente."

# --- FUNÇÃO QUE TRATA MENSAGENS ---
async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if msg.reply_to_message:  # ignora replies
        return
    texto = msg.text.strip()
    if texto:
        reply = gerar_resposta_ia(texto)
        await msg.reply_text(reply)

# --- INICIALIZAÇÃO DO BOT ---
async def iniciar_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), processar_mensagem))
    print("Manu está online! 🤖💖")
    await app.run_polling()

# --- SERVIDOR WEB FAKE (PORTA PARA O RENDER) ---
flask_app = Flask("ManuFakeWeb")

@flask_app.route("/")
def home():
    return "Manu Telegram Bot está online! 🤖💖"

def run_flask():
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

threading.Thread(target=run_flask).start()

# --- START ---
if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(iniciar_bot())
    except RuntimeError as e:
        if "already running" in str(e):
            asyncio.get_event_loop().create_task(iniciar_bot())
