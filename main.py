import logging
import os
import threading
import asyncio
import time
import requests
import json
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    PreCheckoutQueryHandler,
    MessageHandler,
    filters
)
from telegram.error import TelegramError, BadRequest, Conflict

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '8010736258:AAF6_xDBDbWCGSACBLv8GI9o6WFWT21ZlBA')
PAYMENT_PROVIDER_TOKEN = os.environ.get('PAYMENT_PROVIDER_TOKEN', '284685063:TEST:YjZiZTk5ZTFmM2Iy')
ADMIN_USER_ID = os.environ.get('ADMIN_USER_ID', '786080766')

def load_donations():
    try:
        with open('donations.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_donations(donations):
    with open('donations.json', 'w') as f:
        json.dump(donations, f, indent=4)

donations_data = load_donations()

# NFT Collections
NFT_COLLECTIONS = {
    "Gems Winter Store": {
        "image": "https://i.ibb.co/JWsYQJwH/CARTONKI.png",
        "description": (
            "🎁 Gift box 🎁\n"
            "by Gems Winter Store\n\n"
            "Rarity: Rare\n\n"
            "Own a piece of digital holiday magic! This rare gift box contains surprises "
            "that collectors dream about - a true digital time capsule of festive joy!"
        )
    },
    # Other NFT collections...
}

# Sticker Collections
STICKER_COLLECTIONS = {
    "Dogs OG": {
        "sticker_url": "https://t.me/sticker_bot/?startapp=tid_Nzg2MDgwNzY2",
        "description": (
            "**Elite Dog Collection - Status Symbols on the Loose!** 🐶\n\n"
            "These aren't just stickers - they're membership cards to the most exclusive "
            "Doge community on Telegram! Show off your status with these ultra-rare digital assets."
        )
    },
    # Other sticker collections...
}

# Collectible Items
COLLECTIBLE_ITEMS = {
    "Not Coin": {
        "link": "https://t.me/notgames_bot/profile?startapp=786080766",
        "description": (
            "🍕 **Pizza #439 and Diamond #542 💎 - NotCoin Chips**\n\n"
            "These aren't just collectibles - they're your resource to create something bigger. "
            "Turn them into profile elements, objects or even stickers."
        )
    },
    # Other collectible items...
}

CONTACT_USER = "not_jammm"

# Keyboard functions
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("NFT", callback_data="nft_menu")], 
        [InlineKeyboardButton("Stickers", callback_data="stickers_menu")],
        [InlineKeyboardButton("Collectible Items", callback_data="collectible_menu")],
        [InlineKeyboardButton("🌟 Donate", callback_data="donate")],
        [InlineKeyboardButton("🏆 Top Donators", callback_data="top_donors")]
    ])

def nft_menu_keyboard():
    buttons = []
    for nft_name in NFT_COLLECTIONS:
        buttons.append([InlineKeyboardButton(nft_name, callback_data=f"nft_{nft_name}")])
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="home")])
    return InlineKeyboardMarkup(buttons)

def nft_detail_keyboard(nft_name):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⬅️ Back", callback_data="back_nft"),
            InlineKeyboardButton("💬 DM for exchange", url=f"https://t.me/{CONTACT_USER}")
        ],
        [InlineKeyboardButton("🏠 Home", callback_data="home")]
    ])

def stickers_menu_keyboard():
    buttons = []
    for sticker_name in STICKER_COLLECTIONS:
        buttons.append([InlineKeyboardButton(sticker_name, callback_data=f"sticker_{sticker_name}")])
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="home")])
    return InlineKeyboardMarkup(buttons)

def sticker_detail_keyboard(sticker_name):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🖼️ View stickers", url=STICKER_COLLECTIONS[sticker_name]["sticker_url"]),
            InlineKeyboardButton("💬 DM for Purchase", url=f"https://t.me/{CONTACT_USER}")
        ],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="stickers_menu"),
            InlineKeyboardButton("🏠 Home", callback_data="home")
        ]
    ])

def collectible_menu_keyboard():
    buttons = []
    for item_name in COLLECTIBLE_ITEMS:
        buttons.append([InlineKeyboardButton(item_name, callback_data=f"collectible_{item_name}")])
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="home")])
    return InlineKeyboardMarkup(buttons)

def collectible_detail_keyboard(item_name):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔍 View Item", url=COLLECTIBLE_ITEMS[item_name]["link"]),
            InlineKeyboardButton("💬 DM for Purchase", url=f"https://t.me/{CONTACT_USER}")
        ],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="collectible_menu"),
            InlineKeyboardButton("🏠 Home", callback_data="home")
        ]
    ])

def donation_thanks_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Main Menu", callback_data="home")]
    ])

