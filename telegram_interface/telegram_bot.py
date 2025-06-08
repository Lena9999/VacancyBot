from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)
from search_handler.searcher import search_vacancies_by_params_hh
import json
from .job_form_template.form_parser import parse_form
from pathlib import Path
import os
from vacancy_site_apis.hh_api import HHClient

"""
Module: telegram_interface.telegram_bot

Purpose:
--------
Implements the Telegram bot interface for VacancyBot. This class handles user interaction,
form collection and parsing, and job search operations by integrating with the HeadHunter (hh.ru) API.

Key Components:
---------------
- Directories used for data:
    - `CANDIDATE_FORM_DIR`: Stores uploaded raw text forms from users.
    - `PARSED_DATA_DIR`: Stores parsed JSON data for each user, used to query hh.ru.

- `handle_job_search_flow`: Core method that loads user preferences, performs the search, and triggers pagination display.
- `perform_job_search` and `job_pagination_callback`: Enable browsing through search results via inline buttons.

Bot Commands:
-------------
- `/start`: Welcomes the user and describes the bot's functionality.
- `/help`: Lists available commands and how to use them.
- `/fill_form`: Offers the user a form template to specify job search preferences.
- `/view_form`: Lets the user download their last uploaded form.
- `/search`: Triggers a job search using the submitted preferences.

Usage Notes:
------------
- User must first submit a correctly formatted `.txt` file using the form template.
- After parsing, preferences are saved in `{user_id}.json`, where the first element
  must be a dictionary of parameters directly acceptable by the hh.ru API.
"""


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PARSED_DATA_DIR = PROJECT_ROOT / "data" / "bot_user_data" / "parsed_user_data"
CANDIDATE_FORM_DIR = PROJECT_ROOT / "data" / "bot_user_data" / "candidate_form"
TEMPLATE_PATH = (
    PROJECT_ROOT / "telegram_interface" /
    "job_form_template" / "job_form_template.txt"
)


