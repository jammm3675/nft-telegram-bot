import os
import asyncio
from uuid import uuid4
from dotenv import load_dotenv
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, InlineQueryHandler
from telegram.error import BadRequest
from aiohttp import web

import database as db
import texts
from ton_api import TONAPIService
from keep_alive import create_keep_alive_app

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# --- Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_pool = context.bot_data['db_pool']
    await db.get_or_create_user(db_pool, user.id, user.username, user.first_name)
    text, reply_markup = texts.get_start_menu()
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    db_pool = context.bot_data['db_pool']
    ton_api = context.bot_data['ton_api']
    user_db_id = await db.get_or_create_user(db_pool, user.id, user.username, user.first_name)
    data = query.data
    try:
        if data == 'main_menu':
            text, reply_markup = texts.get_start_menu()
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')
        elif data == 'wallets_menu':
            await show_wallets_menu(query, db_pool, user_db_id)
        elif data == 'add_wallet':
            text, reply_markup = texts.get_add_wallet_prompt()
            await db.set_user_state(db_pool, user.id, 'awaiting_wallet_address')
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')
        elif data == 'remove_wallet_menu':
            wallets = await db.get_user_wallets(db_pool, user_db_id)
            text, reply_markup = texts.get_remove_wallet_menu(wallets)
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')
        elif data.startswith('confirm_remove_'):
            wallet_address = data.replace('confirm_remove_', '')
            text, reply_markup = texts.get_confirm_remove_wallet_menu(wallet_address)
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')
        elif data.startswith('remove_'):
            wallet_address = data.replace('remove_', '')
            await db.remove_wallet(db_pool, user_db_id, wallet_address)
            await show_wallets_menu(query, db_pool, user_db_id)
        elif data == 'help_menu':
            text, reply_markup = texts.get_help_menu()
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')
        elif data == 'my_nft_menu' or data == 'my_nft_menu_refresh':
            context.user_data.pop('nfts', None)
            await show_my_nfts_menu(query, db_pool, ton_api, user_db_id, context)
        elif data.startswith('nft_page_'):
            page = int(data.split('_')[-1])
            await show_my_nfts_menu(query, db_pool, ton_api, user_db_id, context, page=page)
        elif data.startswith('share_'):
            nft_address = data.replace('share_', '')
            await send_share_card(query.message, ton_api, nft_address, user.username)
        elif data == 'noop':
            pass
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            print(f"BadRequest error in button_handler: {e}")

async def share_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ton_api = context.bot_data['ton_api']
    nft_address = context.args[0] if context.args else None
    if not nft_address:
        await update.message.reply_text("❌ Укажите адрес NFT: /share <адрес_NFT>")
        return
    await send_share_card(update.message, ton_api, nft_address, update.effective_user.username)

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    ton_api = context.bot_data['ton_api']
    if not query or len(query) < 48:
        return
    nft_data = await ton_api.get_nft_details(query)
    if not nft_data:
        return
    text, reply_markup = texts.get_share_card(nft_data, update.effective_user.username)
    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=f"Поделиться {nft_data.get('metadata', {}).get('name', 'NFT')}",
            description=f"Коллекция: {nft_data.get('collection', {}).get('name', 'Unknown')}",
            input_message_content=InputTextMessageContent(message_text=text, parse_mode='MarkdownV2'),
            reply_markup=reply_markup
        )
    ]
    await update.inline_query.answer(results)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_pool = context.bot_data['db_pool']
    user_state = await db.get_user_state(db_pool, user.id)
    if user_state == 'awaiting_wallet_address':
        wallet_address = update.message.text.strip()
        if len(wallet_address) == 48:
            user_db_id = await db.get_or_create_user(db_pool, user.id, user.username, user.first_name)
            success = await db.add_wallet(db_pool, user_db_id, wallet_address)
            if success:
                await update.message.reply_text("✅ Кошелек успешно добавлен!")
            else:
                await update.message.reply_text("Этот кошелек уже был добавлен ранее.")
            await db.clear_user_state(db_pool, user.id)
            text, reply_markup = texts.get_start_menu()
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')
        else:
            await update.message.reply_text("❌ Неверный формат адреса кошелька. Попробуйте еще раз.")

# --- Helper Functions ---
async def send_share_card(message, ton_api, nft_address, owner_username):
    nft_data = await ton_api.get_nft_details(nft_address)
    if not nft_data:
        await message.reply_text("❌ NFT не найдена.")
        return
    text, reply_markup = texts.get_share_card(nft_data, owner_username)
    await message.reply_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')

async def show_wallets_menu(query, db_pool, user_db_id):
    wallets = await db.get_user_wallets(db_pool, user_db_id)
    text, reply_markup = texts.get_wallets_menu(wallets)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')

async def show_my_nfts_menu(query, db_pool, ton_api, user_db_id, context, page=0):
    if 'nfts' not in context.user_data:
        loading_text, loading_markup = texts.get_my_nft_menu_loading()
        await query.edit_message_text(loading_text, reply_markup=loading_markup, parse_mode='MarkdownV2')
        wallets = await db.get_user_wallets(db_pool, user_db_id)
        if not wallets:
            text, reply_markup = texts.get_my_nft_menu([])
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')
            return
        all_nfts = []
        for wallet in wallets:
            nfts = await ton_api.get_wallet_nfts(wallet['wallet_address'])
            all_nfts.extend(nfts)
        all_nfts.sort(key=lambda x: (x.get('collection', {}).get('name', 'zzzz'), x.get('metadata', {}).get('name', 'zzzz')))
        context.user_data['nfts'] = all_nfts
    nfts_to_show = context.user_data['nfts']
    text, reply_markup = texts.get_my_nft_menu(nfts_to_show, page=page)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')

# --- Application Setup ---
async def post_init(application: Application):
    db_pool = await db.create_pool()
    await db.init_db(db_pool)
    application.bot_data['db_pool'] = db_pool
    application.bot_data['ton_api'] = TONAPIService()

async def main():
    """Main function to set up and run the bot and web server."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("share", share_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_handler(InlineQueryHandler(inline_query_handler))
    
    # --- aiohttp Web Server Setup ---
    keep_alive_app = await create_keep_alive_app()
    runner = web.AppRunner(keep_alive_app)
    await runner.setup()
    port = int(os.getenv('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)

    # Initialize the application and then start both servers
    await application.initialize()
    await site.start()

    # Start polling for Telegram updates
    await application.updater.start_polling()

    # Keep the script running
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
