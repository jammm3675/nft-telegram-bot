import logging
import os
import threading
import asyncio
import time
import requests
import json
from flask import Flask
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    LabeledPrice, 
    PreCheckoutQuery,
    BotCommand
)
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

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '8010736258:AAF6_xDBDbWCGSACBLv8GI9o6WFWT21ZlBA')
PAYMENT_PROVIDER_TOKEN = os.environ.get('PAYMENT_PROVIDER_TOKEN', '284685063:TEST:YjZiZTk5ZTFmM2Iy')
ADMIN_USER_ID = int(os.environ.get('ADMIN_USER_ID', 786080766))  # Your Telegram user ID

# Load donation data
def load_donations():
    try:
        with open('donations.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Save donation data
def save_donations(donations):
    with open('donations.json', 'w') as f:
        json.dump(donations, f, indent=4)

# Load refund data
def load_refunds():
    try:
        with open('refunds.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Save refund data
def save_refunds(refunds):
    with open('refunds.json', 'w') as f:
        json.dump(refunds, f, indent=4)

# Initialize data
donations_data = load_donations()
refunds_data = load_refunds()

# NFT Collections
NFT_COLLECTIONS = {
    "Gems Winter Store": {
        "image": "https://i.ibb.co/JWsYQJwH/CARTONKI.png",
        "description": (
            "🎁 Gift box 🎁  \n"
            "by Gems Winter Store  \n\n"
            "Rarity: Rare  \n\n"
            "Own a piece of digital holiday magic! This rare gift box from Gems Winter Store \n"
            "Each box contains surprises that collectors dream about - a true digital time capsule of festive joy!  "
        )
    },
    "Lost Dogs: The Hint": {
        "image": "https://i.ibb.co/gZ20qd68/Lost-Dogs.png",
        "description": (
            "🦸 The League 🦸 - Ultimate Collector's Trophy  \n"
            "by Lost Dogs: The Hint  \n\n"
            "Rarity: Rare  \n\n"
            "Secure this legendary piece from the acclaimed Lost Dogs universe!  \n"
            "This isn't just an NFT - it's a symbol of your status in the crypto-art world.  \n"
            "Rare backstory with cult following. "
        )
    },
    "Medieval Deck": {
        "image": "https://i.ibb.co/RTHnvCsr/TON-POKER.png",
        "description": (
            "🃏 Ace of Strength 🃏  \n"
            "by Medieval Deck\n\n"
            "Rarity: Epic\n\n"
            "This epic NFT was handcrafted by the visionary artist Ilya Stallone in collaboration with TON Poker.  "
        )
    },
    "Postmarks: Odds + Ends": {
        "image": "https://i.ibb.co/1tvKy4HV/Fool-moon.png",
        "description": (
            "🌙 Fool Moon 🌙 -  Classic Digital Art  \n"
            "by Postmarks: Odds + Ends\n\n"
            "**Story**: The fool moon, the worm-eaten luminary: a drunken sanctuary of the bewildered,  \n"
            "a lighthouse flickering from all sides. You get distracted, wandering like a sleeper –  \n"
            "that's how the zodiacs died, my friend. Not overthrown by force, not defeated by intellect,  \n"
            "but lost in delirium.  "
        )
    },
    "Postmarks: The Jaegers": {
        "image": "https://i.ibb.co/MyCJ8J33/NIX.png",
        "description": (
            "🌊 NIX 🌊- Deepwater Miracle  \n"
            "by Postmarks: The Jaegers\n\n"
            "Rarity: Rare\n\n"
            "**Story**: Once one of the Jaegers tried to fight one of the ancient titans "
            "in the Pacific Ocean, but was defeated and now his body lies lifeless at a depth of 10 kilometers. "
            "But who knows, maybe he's just accumulating energy."
        )
    },
    "The Seven Virtues": {
        "image": "https://i.ibb.co/ympwRnF8/TheSevenVirtues.png",
        "description": (
            "💫 Patience Postmark 💫 - Symbol of Inner Strength  \n"
            "by The Seven Virtues  \n\n"
            "Rarity: Rare  \n\n"
            "The Seven Virtues is a collaboration between the artist Olyabolyaboo and Cheques Corp., continuing the narrative of -The Seven Deadly Sins-  \n"
            "While the sins made us reflect on our weaknesses, this collection inspires action. Humility, generosity,  \n"
            "patience, purity, kindness, temperance, and diligence — seven principles that create a new story.  \n"
            "This drop is a symbol of the bright side of your inner strength.  "
        )
    },
    "Ton Space Badges": {
        "image": "https://i.ibb.co/LDDnhfXy/TonSpaceBadges.png",
        "description": (
            "🥇 Gold Badge 🥇 - Proof You Were EARLY  \n"
            "by Ton Space Badges\n\n"
            "Own a piece of TON Space history! This exclusive badge is your verifiable proof  \n"
            "that you recognized the potential of TON Space before anyone else.  \n"
            "No remints. No second drops. Just verifiable proof you were early.  "
        )
    }
}

# Sticker Collections
STICKER_COLLECTIONS = {
    "Dogs OG": {
        "sticker_url": "https://t.me/sticker_bot/?startapp=tid_Nzg2MDgwNzY2",
        "description": (
            "**Elite Dog Collection - Status Symbols on the Loose!** 🐶\n\n"
            "These aren't just stickers - they're membership cards to the most exclusive  \n"
            "Doge community on Telegram! Show off your status with these ultra-rare digital assets:  \n\n"
            "•Bow Tie #4780 - Absolutely Classic and Elegant  \n"
            "•One Piece #6673 - Iconic Character from the eponymous production  \n"
            "•Panama Hat #1417 - Summer Classic  \n"
            "•Kamikaze #4812 - Favorite Among Collectors of Original Items  \n\n"
            "Meet Dogs and get ready to meet your new best friend who's always got your back (and your snacks)!  "
        )
    },
    "Dogs Rewards": {
        "sticker_url": "https://t.me/sticker_bot/?startapp=tid_Nzg2MDgwNzY2",
        "description": (
            "•Full Dig #4453 - The Ultimate Miner's Trophy** ⛏️\n\n" 
            "This isn't just a sticker - it's proof of your dedication to the Doge ecosystem!  \n" 
            "Awarded only to the most committed community members and early supporters.  \n\n" 
            "Why collectors value this above all:  \n" 
            "- Rare sticker in the Dogs universe  \n" 
            "- Grants special mining bonuses  \n" 
            "- Recognized status in all Doge games  " 
        )
    },
    "Lost Dogs": {
        "sticker_url": "https://t.me/sticker_bot/?startapp=tid_Nzg2MDgwNzY2",
        "description": (
            "**•Magic of the Way #2871 - The Philosopher's Stone of Stickers** 🔮  \n\n"
            "Own the most mystical sticker in the Lost Dogs universe! This isn't just digital art - \n"
            "it's a key to hidden content and special privileges across the entire Lost Dogs ecosystem.  \n\n"
            "Who are these Lost Dogs? They have an NFT collection, a game, a cartoon, and an entire universe… all for fun?  "
        )
    },
    "Not Coin": {
        "sticker_url": "https://t.me/sticker_bot/?startapp=tid_Nzg2MDgwNzY2",
        "description": (
            "**•Not Meme #2015 - The Icon that started a revolution** 🪙  \n\n"
            "Own a piece of crypto history! This legendary sticker launched a thousand memes  \n"
            "and became the symbol of the NotCoin phenomenon. More than digital art - it's a cultural artifact!  \n\n"
            "Probably nothing  "
        )
    },
    "Not Pixel": {
        "sticker_url": "https://t.me/sticker_bot/?startapp=tid_Nzg2MDgwNzY2",
        "description": (
            "**Pixel Collection - Battle-tested, collector-approved** 🎮  \n\n"
            "Collect your own set of the most iconic pixel art from Telegram's biggest battle!  \n"
            "These aren't just stickers - these are trophies from the front lines of a social experiment that rocked crypto.  \n\n"
            "Best Flexible Set:  \n"
            "•Vice Pixel #1736: a nod to the legendary game  \n"
            "•Dog Pixel #1023: a community favorite  \n"
            "•Grass Pixel #2536: from the Minecraft universe  \n"
            "•Mac Pixel #3071: everyone loves fast food, right?  \n\n"
            "Biggest Telegram Battle, biggest social experiment, and now – biggest sticker flex  "
        )
    }
}

# Collectible Items
COLLECTIBLE_ITEMS = {
    "Not Coin": {
        "link": "https://t.me/notgames_bot/profile?startapp=786080766",
        "description": (
            "🍕 **Pizza #439 and Diamond #542 💎 - NotCoin Chips**  \n\n"
            "These aren't just collectibles - they're your resource to create something bigger.  \n"
            "Turn them into a corner of a profile, objects or even stickers.  "

        )
    },
    "Not Games": {
        "link": "https://t.me/notgames_bot/profile?startapp=786080766",
        "description": (
            "☀️ **Sun #103 ☀️ - the main source of energy**  \n\n"
            "It's not just a collectible - it's your way of expressing yourself in the ecosystem, not in games.  \n"
            "Not Games - It's probably Steam for mobile games with (finally) updated interface.  "
        )
    },
    "Void": {
        "link": "https://t.me/notgames_bot/profile?startapp=786080766",
        "description": (
            "🌀 **Void Collection 🌀 - Digital Artifacts of Power**  \n\n"
            "Claim these legendary items before they disappear into the void! Each item unlocks  \n"
            "unique opportunities in the expanding Void universe.  \n\n"
            "Why collectors compete for them:  \n"
            "- Psychedelic #300: the rarest skin in the game, dedicated to the birthday of Not Coin  \n"
            "- Beta #9962: an indicator of the status of one of the first through a simple skin  \n"
            "- First Flight #605: one of the First Card  \n"
            "- MEME/FOOD/BADGE: cases with exclusive skins  \n\n"
            "These aren't just items - they're pieces of digital history.  \n"
            "Complete your collection today!  "
        )
    }
}

CONTACT_USER = "jamside_ay_lol"

# Menu Keyboards
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("NFT", callback_data="nft_menu")], 
        [InlineKeyboardButton("Stickers", callback_data="stickers_menu")],
        [InlineKeyboardButton("Collectible Items", callback_data="collectible_menu")],
        [InlineKeyboardButton("🌟 Donate", callback_data="donate")],
        [InlineKeyboardButton("🏆 Top Donors", callback_data="top_donors")]
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

# Bot Commands
async def set_commands(application: Application):
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("donate", "Support the developer"),
        BotCommand("refund", "Refund a donation (admin)"),
    ]
    await application.bot.set_my_commands(commands)

