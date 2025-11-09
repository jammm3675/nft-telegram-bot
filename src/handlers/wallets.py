from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)
from src.texts import get_text
from src.utils.keyboards import wallets_menu_keyboard
from src.utils.db import get_wallets, add_wallet

# Define states for the conversation
AWAITING_WALLET = 1

async def wallets_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /wallets command and 'my_wallet' callback."""
    query = update.callback_query
    user_id = update.effective_user.id
    db_pool = context.bot_data["db_pool"]

    user_wallets = await get_wallets(db_pool, user_id)

    if query:
        await query.answer()
        await query.edit_message_text(
            get_text('wallets_menu'),
            reply_markup=wallets_menu_keyboard(user_wallets)
        )
    else:
        await update.message.reply_text(
            get_text('wallets_menu'),
            reply_markup=wallets_menu_keyboard(user_wallets)
        )


async def add_wallet_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompts the user to send a wallet address."""
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(get_text('add_wallet_prompt'))
    return AWAITING_WALLET

async def wallet_address_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the wallet address sent by the user."""
    user_id = update.effective_user.id
    wallet_address = update.message.text.strip()
    db_pool = context.bot_data["db_pool"]

    if len(wallet_address) == 48:
        if await add_wallet(db_pool, user_id, wallet_address):
            await update.message.reply_text("✅ Wallet added successfully!")
        else:
            await update.message.reply_text("⚠️ This wallet is already added.")
    else:
        await update.message.reply_text("❌ Invalid wallet address.")

    user_wallets = await get_wallets(db_pool, user_id)
    await update.message.reply_text(
        get_text('wallets_menu'),
        reply_markup=wallets_menu_keyboard(user_wallets)
    )
    return ConversationHandler.END

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the conversation."""
    await update.message.reply_text("Action cancelled.")
    await wallets_menu(update, context)
    return ConversationHandler.END


wallets_handler = CommandHandler('wallets', wallets_menu)
wallets_callback_handler = CallbackQueryHandler(wallets_menu, pattern='^my_wallet$')

add_wallet_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_wallet_prompt, pattern='^add_wallet$')],
    states={
        AWAITING_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, wallet_address_handler)],
    },
    fallbacks=[CommandHandler('cancel', cancel_conversation)],
)
