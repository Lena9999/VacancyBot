import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PASSWORD = os.getenv("DB_PASSWORD")

if not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN is missing! Add it to .env or set it as an environment variable.")
