import asyncio
import logging
from telegram.ext import Application
from src.config import TELEGRAM_TOKEN
from src.keep_alive import app as flask_app
from src.utils.db import setup_database, get_pool
import uvicorn

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main() -> None:
    """Start the bot."""
    # Set up the database
    await setup_database()

    # Create a database connection pool
    db_pool = await get_pool()
    if not db_pool:
        logger.error("Failed to create database pool. Exiting.")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.bot_data["db_pool"] = db_pool

    # Import handlers
    from src.handlers.start import start_handler
    from src.handlers.wallets import (
        wallets_handler,
        wallets_callback_handler,
        add_wallet_conversation_handler,
    )
    from src.handlers.nft import (
        my_nft_handler,
        my_nft_callback_handler,
        nft_page_handler,
        nft_details_handler,
    )
    from src.handlers.inline import inline_handler

    # Add handlers
    application.add_handler(start_handler)
    application.add_handler(inline_handler)
    application.add_handler(wallets_handler)
    application.add_handler(wallets_callback_handler)
    application.add_handler(add_wallet_conversation_handler)
    application.add_handler(my_nft_handler)
    application.add_handler(my_nft_callback_handler)
    application.add_handler(nft_page_handler)
    application.add_handler(nft_details_handler)

    # Start the bot
    await application.bot.set_my_commands([
        ('start', 'Main Menu'),
        ('wallets', 'Manage Wallets'),
        ('my_nft', 'My NFTs for Sharing'),
    ])

    await application.initialize()
    await application.start()

    # Start the Flask keep-alive server
    config = uvicorn.Config(flask_app, host="0.0.0.0", port=8080, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == '__main__':
    asyncio.run(main())
