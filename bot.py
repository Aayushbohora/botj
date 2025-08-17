import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from datetime import datetime

# === CONFIG ===
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
DAILY_LIMIT = 50
SPAM_INTERVAL = 5  # seconds
FROZEN_TIME = 60 * 60  # 1 hour freeze

# User tracking
user_data = {}  # {user_id: {date:str, count:int, last_request:float, frozen_until:float}}

logging.basicConfig(level=logging.INFO)

# === /start and /help command ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    text = f"""👋 Hello {name}!

✨ Use me to create AI images with Pollinations AI.

📌 Command:
/paint <prompt>

🎨 Example:
/paint a car 🚗

⚡ Daily limit: {DAILY_LIMIT} images per user
🚫 Spammers are frozen for 1 hour

👨‍💻 Bot creator: @Nepomodz
Enjoy creating! 🌟"""
    await update.message.reply_text(text)

# === /paint command ===
async def paint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    prompt = " ".join(context.args)
    now = datetime.now().timestamp()

    if not prompt:
        await update.message.reply_text("❌ Please provide a prompt! Example: /paint a car")
        return

    # Initialize user data
    if user_id not in user_data or user_data[user_id]['date'] != datetime.now().strftime("%Y-%m-%d"):
        user_data[user_id] = {'date': datetime.now().strftime("%Y-%m-%d"), 'count': 0, 'last_request': 0, 'frozen_until': 0}

    u = user_data[user_id]

    # Freeze check
    if now < u['frozen_until']:
        await update.message.reply_text("⏳ You are frozen for spamming. Try again later.")
        return

    # Spam check
    if now - u['last_request'] < SPAM_INTERVAL:
        u['frozen_until'] = now + FROZEN_TIME
        await update.message.reply_text("🚫 Too many requests! You are frozen for 1 hour.")
        return

    u['last_request'] = now

    # Daily limit
    if u['count'] >= DAILY_LIMIT:
        await update.message.reply_text(f"⚡ You have reached your daily limit of {DAILY_LIMIT} images. Come back tomorrow!")
        return

    u['count'] += 1

    await update.message.reply_text(f"🎨 Generating your image for: {prompt} ...")

    # Fetch image
    try:
        image_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
        await context.bot.send_photo(chat_id=chat_id, photo=image_url, caption=f"✨ Here’s your image for: {prompt}\n⚡ ({u['count']}/{DAILY_LIMIT} today)")
    except Exception as e:
        await update.message.reply_text("❌ Failed to generate image. Try again later.")
        print(e)

# === THANK ADMIN WHEN ADDED TO GROUP ===
async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.is_bot:
            await update.message.reply_text(f"🙏 Thanks Admin for adding me here!\nUse /paint <prompt> to create AI art 🎨")

# === MAIN ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", start))
app.add_handler(CommandHandler("paint", paint))
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))

print("Bot is running...")
app.run_polling()