def top_donors_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back", callback_data="home")]
    ])

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command handler /start"""
    user_data = context.user_data
    
    if 'base_message_id' in user_data:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=user_data['base_message_id']
            )
        except TelegramError:
            pass
    
    user_data.clear()
    user_data['temp_messages'] = []
    
    await show_main_menu(update, context, is_new=True)

async def cleanup_temp_messages(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Deletes all temporary messages and clears the list"""
    user_data = context.user_data
    if 'temp_messages' not in user_data:
        return
    
    for msg_id in reversed(user_data['temp_messages']):
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            logger.info(f"Temporary message removed: {msg_id}")
        except TelegramError as e:
            if "message to delete not found" not in str(e).lower():
                logger.error(f"Error deleting message {msg_id}: {e}")
    
    user_data['temp_messages'] = []

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, is_new=False) -> None:
    """Shows the main menu"""
    chat_id = update.effective_chat.id
    user_data = context.user_data
    text = (
        "🏛 **Welcome to the Showcase!** 🏛\n\n"
        "Discover rare NFTs, unique stickers, and collectible items. "
        "All transactions are secure via @GiftElfRobot.\n\n"
        "🛍️ How to buy:\n"
        "1️⃣ Browse our collections\n"
        "2️⃣ Found something you like? DM us for purchase or exchange!\n\n"
        "⚠️ NFTs from the profile are for sale ONLY from 01.10.25 ⚠️"
    )
    
    await cleanup_temp_messages(context, chat_id)
    
    if is_new or 'base_message_id' not in user_data:
        message = await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )
        user_data['base_message_id'] = message.message_id
        logger.info(f"New main message created: {message.message_id}")
    else:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=user_data['base_message_id'],
                text=text,
                reply_markup=main_menu_keyboard(),
                parse_mode="Markdown"
            )
            logger.info(f"Main message updated: {user_data['base_message_id']}")
        except BadRequest as e:
            if "message is not modified" in str(e).lower():
                logger.info("Message unchanged (main menu)")
            else:
                logger.error(f"Main menu error: {e}")
                message = await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=main_menu_keyboard(),
                    parse_mode="Markdown"
                )
                user_data['base_message_id'] = message.message_id
                logger.info(f"New main message created due to error: {message.message_id}")

# Navigation handlers
async def show_nft_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the NFT menu"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_data = context.user_data
    
    await cleanup_temp_messages(context, chat_id)
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=user_data['base_message_id'],
            text="🎨 **NFT Collections**\n\nSelect an NFT to view:",
            reply_markup=nft_menu_keyboard(),
            parse_mode="Markdown"
        )
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            pass
        else:
            logger.error(f"NFT menu error: {e}")
            await show_main_menu(update, context, is_new=True)

async def show_nft_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, nft_name: str) -> None:
    """Shows NFT details"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_data = context.user_data
    
    await cleanup_temp_messages(context, chat_id)
    
    nft = NFT_COLLECTIONS[nft_name]
    
    try:
        message = await context.bot.send_photo(
            chat_id=chat_id,
            photo=nft['image'],
            caption=f"✨ **{nft_name}** ✨\n\n{nft['description']}\n\n✅ Ready for sale/exchange",
            reply_markup=nft_detail_keyboard(nft_name),
            parse_mode="Markdown"
        )
        user_data.setdefault('temp_messages', []).append(message.message_id)
    except Exception as e:
        logger.error(f"NFT details error: {e}")
        message = await context.bot.send_message(
            chat_id=chat_id,
            text=f"✨ **{nft_name}** ✨\n\n{nft['description']}\n\n✅ Ready for sale/exchange\n\n⚠️ Image unavailable",
            reply_markup=nft_detail_keyboard(nft_name),
            parse_mode="Markdown"
        )
        user_data.setdefault('temp_messages', []).append(message.message_id)

# Other navigation handlers (stickers, collectibles) follow the same pattern...

# Donation handlers
async def start_donate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends donation invoice"""
    query = update.callback_query
    if query:
        await query.answer()
        chat_id = query.message.chat_id
    else:
        chat_id = update.message.chat_id
    
    user_data = context.user_data
    await cleanup_temp_messages(context, chat_id)
    
    if not PAYMENT_PROVIDER_TOKEN:
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ Donations are temporarily unavailable"
        )
        return

    try:
        payload = f"donate_{update.effective_user.id}_{int(time.time())}"
        await context.bot.send_invoice(
            chat_id=chat_id,
            title="Support the Developer",
            description="Your donation helps improve this bot!",
            payload=payload,
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency="XTR",
            prices=[LabeledPrice(label="Stars", amount=1)],
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            is_flexible=False
        )
    except Exception as e:
        logger.error(f"Error sending invoice: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ Error creating donation. Please try again later."
        )

async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles pre-checkout query"""
    query = update.pre_checkout_query
    try:
        await query.answer(ok=True)
    except Exception as e:
        logger.error(f"Pre-checkout error: {e}")

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles successful payment"""
    user = update.effective_user
    payment = update.message.successful_payment
    amount = payment.total_amount
    
    global donations_data
    
    user_id = str(user.id)
    if user_id in donations_data:
        donations_data[user_id]['total'] += amount
        donations_data[user_id]['count'] += 1
    else:
        donations_data[user_id] = {
            'username': user.username or user.full_name,
            'total': amount,
            'count': 1
        }
    
    save_donations(donations_data)
    
    await update.message.reply_text(
        f"❤️ Thank you for your donation of {amount} stars!",
        reply_markup=donation_thanks_keyboard()
    )

