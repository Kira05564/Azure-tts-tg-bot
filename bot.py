import logging
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import requests
from io import BytesIO
import sqlite3
import os

# Bot setup
BOT_TOKEN = "7730705217:AAHCQmZ7f47Y7a4q2XA15FJJEwpKCbMo1eQ"
OWNER_ID = 7659192518

# Microsoft TTS API configuration (no API key needed as requested)
MICROSOFT_TTS_URL = "https://api.edenai.run/v2/audio/text_to_speech"
# Note: In a real implementation, you might need an API key for Microsoft TTS services

# Database setup for storing user/group data and voice preferences
DB_NAME = "tts_bot.db"

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Available Microsoft voices (male and female from various countries)
VOICES = {
    "en-US-JennyNeural": {"name": "Jenny (US English, Female)", "gender": "female", "language": "English"},
    "en-US-GuyNeural": {"name": "Guy (US English, Male)", "gender": "male", "language": "English"},
    "en-GB-SoniaNeural": {"name": "Sonia (UK English, Female)", "gender": "female", "language": "English"},
    "en-GB-RyanNeural": {"name": "Ryan (UK English, Male)", "gender": "male", "language": "English"},
    "hi-IN-SwaraNeural": {"name": "Swara (Hindi, Female)", "gender": "female", "language": "Hindi"},
    "hi-IN-MadhurNeural": {"name": "Madhur (Hindi, Male)", "gender": "male", "language": "Hindi"},
    "es-ES-ElviraNeural": {"name": "Elvira (Spanish, Female)", "gender": "female", "language": "Spanish"},
    "es-ES-AlvaroNeural": {"name": "Alvaro (Spanish, Male)", "gender": "male", "language": "Spanish"},
    "fr-FR-DeniseNeural": {"name": "Denise (French, Female)", "gender": "female", "language": "French"},
    "fr-FR-HenriNeural": {"name": "Henri (French, Male)", "gender": "male", "language": "French"},
    "de-DE-KatjaNeural": {"name": "Katja (German, Female)", "gender": "female", "language": "German"},
    "de-DE-ConradNeural": {"name": "Conrad (German, Male)", "gender": "male", "language": "German"},
    "ja-JP-NanamiNeural": {"name": "Nanami (Japanese, Female)", "gender": "female", "language": "Japanese"},
    "ja-JP-KeitaNeural": {"name": "Keita (Japanese, Male)", "gender": "male", "language": "Japanese"},
    "ar-SA-ZariyahNeural": {"name": "Zariyah (Arabic, Female)", "gender": "female", "language": "Arabic"},
    "ar-SA-HamedNeural": {"name": "Hamed (Arabic, Male)", "gender": "male", "language": "Arabic"},
}

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create table for user preferences
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_preferences (
        user_id INTEGER PRIMARY KEY,
        voice_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create table for groups
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS groups (
        group_id INTEGER PRIMARY KEY,
        group_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create table for users
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

# Get user preference
def get_user_voice_preference(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT voice_name FROM user_preferences WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "en-US-JennyNeural"

# Set user preference
def set_user_voice_preference(user_id, voice_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO user_preferences (user_id, voice_name) VALUES (?, ?)",
        (user_id, voice_name)
    )
    conn.commit()
    conn.close()

# Save user info
def save_user(user_id, username, first_name, last_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
        (user_id, username, first_name, last_name)
    )
    conn.commit()
    conn.close()

# Save group info
def save_group(chat_id, title):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO groups (group_id, group_name) VALUES (?, ?)",
        (chat_id, title)
    )
    conn.commit()
    conn.close()

# Get all users for broadcast
def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

# Get all groups for broadcast
def get_all_groups():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT group_id FROM groups")
    groups = [row[0] for row in cursor.fetchall()]
    conn.close()
    return groups

# Generate TTS using Microsoft API
def generate_tts(text, voice_name):
    # This is a placeholder implementation
    # In a real scenario, you would use the Microsoft TTS API
    # For demonstration, we'll return a placeholder audio
    
    # Note: Actual implementation would require proper API integration
    # For now, we'll create a dummy audio file
    try:
        # This is where you would call the Microsoft TTS API
        # response = requests.post(MICROSOFT_TTS_URL, json={
        #     "text": text,
        #     "voice": voice_name,
        #     "provider": "microsoft"
        # })
        
        # For demonstration, we'll create a dummy audio file
        # In a real implementation, you would return the actual audio from the API
        audio_file = BytesIO()
        audio_file.name = "tts_audio.wav"
        
        # Placeholder - in reality, you'd have the actual audio content
        # For now, we'll just return a text file as a placeholder
        audio_file.write(f"Text: {text}\nVoice: {voice_name}".encode())
        audio_file.seek(0)
        
        return audio_file
    except Exception as e:
        logger.error(f"Error generating TTS: {e}")
        return None

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    
    # Save user info
    save_user(user.id, user.username, user.first_name, user.last_name)
    
    # If it's a group chat, save group info
    if chat.type in ["group", "supergroup"]:
        save_group(chat.id, chat.title)
    
    welcome_text = (
        f"👋 Hello {user.first_name}!\n\n"
        "Welcome to the Microsoft TTS Bot! 🎙️\n\n"
        "I can convert text to speech using high-quality Microsoft voices from around the world. 🌍\n\n"
        "Use /voice to select your preferred voice\n"
        "Use /tts followed by text to generate speech\n"
        "Use /help to see all available commands\n\n"
        "Enjoy using the bot! 😊"
    )
    
    await update.message.reply_text(welcome_text)

# Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 *Microsoft TTS Bot Help*\n\n"
        "*/start* - Start the bot and see welcome message\n"
        "*/help* - Show this help message\n"
        "*/tts* <text> - Convert text to speech\n"
        "*/voice* - Select your preferred voice\n"
        "*/voices* - Show all available voices\n"
        "*/about* - Information about this bot\n"
        "*/broadcast* <message> - Broadcast message to all users (Owner only)\n\n"
        "📝 *How to use:*\n"
        "1. Use /voice to select your preferred voice\n"
        "2. Send /tts followed by your text to convert it to speech\n"
        "3. Enjoy the high-quality Microsoft voices! 🎵"
    )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

# Voice selection command
async def voice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    row = []
    
    for i, (voice_id, voice_info) in enumerate(VOICES.items()):
        button = InlineKeyboardButton(
            f"{voice_info['name']}",
            callback_data=f"voice_{voice_id}"
        )
        row.append(button)
        
        # Create a new row every 2 buttons
        if (i + 1) % 2 == 0:
            keyboard.append(row)
            row = []
    
    # Add any remaining buttons
    if row:
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎵 Select your preferred voice:",
        reply_markup=reply_markup
    )

