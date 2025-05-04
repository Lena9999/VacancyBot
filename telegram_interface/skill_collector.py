from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
    Application,
    PicklePersistence,
)
import os
from typing import Dict, List, Any


class AddSkillsDialog:
    """Handles the dialog for adding skills."""

    STATE_ADD_NEW_SKILLS = 1

    def __init__(self, persistence_path: str = "user_data.pickle"):
        """Initialize the AddSkillsDialog.

        Args:
            persistence_path: The file path for storing user data.
        """
        self.persistence_path = persistence_path

    def get_handler(self) -> ConversationHandler:
        """Returns the conversation handler for the skills dialog.

        Returns:
            ConversationHandler: The configured handler for skills dialog.
        """
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    self.handle_new_skills_button, pattern="^add_new_skills$"
                ),
                # CommandHandler("new_skills", self.start_skills_dialog),
            ],
            states={
                self.STATE_ADD_NEW_SKILLS: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, self.handle_new_skills_input
                    )
                ],
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel_skills),
                CallbackQueryHandler(
                    self.cancel_skills, pattern="^cancel$"),
            ],
            allow_reentry=True,
            name="add_skills_dialog",
            persistent=True,
            per_message=False
        )

    async def start_skills_dialog(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Starts the skills dialog by sending the add skills button.
        Returns:
            int: The end state of the conversation.
        """
        await self.send_add_skills_button(update, context)
        return ConversationHandler.END

    async def send_add_skills_button(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Sends a button for adding skills.
        """
        keyboard = [
            [InlineKeyboardButton("➕ Add skills",
                                  callback_data="add_new_skills")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Would you like to add skills to your profile?",
            reply_markup=reply_markup,
        )

    async def handle_new_skills_button(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handles the click on the 'Add skills' button.
        Returns:
            int: The next state of the conversation.
        """
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "Let us know your skills! Just separate them with commas (like this: Python, SQL, JavaScript)."
        )
        return self.STATE_ADD_NEW_SKILLS

    async def handle_new_skills_input(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Processes the user input for skills.
        Returns:
            int: The end state of the conversation.
        """
        skills_text = update.message.text

        skills_list = [
            skill.strip() for skill in skills_text.split(",")
            if skill.strip() and len(skill.strip()) <= 50  # Ограничение длины навыка
        ]

        if not skills_list:
            await update.message.reply_text(
                "Please enter at least one valid skill. Skills should be separated by commas."
            )
            return self.STATE_ADD_NEW_SKILLS

        user_id = update.effective_user.id

        os.makedirs(os.path.dirname(self.persistence_path), exist_ok=True)

        if "skills" not in context.user_data:
            context.user_data["skills"] = []

        new_skills = []
        for skill in skills_list:
            if skill not in context.user_data["skills"]:
                context.user_data["skills"].append(skill)
                new_skills.append(skill)

        await context.application.persistence.update_user_data(
            user_id, context.user_data
        )

        if new_skills:
            await update.message.reply_text(
                f"Great! Skills added: {', '.join(new_skills)}"
            )
        else:
            await update.message.reply_text("These skills have already been added before.")

        all_skills = context.user_data["skills"]
        await update.message.reply_text(f"Here are your current skills: {', '.join(all_skills)}")

        keyboard = [
            [InlineKeyboardButton("✅ Complete", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Click when you're done", reply_markup=reply_markup)

        return ConversationHandler.END

    async def cancel_skills(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Cancels the skills dialog.

        Returns:
            int: The end state of the conversation.
        """
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text("Skill collection completed!")
        else:
            await update.message.reply_text("Skill collection completed!")
        return ConversationHandler.END
