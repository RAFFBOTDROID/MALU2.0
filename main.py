import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# --- CONFIGURAÇÃO ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "meta-llama/llama-3.2-3b-instruct:free"  # modelo gratuito

# Endpoint do OpenRouter para chat
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
    response = requests.post(OPENROUTER_URL, json=data, headers=headers)
    if response.status_code == 200:
        resposta = response.json()
        return resposta["choices"][0]["message"]["content"]
    else:
        return "Desculpa, deu um errinho 😅 tente novamente."

# --- FUNÇÃO QUE TRATA AS MENSAGENS ---
async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    # Ignora se é uma resposta (*reply*) para outro membro
    if msg.reply_to_message:
        return

    texto = msg.text.strip()
    # Apenas responde se houver texto
    if texto:
        # Gera resposta da IA
        reply = gerar_resposta_ia(texto)
        await msg.reply_text(reply)

# --- INICIALIZAÇÃO DO BOT ---
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), processar_mensagem))

    print("Manu está online! 🤖💖")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