# Start command
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

# Cleanup temporary messages
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

# Show main menu
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, is_new=False) -> None:
    """Shows the main menu"""
    chat_id = update.effective_chat.id
    user_data = context.user_data
    text = (
        "🏛 **Welcome to the Digital Collectibles Showcase!** 🏛\n\n"
        "Discover rare NFTs, unique stickers, and exclusive collectible items ready to join your collection. "
        "All transactions are securely processed via Telegram Stars.\n\n"
        "🛍️ How to acquire items:\n"
        "1️⃣ Browse our collections below\n"
        "2️⃣ Found something you like? DM us for purchase or exchange options!\n\n"
        "⚠️ NFTs from this profile will be available for sale ONLY after 01.10.25 ⚠️"
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
                logger.info("Main menu unchanged")
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

# NFT Menu
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
            text="🎨 **NFT Collections**\n\nSelect an NFT to view details:",
            reply_markup=nft_menu_keyboard(),
            parse_mode="Markdown"
        )
        logger.info(f"NFT menu shown in message {user_data['base_message_id']}")
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.info("NFT menu unchanged")
        else:
            logger.error(f"NFT menu error: {e}")
            await show_main_menu(update, context, is_new=True)

# NFT Details
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
            caption=f"✨ **{nft_name}** ✨\n\n{nft['description']}\n\n✅ Available for sale/exchange",
            reply_markup=nft_detail_keyboard(nft_name),
            parse_mode="Markdown"
        )
        
        user_data.setdefault('temp_messages', []).append(message.message_id)
        logger.info(f"Temporary NFT message created: {message.message_id}")
        
    except Exception as e:
        logger.error(f"NFT detail error: {e}")
        message = await context.bot.send_message(
            chat_id=chat_id,
            text=f"✨ **{nft_name}** ✨\n\n{nft['description']}\n\n✅ Available for sale/exchange\n\n⚠️ Image temporarily unavailable",
            reply_markup=nft_detail_keyboard(nft_name),
            parse_mode="Markdown"
        )
        user_data.setdefault('temp_messages', []).append(message.message_id)
        logger.info(f"NFT text temporary message created: {message.message_id}")

