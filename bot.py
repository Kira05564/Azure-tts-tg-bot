#!/usr/bin/env python3
import os
import asyncio
import tempfile
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import edge_tts
from pydub import AudioSegment

# Get token from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("Error: BOT_TOKEN environment variable not set")
    exit(1)

updater = Updater(token=BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Edge TTS voices
VOICE_MAP = {
    "male": "hi-IN-PrabhatNeural",
    "female": "hi-IN-SwaraNeural"
}

async def generate_tts(text: str, voice: str, output_file: str):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Hi! Commands:\n/tts female <text>\n/tts male <text>"
    )

def tts(update: Update, context: CallbackContext):
    if len(context.args) < 2:
        update.message.reply_text("Usage: /tts <male|female> <text>")
        return

    voice_type = context.args[0].lower()
    text = " ".join(context.args[1:])

    if voice_type not in VOICE_MAP:
        update.message.reply_text("Voice must be 'male' or 'female'")
        return

    update.message.reply_text("🎙 Generating voice...")

    tmp_dir = tempfile.gettempdir()
    output_file = os.path.join(tmp_dir, f"tts_{update.message.message_id}.mp3")

    # Run edge-tts
    asyncio.run(generate_tts(text, VOICE_MAP[voice_type], output_file))

    # Convert to ogg/opus for Telegram
    ogg_file = output_file.replace(".mp3", ".ogg")
    audio = AudioSegment.from_file(output_file, format="mp3")
    audio.export(ogg_file, format="ogg", codec="libopus")

    with open(ogg_file, "rb") as f:
        update.message.reply_voice(voice=f, caption=f"({voice_type} voice)")

    # Cleanup
    for f in [output_file, ogg_file]:
        if os.path.exists(f):
            os.remove(f)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("tts", tts))

def main():
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()