class TelegramBot:
    CALLBACK_DOWNLOAD = "download_template"
    CALLBACK_SEARCH_JOBS = "search_jobs"

    def __init__(self, token: str):
        self.token = token

        # check that the folders for storing data exist
        CANDIDATE_FORM_DIR.mkdir(parents=True, exist_ok=True)
        PARSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.user_job_cards = {}

        self.application = Application.builder().token(self.token).build()
        self._register_handlers()

    def _register_handlers(self) -> None:
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(
            CommandHandler("fill_form", self.ask_user_to_fill_form)
        )

        self.application.add_handler(
            CommandHandler("view_form", self.view_form))

        self.application.add_handler(
            CallbackQueryHandler(
                self.send_template_button, pattern=f"^{self.CALLBACK_DOWNLOAD}$"
            )
        )
        self.application.add_handler(
            MessageHandler(
                filters.Document.ALL & ~filters.COMMAND, self.process_uploaded_form
            )
        )
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.echo)
        )

        self.application.add_handler(
            CommandHandler("search", self.handle_search_jobs_command)
        )

        self.application.add_handler(
            CallbackQueryHandler(
                self.handle_search_jobs_button, pattern=f"^{self.CALLBACK_SEARCH_JOBS}$"
            )
        )
        self.application.add_handler(
            CallbackQueryHandler(
                self.job_pagination_callback, pattern=r"^job#\d+$")
        )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        await update.message.reply_text(
            f"Hello, {user.first_name}!\n"
            "I am your new bot. Here’s what I can do:\n\n"
            "- /fill_form — Submit a job preferences form\n"
            "- /view_form — View your latest submitted form\n"
            "- /help — See the available commands\n"
            "- /search — Search for jobs based on your form (available after submitting it)\n\n"
            "Let’s get started!"
        )

    async def help_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await update.message.reply_text(
            "I can help you manage your job preferences form. Here’s what I can do:\n\n"
            "- /start — Start the bot\n"
            "- /help — Show this help message\n"
            "- /fill_form — Download and fill out a job preferences form\n"
            "- /view_form — View your latest submitted form\n"
            "- /search — Search for jobs based on your form (available after submitting it)\n\n"
            "Let’s get started!"
        )

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(update.message.text)

    # form handling
    async def ask_user_to_fill_form(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Download form template", callback_data=self.CALLBACK_DOWNLOAD
                    )
                ]
            ]
        )
        await update.message.reply_text(
            "Please download the form template, fill it out, and send it back to me.",
            reply_markup=keyboard,
        )

    async def send_template_button(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        await query.answer()
        file_path_str = str(TEMPLATE_PATH.resolve())
        print(f"📂 Sending file: {file_path_str}")

        if not os.path.isfile(file_path_str):
            await query.message.reply_text("⚠️ File not found. Check the path!")
            return

        with open(file_path_str, "rb") as f:
            await query.message.reply_document(
                document=InputFile(f, filename=TEMPLATE_PATH.name)
            )

    async def process_uploaded_form(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        doc = update.message.document
        user_id = update.effective_user.id

        if not doc.mime_type.startswith("text/"):
            await update.message.reply_text(
                "Please send a text file (.txt) with the filled form."
            )
            return

        user_forms_path = CANDIDATE_FORM_DIR / f"{user_id}.txt"

        telegram_file = await doc.get_file()
        await telegram_file.download_to_drive(custom_path=str(user_forms_path))

        try:
            with open(user_forms_path, "r", encoding="utf-8") as f:
                form_text = f.read()

            parsed_data = parse_form(form_text)
            if not parsed_data:
                await update.message.reply_text(
                    "The form is empty or incorrectly formatted. Please use the provided template."
                )
                return

            PARSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
            parsed_user_data_file = PARSED_DATA_DIR / f"{user_id}.json"
            with open(parsed_user_data_file, "w", encoding="utf-8") as f:
                json.dump(parsed_data, f, ensure_ascii=False, indent=4)

            search_job_keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔍 Search jobs for me",
                            callback_data=self.CALLBACK_SEARCH_JOBS,
                        )
                    ]
                ]
            )
            await update.message.reply_text(
                f"Your form has been successfully processed and saved."
                "You can view it using the /view_form command. \nWould you like to search jobs based on your info?",
                reply_markup=search_job_keyboard,
            )
        except Exception as e:
            await update.message.reply_text(
                f"Error processing your form. Please ensure the form follows the provided template and is encoded in UTF-8."
            )

    async def view_form(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        user_id = update.effective_user.id
        file_path = CANDIDATE_FORM_DIR / f"{user_id}.txt"

        if not file_path.exists():
            await update.message.reply_text(
                "No form found. Please use /fill_form first."
            )
            return

        with open(file_path, "rb") as f:
            await update.message.reply_document(
                document=InputFile(f, filename="job_form.txt")
            )

    # Searching jobs
    async def handle_search_jobs_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        user_id = update.effective_chat.id
        await self.handle_job_search_flow(user_id, context)

    async def handle_search_jobs_button(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.callback_query
        await query.answer()
        user_id = query.message.chat.id
        await self.handle_job_search_flow(user_id, context)

    async def handle_job_search_flow(
            self, user_id: int, context: ContextTypes.DEFAULT_TYPE):
        """
        This function is triggered when a user initiates a job search via the /search command
        or the "🔍 Search jobs for me" inline button. It loads the user's job preferences
        (previously parsed and saved as JSON), passes them directly to the HeadHunter (hh.ru)
        API client, and stores the resulting list of job postings (URLs or card content)
        in memory for pagination and user navigation.
        Notes:
            The job preferences file must exist at PARSED_DATA_DIR/{user_id}.json
            and must be a list where the first element is a dictionary of valid hh.ru API search parameters.
        """
        # Notify the user
        await context.bot.send_message(
            chat_id=user_id, text="🔍 Finding jobs based on your filters, one moment..."
        )
        path_to_user_form = PARSED_DATA_DIR / f"{user_id}.json"

        if not path_to_user_form.exists():
            await context.bot.send_message(
                chat_id=user_id,
                text="⚠️ You haven't submitted your job preferences form yet.\n"
                "Please use the /fill_form command to provide your preferences before searching for jobs.",
            )
            return

        with open(path_to_user_form, "r", encoding="utf-8") as f:
            user_form = json.load(f)

        hh_base_filters = user_form[0]

        hh_api_client = HHClient()

        self.user_job_cards[user_id] = search_vacancies_by_params_hh(
            hh_api_client, hh_base_filters, user_id
        )
        await self.perform_job_search(user_id, context)

    # Searching jobs buttons
    async def perform_job_search(
            self, user_id: int, context: ContextTypes.DEFAULT_TYPE):

        job_cards = self.user_job_cards.get(user_id, [])

        if not job_cards:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Unfortunately, we couldn't find any vacancies matching your criteria. Please try changing your filters.",
            )
            return

        page = 0
        total = len(job_cards)
        vacancy_text = f"📄  Viewing job {page + 1}/{total}\n\n{job_cards[page]}"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Next", callback_data=f"job#{page + 1}")]
        ])

        await context.bot.send_message(
            chat_id=user_id, text=vacancy_text, reply_markup=keyboard
        )

    async def job_pagination_callback(
            self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.message.chat.id
        job_cards = self.user_job_cards.get(user_id, [])

        page = int(query.data.split("#")[1])
        total = len(job_cards)
        vacancy_text = f"📄  Viewing job {page + 1}/{total}\n\n{job_cards[page]}"

        buttons = []
        if page > 0:
            buttons.append(InlineKeyboardButton(
                "⬅️ Back", callback_data=f"job#{page - 1}"))
        if page < total - 1:
            buttons.append(InlineKeyboardButton(
                "➡️ Next", callback_data=f"job#{page + 1}"))

        keyboard = InlineKeyboardMarkup([buttons]) if buttons else None

        await query.edit_message_text(text=vacancy_text, reply_markup=keyboard)

    def run(self) -> None:
        self.application.run_polling()