# Stickers Menu
async def show_stickers_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the sticker menu"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_data = context.user_data
    
    await cleanup_temp_messages(context, chat_id)
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=user_data['base_message_id'],
            text="🎭 **Sticker Collections**\n\nSelect a sticker pack to view:",
            reply_markup=stickers_menu_keyboard(),
            parse_mode="Markdown"
        )
        logger.info(f"Sticker menu shown in message {user_data['base_message_id']}")
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.info("Sticker menu unchanged")
        else:
            logger.error(f"Sticker menu error: {e}")
            await show_main_menu(update, context, is_new=True)

# Sticker Details
async def show_sticker_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, sticker_name: str) -> None:
    """Shows sticker pack details"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_data = context.user_data
    
    await cleanup_temp_messages(context, chat_id)
    
    sticker_data = STICKER_COLLECTIONS[sticker_name]
    text = f"✨ **{sticker_name}** ✨\n\n{sticker_data['description']}\n"
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=user_data['base_message_id'],
            text=text,
            reply_markup=sticker_detail_keyboard(sticker_name),
            parse_mode="Markdown"
        )
        logger.info(f"Sticker details shown in message {user_data['base_message_id']}")
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.info("Sticker details unchanged")
        else:
            logger.error(f"Sticker details error: {e}")
            await show_main_menu(update, context, is_new=True)

# Collectibles Menu
async def show_collectible_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the collectible items menu"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_data = context.user_data
    
    await cleanup_temp_messages(context, chat_id)
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=user_data['base_message_id'],
            text="⚱️ **Collectible Items**\n\nSelect a category to view:",
            reply_markup=collectible_menu_keyboard(),
            parse_mode="Markdown"
        )
        logger.info(f"Collectible menu shown in message {user_data['base_message_id']}")
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.info("Collectible menu unchanged")
        else:
            logger.error(f"Collectible menu error: {e}")
            await show_main_menu(update, context, is_new=True)

# Collectible Details
async def show_collectible_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, item_name: str) -> None:
    """Shows collectible item details"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_data = context.user_data
    
    await cleanup_temp_messages(context, chat_id)
    
    item_data = COLLECTIBLE_ITEMS[item_name]
    text = f"✨ **{item_name}** ✨\n\n{item_data['description']}\n"
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=user_data['base_message_id'],
            text=text,
            reply_markup=collectible_detail_keyboard(item_name),
            parse_mode="Markdown"
        )
        logger.info(f"Collectible details shown in message {user_data['base_message_id']}")
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.info("Collectible details unchanged")
        else:
            logger.error(f"Collectible details error: {e}")
            await show_main_menu(update, context, is_new=True)

