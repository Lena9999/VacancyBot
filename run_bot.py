from telegram_interface.telegram_bot import TelegramBot
from config.config import BOT_TOKEN
import os

if __name__ == "__main__":
    print("🚀 Starting JobRadarBot...")
    bot = TelegramBot(BOT_TOKEN)
    bot.run()
