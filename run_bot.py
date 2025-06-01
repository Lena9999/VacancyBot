from telegram_interface.telegram_bot import TelegramBot
from config.config import BOT_TOKEN
import os

if __name__ == "__main__":
    print("🚀 Starting JobRadarBot...")
    data_path = os.path.join("data", "user_data.pickle")
    bot = TelegramBot(BOT_TOKEN, persistence_path=data_path)
    bot.run()
