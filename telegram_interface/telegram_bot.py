from telegram import Update
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    PicklePersistence,
    CallbackQueryHandler,
)
from datetime import datetime
import json
from .job_form_template.form_parser import parse_form
from .skill_collector import AddSkillsDialog
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PARSED_DATA_DIR = PROJECT_ROOT / "data" / \
    "bot_user_data" / "parsed_user_data"
CANDIDATE_FORM_DIR = PROJECT_ROOT / "data" / "bot_user_data" / "candidate_form"
TEMPLATE_PATH = PROJECT_ROOT / "telegram_interface" / \
    "job_form_template" / "job_form_template.txt"


class TelegramBot:
    CALLBACK_DOWNLOAD = "download_template"

    def __init__(self, token: str, persistence_path: str = "user_data.pickle"):
        self.token = token
        self.persistence_path = persistence_path
        persistence = PicklePersistence(filepath=self.persistence_path)
        self.application = (
            Application.builder().token(self.token).persistence(persistence).build()
        )
        self.skills_dialog = AddSkillsDialog(
            persistence_path=self.persistence_path)
        self._register_handlers()

    def _register_handlers(self) -> None:
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler(
            "fill_form", self.ask_user_to_fill_form))
        self.application.add_handler(
            CommandHandler("view_form", self.view_form))
        self.application.add_handler(CallbackQueryHandler(
            self.send_template_button, pattern=f"^{self.CALLBACK_DOWNLOAD}$"))
        self.application.add_handler(MessageHandler(
            filters.Document.ALL & ~filters.COMMAND, self.process_uploaded_form))
        self.application.add_handler(self.skills_dialog.get_handler())
        self.application.add_handler(CommandHandler(
            "add_skills", self.start_skills_dialog))
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, self.echo))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        await update.message.reply_text(
            f"Hello, {user.first_name}! I am your new bot. Use /add_skills to add your skills to your profile, "
            "or /fill_form to submit a job preferences form."
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "I can help you manage your skills profile. Available commands:\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/add_skills - Add new skills to your profile\n"
            "/fill_form - Download and fill out a job preferences form\n"
            "/view_form - View your latest submitted form"
        )

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(update.message.text)

    # form handling

    async def ask_user_to_fill_form(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(
            "Download form template", callback_data=self.CALLBACK_DOWNLOAD)]])
        await update.message.reply_text(
            "Please download the form template, fill it out, and send it back to me.",
            reply_markup=keyboard,
        )

    async def send_template_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        file_path_str = str(TEMPLATE_PATH.resolve())
        print(f"📂 Sending file: {file_path_str}")

        if not os.path.isfile(file_path_str):
            await query.message.reply_text("⚠️ File not found. Check the path!")
            return

        with open(file_path_str, "rb") as f:
            await query.message.reply_document(document=InputFile(f, filename=TEMPLATE_PATH.name))

    async def process_uploaded_form(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        doc = update.message.document
        user_id = update.effective_user.id

        if not doc.mime_type.startswith("text/"):
            await update.message.reply_text("Please send a text file (.txt) with the filled form.")
            return

        CANDIDATE_FORM_DIR.mkdir(parents=True, exist_ok=True)
        user_forms_path = CANDIDATE_FORM_DIR / f"{user_id}.txt"

        telegram_file = await doc.get_file()
        await telegram_file.download_to_drive(custom_path=str(user_forms_path))

        try:
            with open(user_forms_path, "r", encoding="utf-8") as f:
                form_text = f.read()

            parsed_data = parse_form(form_text)
            if not parsed_data:
                await update.message.reply_text("The form is empty or incorrectly formatted. Please use the provided template.")
                return

            PARSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
            parsed_user_data_file = PARSED_DATA_DIR / \
                f"{user_id}.json"
            with open(parsed_user_data_file, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, ensure_ascii=False, indent=4)

            await update.message.reply_text(
                f"Your form has been successfully processed and saved."
                "You can view it using the /view_form command."
            )
        except Exception as e:
            await update.message.reply_text(
                f"Error processing your form. Please ensure the form follows the provided template and is encoded in UTF-8."
            )

    async def view_form(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        file_path = CANDIDATE_FORM_DIR / f"{user_id}.txt"

        if not file_path.exists():
            await update.message.reply_text("No form found. Please use /fill_form first.")
            return

        with open(file_path, "rb") as f:
            await update.message.reply_document(
                document=InputFile(f, filename="job_form.txt")
            )

    async def start_skills_dialog(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.skills_dialog.send_add_skills_button(update, context)

    def run(self) -> None:
        self.application.run_polling()
