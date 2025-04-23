from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)


class TelegramBot:

    def __init__(self, token: str):

        self.token = token
        self.application = Application.builder().token(self.token).build()

        # Register handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register all message and command handlers."""
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))

        # Add message handler
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.echo)
        )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a welcome message when the /start command is issued."""
        user = update.effective_user
        await update.message.reply_text(f"Hello, {user.first_name}! I am your new bot.")

    async def help_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Send a help message when the /help command is issued."""
        await update.message.reply_text(
            "I can respond to your messages. Try typing something!"
        )

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Echo the user message back to the user."""
        await update.message.reply_text(update.message.text)

    def run(self) -> None:
        """Run the bot until Ctrl-C is pressed."""
        self.application.run_polling()
