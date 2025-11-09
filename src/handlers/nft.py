from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from src.texts import get_text
from src.utils.keyboards import nft_list_keyboard, share_nft_keyboard
from src.utils.db import get_wallets
from src.services.ton_api import TONAPIService
from src.config import TON_API_KEY
import math

NFTS_PER_PAGE = 5

async def my_nft_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /my_nft command and 'my_nft' callback."""
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
    else:
        message = update.message

    user_id = update.effective_user.id
    db_pool = context.bot_data["db_pool"]

    await message.reply_text(get_text('loading_nfts'))

    user_wallets = await get_wallets(db_pool, user_id)
    if not user_wallets:
        await message.edit_text("You have no wallets linked.")
        return

    ton_api = TONAPIService(TON_API_KEY)
    all_nfts = []
    for wallet in user_wallets:
        nfts_data = await ton_api.get_nfts(wallet)
        all_nfts.extend(nfts_data.get('nft_items', []))

    context.user_data['nfts'] = all_nfts

    await show_nft_page(update, context, page=0)


async def show_nft_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    """Displays a paginated list of NFTs."""
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
    else:
        message = update.message

    all_nfts = context.user_data.get('nfts', [])
    if not all_nfts:
        await message.edit_text("No NFTs found in your wallets.")
        return

    start_index = page * NFTS_PER_PAGE
    end_index = start_index + NFTS_PER_PAGE
    nfts_to_show = all_nfts[start_index:end_index]

    total_pages = math.ceil(len(all_nfts) / NFTS_PER_PAGE)

    keyboard = []
    for nft in nfts_to_show:
        nft_name = nft.get('metadata', {}).get('name', 'Unnamed NFT')
        keyboard.append([InlineKeyboardButton(f"🖼️ {nft_name}", callback_data=f"nft_{nft['address']}")])

    pagination_keyboard = nft_list_keyboard(page + 1, total_pages)
    for row in pagination_keyboard.inline_keyboard:
        keyboard.append(row)

    await message.edit_text(
        "🖼️ Ваши NFT для шаринга",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def nft_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles pagination for the NFT list."""
    query = update.callback_query
    page = int(query.data.split('_')[-1])
    await show_nft_page(update, context, page=page)


async def show_nft_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the details of a single NFT."""
    query = update.callback_query
    nft_address = query.data.split('_')[1]
    all_nfts = context.user_data.get('nfts', [])

    selected_nft = next((nft for nft in all_nfts if nft['address'] == nft_address), None)

    if not selected_nft:
        await query.answer("NFT not found.", show_alert=True)
        return

    nft_name = selected_nft.get('metadata', {}).get('name', 'Unnamed NFT')
    collection_name = selected_nft.get('collection', {}).get('name', 'Unnamed Collection')
    owner_username = f"@{update.effective_user.username}" if update.effective_user.username else "link"
    getgems_url = f"https://getgems.io/nft/{nft_address}"

    message_text = get_text('nft_card_template').format(
        nft_name=nft_name,
        collection_name=collection_name,
        owner_username=owner_username
    )

    await query.edit_message_text(
        message_text,
        reply_markup=share_nft_keyboard(update.effective_user.id, getgems_url)
    )

my_nft_handler = CommandHandler('my_nft', my_nft_command)
my_nft_callback_handler = CallbackQueryHandler(my_nft_command, pattern='^my_nft$')
nft_page_handler = CallbackQueryHandler(nft_page_callback, pattern='^(prev_nft_page_|next_nft_page_)')
nft_details_handler = CallbackQueryHandler(show_nft_details, pattern='^nft_')
