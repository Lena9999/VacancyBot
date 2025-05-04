from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    PicklePersistence
)
from .skill_collector import AddSkillsDialog


class TelegramBot:

    def __init__(self, token: str, persistence_path: str = "user_data.pickle"):

        self.token = token

        self.persistence_path = persistence_path
        persistence = PicklePersistence(filepath=self.persistence_path)
        self.application = Application.builder().token(
            self.token).persistence(persistence).build()

        self.skills_dialog = AddSkillsDialog(
            persistence_path=self.persistence_path)

        # Register handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register all message and command handlers."""
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))

        # SKILLS
        # Add skills dialog handler
        self.application.add_handler(self.skills_dialog.get_handler())
        # Add command to start skills dialog
        self.application.add_handler(CommandHandler(
            "add_skills", self.start_skills_dialog))

        # Add message handler
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.echo)
        )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a welcome message when the /start command is issued."""
        user = update.effective_user
        await update.message.reply_text(f"Hello, {user.first_name}! I am your new bot. Use /add_skills to add your skills to your profile.")

    async def help_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Send a help message when the /help command is issued."""
        await update.message.reply_text(
            "I can help you manage your skills profile. Available commands:\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/add_skills - Add new skills to your profile"
        )

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Echo the user message back to the user."""
        await update.message.reply_text(update.message.text)

    # SKILLS
    async def start_skills_dialog(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Start the skills dialog."""
        await self.skills_dialog.send_add_skills_button(update, context)

    def run(self) -> None:
        """Run the bot until Ctrl-C is pressed."""
        self.application.run_polling()
