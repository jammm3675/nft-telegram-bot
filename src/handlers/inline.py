import uuid
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes, InlineQueryHandler
from src.texts import get_text
from src.utils.db import get_wallets
from src.services.ton_api import TONAPIService
from src.config import TON_API_KEY
from src.utils.keyboards import share_nft_keyboard

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the inline query."""
    query = update.inline_query.query
    user_id = update.effective_user.id
    db_pool = context.bot_data["db_pool"]

    user_wallets = await get_wallets(db_pool, user_id)
    if not user_wallets:
        await update.inline_query.answer([], switch_pm_text="Link a wallet first", switch_pm_parameter="start")
        return

    ton_api = TONAPIService(TON_API_KEY)
    all_nfts = []
    for wallet in user_wallets:
        nfts = await ton_api.get_nfts(wallet)
        all_nfts.extend(nfts.get('nft_items', []))

    results = []
    for nft in all_nfts:
        if query.lower() in nft.get('metadata', {}).get('name', '').lower():
            nft_name = nft.get('metadata', {}).get('name', 'Unnamed NFT')
            collection_name = nft.get('collection', {}).get('name', 'Unnamed Collection')
            owner_username = f"@{update.effective_user.username}" if update.effective_user.username else "link"

            # Placeholder for Getgems URL
            getgems_url = f"https://getgems.io/nft/{nft.get('address')}"

            message_text = get_text('nft_card_template').format(
                nft_name=nft_name,
                collection_name=collection_name,
                owner_username=owner_username
            )

            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title=nft_name,
                    description=collection_name,
                    input_message_content=InputTextMessageContent(message_text),
                    reply_markup=share_nft_keyboard(user_id, getgems_url)
                )
            )

    await update.inline_query.answer(results)

inline_handler = InlineQueryHandler(inline_query)
