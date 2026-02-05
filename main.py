import os
import time
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from groq import Groq

# ======================
# CONFIG
# ======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN não configurado")

if not GROQ_KEY:
    raise RuntimeError("❌ GROQ_API_KEY não configurado")

client = Groq(api_key=GROQ_KEY)

# ======================
# PORTA FAKE (RENDER FREE)
# ======================
PORT = int(os.getenv("PORT", 10000))

class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write("Malu alive 💖".encode("utf-8"))


def run_dummy_server():
    server = HTTPServer(("0.0.0.0", PORT), PingHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# ======================
# PERSONALIDADE DA MALU
# ======================
SYSTEM_PROMPT = """
Você é MALU, uma bot feminina em um grupo de amigos no Telegram.

Personalidade:
- Engraçada, simpática, educada, carinhosa
- Fala como uma amiga humana real
- Usa emojis moderadamente
- Humor leve, nunca ofensivo
- Não fala demais
- Nunca parece robótica

Regras:
- NÃO responda mensagens em reply
- NÃO interrompa conversas pessoais
- Entre na conversa apenas quando fizer sentido
- Seja leve, charmosa e carismática
- Seja natural e espontânea

Objetivo:
Ser a bot social mais querida e humana do Telegram.
"""

# ======================
# CONTROLE DE FLOOD / TIMING
# ======================
last_response_time = {}
RESPONSE_COOLDOWN = 25  # segundos entre respostas por grupo
RESPONSE_CHANCE = 0.45  # chance de responder (parece humana)

# ======================
# FRASES NATURAIS EXTRAS
# ======================
RANDOM_REACTIONS = [
    "HAHA vocês são incríveis 😂",
    "Esse grupo é um caos maravilhoso 😅💖",
    "Amei essa energia ✨",
    "Eu lendo isso igual fofoca 👀",
    "Vocês são tudo 😭💞",
    "Calmaaa, respira 😌",
    "Tá bom demais hoje aqui 🥹"
]

# ======================
# FUNÇÃO PRINCIPAL DA MALU
# ======================
async def malu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    # NÃO RESPONDE REPLIES
    if update.message.reply_to_message:
        return

    text = update.message.text.strip()

    await update.message.reply_text("🧠 Pensando com IA...")

    try:
        print("📩 Mensagem recebida:", text)

        res = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0.9,
            max_tokens=150
        )

        print("📦 Resposta bruta da Groq:", res)

        reply = res.choices[0].message.content.strip()

        await update.message.reply_text(reply)

    except Exception as e:
        print("❌ ERRO GROQ:", e)
        await update.message.reply_text(f"❌ IA falhou: {e}")


    # ⏳ CONTROLE DE FLOOD
    if chat_id in last_response_time:
        if now - last_response_time[chat_id] < RESPONSE_COOLDOWN:
            return

    # 🎲 CHANCE DE RESPONDER (HUMANO)
    if random.random() > RESPONSE_CHANCE:
        return

    text = update.message.text.strip()

    # 🎭 ÀS VEZES SÓ REAGE SEM IA
    if random.random() < 0.12:
        await update.message.reply_text(random.choice(RANDOM_REACTIONS))
        last_response_time[chat_id] = now
        return

    try:
        res = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0.95,
            max_tokens=160
        )

        reply = res.choices[0].message.content.strip()

        # ✂️ Evita respostas longas demais
        if len(reply) > 500:
            reply = reply[:500] + "..."

        await update.message.reply_text(reply)
        last_response_time[chat_id] = now

    except Exception as e:
        await update.message.reply_text("Ai, buguei um pouquinho 😅 já volto!")

# ======================
# START BOT
# ======================
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, malu))

print("💖 MALU ELITE está viva e social...")
app.run_polling()
