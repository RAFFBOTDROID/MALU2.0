import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from groq import Groq

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_KEY)

SYSTEM_PROMPT = """
Você é MALU, uma bot feminina em um grupo de amigos no Telegram.

Personalidade:
- Engraçada
- Simpática
- Muito educada
- Carinhosa
- Humana
- Fala como amiga real
- Usa emojis moderadamente

Comportamento:
- NÃO se intrometa em replies
- NÃO interrompa conversas pessoais
- Seja natural e respeitosa
- Entre na conversa só quando fizer sentido
- Nunca pareça robótica

Objetivo:
Ser a bot social mais querida e humana do Telegram.
"""

async def malu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    # ❌ NÃO RESPONDE REPLIES
    if update.message.reply_to_message:
        return

    user_text = update.message.text

    try:
        res = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            temperature=0.9,
            max_tokens=180
        )

        reply = res.choices[0].message.content

        # Evita respostas muito longas
        if len(reply) > 600:
            reply = reply[:600] + "..."

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text("Ai, deu um bugzinho aqui 😅 mas já volto!")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, malu))

print("💖 MALU está viva e social...")
app.run_polling()