# Back to NFT Menu
async def handle_back_nft(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """NFT Back Button Handler"""
    query = update.callback_query
    await query.answer()
    
    await cleanup_temp_messages(context, query.message.chat_id)
    
    await show_nft_menu(update, context)

# Start Donation
async def start_donate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send donation invoice"""
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
            text="⚠️ Donations are temporarily unavailable. Please try again later."
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
            prices=[LabeledPrice(label="Telegram Stars", amount=1)],
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            is_flexible=False
        )
        logger.info(f"Donation invoice sent to {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Error sending invoice: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ An error occurred while creating the donation. Please try again later."
        )

# Pre-checkout Handler
async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles pre-checkout payment query"""
    query = update.pre_checkout_query
    try:
        await query.answer(ok=True)
        logger.info(f"Pre-checkout approved for {query.from_user.id}")
    except Exception as e:
        logger.error(f"Pre-checkout error: {e}")

# Successful Payment
async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles successful payment"""
    user = update.effective_user
    payment = update.message.successful_payment
    amount = payment.total_amount  # Amount in stars
    
    global donations_data
    
    # Update donation data
    user_id = str(user.id)
    transaction_id = payment.telegram_payment_charge_id
    
    if user_id in donations_data:
        donations_data[user_id]['total'] += amount
        donations_data[user_id]['count'] += 1
        donations_data[user_id]['transactions'].append({
            "id": transaction_id,
            "amount": amount,
            "timestamp": int(time.time())
        })
    else:
        donations_data[user_id] = {
            'username': user.username or user.full_name,
            'total': amount,
            'count': 1,
            'transactions': [{
                "id": transaction_id,
                "amount": amount,
                "timestamp": int(time.time())
            }]
        }
    
    save_donations(donations_data)
    
    # Send thank you message
    await update.message.reply_text(
        f"❤️ Thank you for your donation of {amount} stars!",
        reply_markup=donation_thanks_keyboard()
    )
    logger.info(f"Successful donation: {amount} stars from {user.id}")

# Show Top Donors
async def show_top_donors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows top donors leaderboard"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_data = context.user_data
    
    await cleanup_temp_messages(context, chat_id)
    
    # Reload data to get latest donations
    global donations_data
    donations_data = load_donations()
    
    # Sort donors by total amount
    sorted_donors = sorted(
        donations_data.items(),
        key=lambda x: x[1]['total'],
        reverse=True
    )[:10]  # Top 10
    
    text = "🏆 **Top Donors** 🏆\n\n"
    if not sorted_donors:
        text += "No donations yet. Be the first to donate!"
    else:
        for i, (user_id, data) in enumerate(sorted_donors, 1):
            username = data['username']
            total = data['total']
            count = data['count']
            text += f"{i}. {username}: {total} stars ({count} donations)\n"
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=user_data['base_message_id'],
            text=text,
            reply_markup=top_donors_keyboard(),
            parse_mode="Markdown"
        )
        logger.info(f"Top donors shown in message {user_data['base_message_id']}")
    except BadRequest as e:
        logger.error(f"Top donors error: {e}")
        await show_main_menu(update, context, is_new=True)

# Refund Command
async def refund(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Refund a donation (admin only)"""
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
        
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Usage: /refund <payment_charge_id>")
        return
        
    payment_charge_id = context.args[0]
    
    try:
        # Attempt to refund the payment
        await context.bot.refund_star_payment(payment_charge_id)
        
        # Update refunds data
        global refunds_data
        refunds_data[payment_charge_id] = {
            "timestamp": int(time.time()),
            "admin": update.effective_user.id
        }
        save_refunds(refunds_data)
        
        # Update donations data
        global donations_data
        for user_id, data in donations_data.items():
            for transaction in data['transactions']:
                if transaction['id'] == payment_charge_id:
                    data['total'] -= transaction['amount']
                    data['count'] -= 1
                    # Remove the transaction
                    data['transactions'] = [t for t in data['transactions'] if t['id'] != payment_charge_id]
                    break
        
        save_donations(donations_data)
        
        await update.message.reply_text(f"✅ Refund for payment {payment_charge_id} processed successfully.")
        logger.info(f"Refund processed: {payment_charge_id} by {update.effective_user.id}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Refund failed: {str(e)}")
        logger.error(f"Refund error: {e}")

# Button Handler
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
            # Clear all temporary messages and show main menu
            await cleanup_temp_messages(context, query.message.chat_id)
            await show_main_menu(update, context, is_new=True)
        elif data == "back_nft":
            await handle_back_nft(update, context)
    except Exception as e:
        logger.error(f"Button handler error: {e}")
        try:
            await query.answer("⚠️ An error occurred, please try again later")
        except:
            pass

# Flask Server for Keep-Alive
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

# Keep-Alive Function
def keep_alive():
    """Regularly sends requests to keep the bot alive"""
    while True:
        try:
            server_url = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:10000')
            health_url = f"{server_url}/health"
            
            response = requests.get(health_url, timeout=10)
            logger.info(f"Keep-alive request sent! Status: {response.status_code}")
        except Exception as e:
            logger.error(f"Keep-alive error: {e}")
        
        time.sleep(14 * 60)  # Sleep for 14 minutes

# Main Function
def main() -> None:
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN environment variable not set!")
        return
        
    if not PAYMENT_PROVIDER_TOKEN:
        logger.warning("⚠️ PAYMENT_PROVIDER_TOKEN not set. Donations will be disabled")
    
    if not ADMIN_USER_ID:
        logger.warning("⚠️ ADMIN_USER_ID not set. Refund command will be disabled")

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
        logger.info("🔔 Keep-alive function started (interval: 14 minutes)")
    else:
        logger.info("🖥️ Local Launch - Keep Alive feature disabled")

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Set bot commands
    application.post_init.set_commands = set_commands
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("donate", start_donate))
    application.add_handler(CommandHandler("refund", refund))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    logger.info("🤖 Bot is starting...")
    
    max_retries = 5
    retry_delay = 10
    
    # Run with retries
    for attempt in range(max_retries):
        try:
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
