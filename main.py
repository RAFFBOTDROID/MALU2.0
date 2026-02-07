import os
import requests
import nest_asyncio
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from flask import Flask
import threading
from collections import deque
import random

# --- Permite rodar corrotinas em loops já existentes ---
nest_asyncio.apply()

# --- CONFIGURAÇÃO ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "meta-llama/llama-3.2-3b-instruct:free"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Quantas mensagens do grupo a Manu vai "lembrar"
MEMORIA_MAX = 30
grupo_memoria = deque(maxlen=MEMORIA_MAX)

# Lista de stickers (IDs ou arquivos locais)
stickers = [
    "CAACAgUAAxkBAAEBQO5g1JZp7-3FAUO0k7fRk6HJx5KXgAACNAADVp29CpsuWZnyXvYEIAQ",
    "CAACAgUAAxkBAAEBQO9g1JjLx3r-WfyywI2tTk9GkpqV9AACOAADVp29CNZLzg6JhHltIAQ",
    # Adicione mais IDs de stickers válidos do Telegram
]

# --- FUNÇÃO DE CHAMADA À API ---
def gerar_resposta_ia(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    # Prepara o contexto com as últimas mensagens do grupo
    mensagens_contexto = [{"role": "system", "content": "Você é a Manu, alegre, carinhosa, simpática e divertida."}]
    for msg in grupo_memoria:
        mensagens_contexto.append({"role": "user", "content": msg})
    mensagens_contexto.append({"role": "user", "content": prompt})

    data = {
        "model": MODEL,
        "messages": mensagens_contexto,
        "max_tokens": 200,
        "temperature": 0.8
    }

    try:
        response = requests.post(OPENROUTER_URL, json=data, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        elif response.status_code == 429:
            return fallback_resposta(prompt)
        else:
            print("Erro OpenRouter:", response.status_code, response.text)
    except Exception as e:
        print("Erro na requisição:", e)

    return fallback_resposta(prompt)

# --- FUNÇÃO DE FALLBACK COM EMOJIS E STICKERS ---
def fallback_resposta(prompt):
    respostas = [
        "Humm 😄 legal!",
        "Entendi! 💖",
        "Que legal! 😍",
        "Ahhh que interessante 😄",
        "Que fofinho! 🥰",
        "Hmm, me conta mais! 😅",
        "Muito legal isso! 😎"
    ]
    resposta = random.choice(respostas)

    # 30% de chance de enviar sticker
    enviar_sticker = random.random() < 0.3
    sticker_id = random.choice(stickers) if stickers else None

    return {"text": resposta, "sticker": sticker_id if enviar_sticker else None}

# --- FUNÇÃO QUE TRATA MENSAGENS ---
async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if msg.reply_to_message:  # ignora replies
        return

    texto = msg.text.strip()
    if not texto:
        return

    # Adiciona no contexto do grupo
    grupo_memoria.append(texto)

    # Gera resposta
    resposta = gerar_resposta_ia(texto)

    # Fallback retorna dict com sticker opcional
    if isinstance(resposta, dict):
        await msg.reply_text(resposta["text"])
        if resposta.get("sticker"):
            try:
                await msg.reply_sticker(resposta["sticker"])
            except:
                pass
    else:
        await msg.reply_text(resposta)

# --- INICIALIZAÇÃO DO BOT ---
async def iniciar_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), processar_mensagem))
    print("Manu está online! 🤖💖")
    await app.run_polling()

# --- SERVIDOR WEB FAKE PARA RENDER ---
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
