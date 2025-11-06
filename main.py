import os
import asyncio
from uuid import uuid4
from dotenv import load_dotenv
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, InlineQueryHandler
from telegram.error import BadRequest

import database as db
import texts
from ton_api import TONAPIService
from keep_alive import keep_alive

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

class NFTShareBot:
    def __init__(self):
        self.ton_api = TONAPIService()
        self.db_pool = None

    # ... (start, message_handler, show_wallets_menu, show_my_nfts_menu methods are unchanged) ...
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for the /start command."""
        user = update.effective_user
        if self.db_pool is None:
            self.db_pool = await db.create_pool()

        await db.get_or_create_user(self.db_pool, user.id, user.username, user.first_name)

        text, reply_markup = texts.get_start_menu()
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for all button presses."""
        query = update.callback_query
        await query.answer()

        user = update.effective_user
        user_db_id = await db.get_or_create_user(self.db_pool, user.id, user.username, user.first_name)

        data = query.data

        try:
            if data == 'main_menu':
                text, reply_markup = texts.get_start_menu()
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')

            elif data == 'wallets_menu':
                await self.show_wallets_menu(query, user_db_id)

            elif data == 'add_wallet':
                text, reply_markup = texts.get_add_wallet_prompt()
                await db.set_user_state(self.db_pool, user.id, 'awaiting_wallet_address')
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')

            elif data == 'remove_wallet_menu':
                wallets = await db.get_user_wallets(self.db_pool, user_db_id)
                text, reply_markup = texts.get_remove_wallet_menu(wallets)
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')

            elif data.startswith('confirm_remove_'):
                wallet_address = data.replace('confirm_remove_', '')
                text, reply_markup = texts.get_confirm_remove_wallet_menu(wallet_address)
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')

            elif data.startswith('remove_'):
                wallet_address = data.replace('remove_', '')
                await db.remove_wallet(self.db_pool, user_db_id, wallet_address)
                await self.show_wallets_menu(query, user_db_id)

            elif data == 'help_menu':
                text, reply_markup = texts.get_help_menu()
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')

            elif data == 'my_nft_menu' or data == 'my_nft_menu_refresh':
                context.user_data.pop('nfts', None) # Clear cache on refresh
                await self.show_my_nfts_menu(query, user_db_id, context)

            elif data.startswith('nft_page_'):
                page = int(data.split('_')[-1])
                await self.show_my_nfts_menu(query, user_db_id, context, page=page)

            elif data.startswith('share_'):
                nft_address = data.replace('share_', '')
                await self.send_share_card(query.message, nft_address, user.username)

            elif data == 'noop':
                pass # Ignore clicks on the page number button

        except BadRequest as e:
            if "Message is not modified" in str(e):
                pass
            else:
                raise

    async def share_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for the /share command."""
        nft_address = context.args[0] if context.args else None
        if not nft_address:
            await update.message.reply_text("❌ Укажите адрес NFT: /share <адрес_NFT>")
            return
        
        await self.send_share_card(update.message, nft_address, update.effective_user.username)

    async def inline_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for inline queries."""
        query = update.inline_query.query
        if not query or len(query) < 48:
            return

        nft_data = await self.ton_api.get_nft_details(query)
        if not nft_data:
            return

        text, reply_markup = texts.get_share_card(nft_data, update.effective_user.username)

        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"Поделиться {nft_data.get('metadata', {}).get('name', 'NFT')}",
                description=f"Коллекция: {nft_data.get('collection', {}).get('name', 'Unknown')}",
                input_message_content=InputTextMessageContent(
                    message_text=text,
                    parse_mode='MarkdownV2'
                ),
                reply_markup=reply_markup
            )
        ]
        await update.inline_query.answer(results)

    async def send_share_card(self, message, nft_address, owner_username):
        """Fetches NFT details and sends the share card."""
        nft_data = await self.ton_api.get_nft_details(nft_address)
        if not nft_data:
            await message.reply_text("❌ NFT не найдена.")
            return

        text, reply_markup = texts.get_share_card(nft_data, owner_username)
        await message.reply_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for text messages, used for adding wallets."""
        user = update.effective_user
        user_state = await db.get_user_state(self.db_pool, user.id)

        if user_state == 'awaiting_wallet_address':
            wallet_address = update.message.text.strip()

            if len(wallet_address) == 48: # Basic validation
                user_db_id = await db.get_or_create_user(self.db_pool, user.id, user.username, user.first_name)
                success = await db.add_wallet(self.db_pool, user_db_id, wallet_address)

                if success:
                    await update.message.reply_text("✅ Кошелек успешно добавлен!")
                else:
                    await update.message.reply_text("Этот кошелек уже был добавлен ранее.")

                await db.clear_user_state(self.db_pool, user.id)

                await self.start(update, context)
            else:
                await update.message.reply_text("❌ Неверный формат адреса кошелька. Попробуйте еще раз.")
    
    async def show_wallets_menu(self, query, user_db_id):
        """Helper to display the wallets menu."""
        wallets = await db.get_user_wallets(self.db_pool, user_db_id)
        text, reply_markup = texts.get_wallets_menu(wallets)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')

    async def show_my_nfts_menu(self, query, user_db_id, context, page=0):
        """Helper to display the NFTs menu."""
        if 'nfts' not in context.user_data:
            loading_text, loading_markup = texts.get_my_nft_menu_loading()
            await query.edit_message_text(loading_text, reply_markup=loading_markup, parse_mode='MarkdownV2')

            wallets = await db.get_user_wallets(self.db_pool, user_db_id)
            if not wallets:
                text, reply_markup = texts.get_my_nft_menu([])
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')
                return

            all_nfts = []
            for wallet in wallets:
                nfts = await self.ton_api.get_wallet_nfts(wallet['wallet_address'])
                all_nfts.extend(nfts)
            
            all_nfts.sort(key=lambda x: (
                x.get('collection', {}).get('name', 'zzzz'),
                x.get('metadata', {}).get('name', 'zzzz')
            ))
            context.user_data['nfts'] = all_nfts
        
        nfts_to_show = context.user_data['nfts']
        text, reply_markup = texts.get_my_nft_menu(nfts_to_show, page=page)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')


async def init_db_for_bot(bot_instance):
    """Creates a db pool and attaches it to the bot instance."""
    bot_instance.db_pool = await db.create_pool()
    await db.init_db(bot_instance.db_pool)

def main():
    """Main function to run the bot."""
    keep_alive()

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    bot_instance = NFTShareBot()

    # Initialize the database and attach the pool to the bot instance
    asyncio.run(init_db_for_bot(bot_instance))

    application.add_handler(CommandHandler("start", bot_instance.start))
    application.add_handler(CommandHandler("share", bot_instance.share_command))
    application.add_handler(CallbackQueryHandler(bot_instance.button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_instance.message_handler))
    application.add_handler(InlineQueryHandler(bot_instance.inline_query_handler))
    
    application.run_polling()

if __name__ == "__main__":
    main()