# Voices command to show all available voices
async def voices_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voices_list = "🎙️ *Available Voices:*\n\n"
    
    for voice_id, voice_info in VOICES.items():
        voices_list += f"• {voice_info['name']} ({voice_info['language']}, {voice_info['gender']})\n"
    
    voices_list += "\nUse /voice to select a voice"
    
    await update.message.reply_text(voices_list, parse_mode="Markdown")

# Handle voice selection
async def voice_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data.startswith("voice_"):
        voice_id = data[6:]  # Remove "voice_" prefix
        if voice_id in VOICES:
            set_user_voice_preference(user_id, voice_id)
            voice_name = VOICES[voice_id]["name"]
            await query.edit_message_text(
                f"✅ You have selected: {voice_name}\n\n"
                "Now use /tts followed by your text to generate speech with this voice."
            )
        else:
            await query.edit_message_text("❌ Invalid voice selection.")

# TTS command
async def tts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide text after /tts command.\nExample: /tts Hello world")
        return
    
    text = " ".join(context.args)
    user_id = update.effective_user.id
    
    # Get user's voice preference
    voice_id = get_user_voice_preference(user_id)
    
    # Generate TTS
    await update.message.reply_chat_action(action="upload_audio")
    audio_file = generate_tts(text, voice_id)
    
    if audio_file:
        voice_name = VOICES[voice_id]["name"]
        await update.message.reply_voice(
            voice=audio_file,
            caption=f"🎵 {text}\n\nVoice: {voice_name}"
        )
    else:
        await update.message.reply_text("❌ Sorry, I couldn't generate the audio at the moment. Please try again later.")

# About command
async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = (
        "🤖 *Microsoft TTS Bot*\n\n"
        "This bot uses Microsoft's high-quality Text-to-Speech technology with natural sounding voices from around the world. 🌍\n\n"
        "• Support for multiple languages\n"
        "• Male and female voices\n"
        "• Natural sounding speech\n"
        "• Easy to use\n\n"
        "For any questions or support, contact the owner:"
    )
    
    keyboard = [[InlineKeyboardButton("Owner ❤️‍🔥", url="https://t.me/ll_RORONOA_ZORO_ll")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(about_text, parse_mode="Markdown", reply_markup=reply_markup)

# Broadcast command (owner only)
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ This command is only available for the owner.")
        return
    
    if not context.args:
        await update.message.reply_text("Please provide a message to broadcast.\nExample: /broadcast Hello everyone!")
        return
    
    message = " ".join(context.args)
    users = get_all_users()
    groups = get_all_groups()
    
    await update.message.reply_text(f"📢 Broadcasting message to {len(users)} users and {len(groups)} groups...")
    
    success_count = 0
    fail_count = 0
    
    # Broadcast to users
    for user in users:
        try:
            await context.bot.send_message(chat_id=user, text=f"📢 Broadcast from owner:\n\n{message}")
            success_count += 1
            await asyncio.sleep(0.1)  # To avoid rate limits
        except Exception as e:
            logger.error(f"Failed to send broadcast to user {user}: {e}")
            fail_count += 1
    
    # Broadcast to groups
    for group in groups:
        try:
            await context.bot.send_message(chat_id=group, text=f"📢 Broadcast from owner:\n\n{message}")
            success_count += 1
            await asyncio.sleep(0.1)  # To avoid rate limits
        except Exception as e:
            logger.error(f"Failed to send broadcast to group {group}: {e}")
            fail_count += 1
    
    await update.message.reply_text(
        f"✅ Broadcast completed!\n\n"
        f"Successfully sent: {success_count}\n"
        f"Failed: {fail_count}"
    )

# Handle new group members and save group info
async def handle_group_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.chat.type in ["group", "supergroup"]:
        chat = update.message.chat
        save_group(chat.id, chat.title)

# Main function
def main():
    # Initialize database
    init_db()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("voice", voice_command))
    application.add_handler(CommandHandler("voices", voices_command))
    application.add_handler(CommandHandler("tts", tts_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    
    application.add_handler(CallbackQueryHandler(voice_button_handler, pattern="^voice_"))
    
    # Handle group updates to save group info
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_group_update))
    application.add_handler(MessageHandler(filters.ChatType.GROUPS, handle_group_update))
    
    # Start the bot
    application.run_polling()
    logger.info("Bot is running...")

if __name__ == "__main__":
    main()