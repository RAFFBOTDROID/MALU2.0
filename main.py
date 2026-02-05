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
# PERSONALIDADE MALU
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
"""

# ======================
# CONTROLE HUMANO
# ======================
last_response_time = {}
RESPONSE_COOLDOWN = 20
RESPONSE_CHANCE = 0.55

RANDOM_REACTIONS = [
    "HAHA vocês são caóticos demais 😂",
    "Esse grupo é simplesmente perfeito 😅💖",
    "Eu lendo isso igual fofoca 👀",
    "Amei essa energiaaaa ✨",
    "Vocês são tudo 😭💞",
    "Calmaaa, respira 😌",
]

# ======================
# FUNÇÃO PRINCIPAL
# ======================
async def malu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    # ❌ NÃO RESPONDE REPLIES
    if update.message.reply_to_message:
        return

    chat_id = update.message.chat_id
    text = update.message.text.strip()
    now = time.time()

    # ⏳ ANTI FLOOD
    if chat_id in last_response_time:
        if now - last_response_time[chat_id] < RESPONSE_COOLDOWN:
            return

    # 🎲 CHANCE HUMANA
    if random.random() > RESPONSE_CHANCE:
        return

    # 🎭 ÀS VEZES REAGE SEM IA
    if random.random() < 0.15:
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
            temperature=0.9,
            max_tokens=160
        )

        reply = res.choices[0].message.content.strip()

        if len(reply) > 450:
            reply = reply[:450] + "..."

        await update.message.reply_text(reply)
        last_response_time[chat_id] = now

    except Exception as e:
        print("❌ Groq error:", e)
        await update.message.reply_text("Ai buguei um pouquinho 😅 já volto!")

# ======================
# START BOT
# ======================
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, malu))

print("💖 MALU ELITE ONLINE...")
app.run_polling()