async def show_top_donors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows top donors"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_data = context.user_data
    
    await cleanup_temp_messages(context, chat_id)
    
    sorted_donors = sorted(
        donations_data.items(),
        key=lambda x: x[1]['total'],
        reverse=True
    )[:10]
    
    text = "🏆 Top Donators:\n\n"
    if not sorted_donors:
        text += "No donations yet. Be the first!"
    else:
        for i, (user_id, data) in enumerate(sorted_donors, 1):
            username = data['username']
            total = data['total']
            text += f"{i}. {username}: {total} stars\n"
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=user_data['base_message_id'],
            text=text,
            reply_markup=top_donors_keyboard(),
            parse_mode="Markdown"
        )
    except BadRequest as e:
        logger.error(f"Top donors error: {e}")
        await show_main_menu(update, context, is_new=True)

# Refund command
async def refund_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles refund requests (admin only)"""
    if str(update.effective_user.id) != ADMIN_USER_ID:
        await update.message.reply_text("❌ You are not authorized to use this command")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /refund <user_id> <amount>")
        return

    try:
        user_id = args[0]
        amount = int(args[1])
        
        if user_id not in donations_data:
            await update.message.reply_text("❌ User not found in donation records")
            return
            
        if donations_data[user_id]['total'] < amount:
            await update.message.reply_text("❌ Refund amount exceeds user's total donations")
            return
        
        # Refund logic would go here
        # In a real implementation, you would call payment provider's API
        donations_data[user_id]['total'] -= amount
        save_donations(donations_data)
        
        await update.message.reply_text(f"✅ Successfully refunded {amount} stars to user {user_id}")
        
    except Exception as e:
        logger.error(f"Refund error: {e}")
        await update.message.reply_text("❌ Error processing refund")

# Button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles all callback buttons"""
    query = update.callback_query
    data = query.data

    try:
        if data == "nft_menu":
            await show_nft_menu(update, context)
        elif data == "stickers_menu":
            await show_stickers_menu(update, context)
        elif data == "collectible_menu":
            await show_collectible_menu(update, context)
        elif data == "donate":
            await start_donate(update, context)
        elif data == "top_donors":
            await show_top_donors(update, context)
        elif data.startswith("nft_"):
            nft_name = data[4:]
            await show_nft_detail(update, context, nft_name)
        elif data.startswith("sticker_"):
            sticker_name = data[8:]
            await show_sticker_detail(update, context, sticker_name)
        elif data.startswith("collectible_"):
            item_name = data[12:]
            await show_collectible_detail(update, context, item_name)
        elif data == "home":
            await show_main_menu(update, context, is_new=True)
        elif data == "back_nft":
            await show_nft_menu(update, context)
    except Exception as e:
        logger.error(f"Button handler error: {e}")
        try:
            await query.answer("⚠️ An error occurred. Please try again later")
        except:
            pass

# Flask server for keep-alive
def run_flask_server():
    app = Flask(__name__)

    @app.route('/')
    def home():
        return "🤖 Bot is running! UptimeRobot monitoring active."

    @app.route('/health')
    def health_check():
        return "OK", 200

    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    """Regularly sends requests to keep the bot awake"""
    while True:
        try:
            server_url = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:10000')
            health_url = f"{server_url}/health"
            response = requests.get(health_url, timeout=10)
            logger.info(f"Keep-alive request sent! Status: {response.status_code}")
        except Exception as e:
            logger.error(f"Keep-alive error: {e}")
        time.sleep(14 * 60)  # 14 minutes

def main() -> None:
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not set!")
        return
        
    if not PAYMENT_PROVIDER_TOKEN:
        logger.warning("⚠️ PAYMENT_PROVIDER_TOKEN not set. Donations disabled")

    # Start Flask server in a thread
    server_thread = threading.Thread(target=run_flask_server)
    server_thread.daemon = True
    server_thread.start()
    logger.info(f"🌐 HTTP server running on port {os.environ.get('PORT', 10000)}")

    # Start keep-alive thread for Render
    if os.environ.get('RENDER'):
        wakeup_thread = threading.Thread(target=keep_alive)
        wakeup_thread.daemon = True
        wakeup_thread.start()
        logger.info("🔔 Keep-alive activated (14 min interval)")

    # Create bot application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("donate", start_donate))
    application.add_handler(CommandHandler("refund", refund_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    # Start polling with retries
    max_retries = 5
    retry_delay = 10
    
    for attempt in range(max_retries):
        try:
            logger.info("🤖 Starting bot...")
            application.run_polling(
                drop_pending_updates=True,
                close_loop=False,
                allowed_updates=Update.ALL_TYPES,
                poll_interval=2.0
            )
            break
        except Conflict as e:
            logger.error(f"Conflict error (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error("Max retries exceeded. Bot stopped.")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            break

if __name__ == "__main__":
    main()
