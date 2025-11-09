from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from src.texts import get_text
from src.utils.keyboards import main_menu_keyboard
from src.utils.db import add_user

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message and the main menu."""
    user = update.effective_user
    db_pool = context.bot_data["db_pool"]

    # Add or update the user in the database
    await add_user(
        db_pool,
        user.id,
        user.username,
        user.first_name,
        user.last_name
    )

    # Send the welcome message
    await update.message.reply_text(
        get_text('welcome'),
        reply_markup=main_menu_keyboard()
    )

start_handler = CommandHandler('start', start)
