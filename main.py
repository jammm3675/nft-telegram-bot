import logging
import os
import threading
import asyncio
import time
import requests
from flask import Flask
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    LabeledPrice,
    PreCheckoutQuery
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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '8010736258:AAF6_xDBDbWCGSACBLv8GI9o6WFWT21ZlBA')
PROVIDER_TOKEN = os.environ.get('PROVIDER_TOKEN', 'YOUR_PAYMENT_PROVIDER_TOKEN')
CURRENCY = 'XTR'  # Telegram Stars

# In-memory storage for donations
donators = {}

# NFT Collections
NFT_COLLECTIONS = {
    "Gems Winter Store": {
        "image": "https://i.ibb.co/JWsYQJwH/CARTONKI.png",
        "description": (
            "🎁 Gift box 🎁  \n"
            "by Gems Winter Store  \n\n"
            "Rarity: Rare  \n\n"
            "Own a piece of digital holiday magic! This rare gift box from Gems Winter Store \n"
            "Each box contains surprises that collectors dream about - a true digital time capsule of festive joy!"
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
            "Rare backstory with cult following."
        )
    },
    "Medieval Deck": {
        "image": "https://i.ibb.co/RTHnvCsr/TON-POKER.png",
        "description": (
            "🃏 Ace of Strength 🃏  \n"
            "by Medieval Deck\n\n"
            "Rarity: Epic\n\n"
            "This epic NFT was handcrafted by the visionary artist Ilya Stallone in collaboration with TON Poker."
        )
    },
    "Postmarks: Odds + Ends": {
        "image": "https://i.ibb.co/1tvKy4HV/Fool-moon.png",
        "description": (
            "🌙 Fool Moon 🌙 - Classic Digital Art  \n"
            "by Postmarks: Odds + Ends\n\n"
            "**Story**: The fool moon, the worm-eaten luminary: a drunken sanctuary of the bewildered,  \n"
            "a lighthouse flickering from all sides. You get distracted, wandering like a sleeper –  \n"
            "that's how the zodiacs died, my friend. Not overthrown by force, not defeated by intellect,  \n"
            "but lost in delirium."
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
            "This drop is a symbol of the bright side of your inner strength."
        )
    },
    "Ton Space Badges": {
        "image": "https://i.ibb.co/LDDnhfXy/TonSpaceBadges.png",
        "description": (
            "🥇 Gold Badge 🥇 - Proof You Were EARLY  \n"
            "by Ton Space Badges\n\n"
            "Own a piece of TON Space history! This exclusive badge is your verifiable proof  \n"
            "that you recognized the potential of TON Space before anyone else.  \n"
            "No remints. No second drops. Just verifiable proof you were early."
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
            "Meet Dogs and get ready to meet your new best friend who’s always got your back (and your snacks)!"
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
            "- Recognized status in all Doge games"
        )
    },
    "Lost Dogs": {
        "sticker_url": "https://t.me/sticker_bot/?startapp=tid_Nzg2MDgwNzY2",
        "description": (
            "**•Magic of the Way #2871 - The Philosopher's Stone of Stickers** 🔮  \n\n"
            "Own the most mystical sticker in the Lost Dogs universe! This isn't just digital art - \n"
            "it's a key to hidden content and special privileges across the entire Lost Dogs ecosystem.  \n\n"
            "Who are these Lost Dogs? They have an NFT collection, a game, a cartoon, and an entire universe… all for fun?"
        )
    },
    "Not Coin": {
        "sticker_url": "https://t.me/sticker_bot/?startapp=tid_Nzg2MDgwNzY2",
        "description": (
            "**•Not Meme #2015 - The Icon that started a revolution** 🪙  \n\n"
            "Own a piece of crypto history! This legendary sticker launched a thousand memes  \n"
            "and became the symbol of the NotCoin phenomenon. More than digital art - it's a cultural artifact!  \n\n"
            "Probably nothing"
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
            "Biggest Telegram Battle, biggest social experiment, and now – biggest sticker flex"
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
            "Turn them into a corner of a profile, objects or even stickers."
        )
    },
    "Not Games": {
        "link": "https://t.me/notgames_bot/profile?startapp=786080766",
        "description": (
            "☀️ **Sun #103 ☀️ - the main source of energy**  \n\n"
            "It's not just a collectible - it's your way of expressing yourself in the ecosystem, not in games.  \n"
            "Not Games - It’s probably Steam for mobile games with (finally) updated interface."
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
            "Complete your collection today!"
        )
    }
}

CONTACT_USER = "jamside_ay_lol"

# ==================== SUPPORT/DONATION FUNCTIONS ====================

def support_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Support Project", callback_data="donate_stars")],
        [InlineKeyboardButton("🏆 Top Donators", callback_data="top_donators")],
        [InlineKeyboardButton("⬅️ Back", callback_data="home")]
    ])

def donate_amount_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data="support_menu")]
    ])

def top_donators_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="top_donators")],
        [InlineKeyboardButton("⭐ Support Project", callback_data="donate_stars")],
        [InlineKeyboardButton("⬅️ Back", callback_data="support_menu")]
    ])

def format_top_donators():
    if not donators:
        return "🌟 No donations yet 😢\nBe the first to support our project!"
    
    sorted_donators = sorted(donators.items(), 
                            key=lambda x: x[1]['total'], 
                            reverse=True)[:10]
    
    result = "🏆 Top Donators:\n\n"
    for i, (user_id, data) in enumerate(sorted_donators, 1):
        stars = data['total']
        name = data['name']
        result += f"{i}. {name} - {stars}⭐\n"
    
    result += f"\nTotal collected: {sum(d['total'] for d in donators.values())}⭐"
    return result

async def show_support_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show support project menu"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_data = context.user_data
    
    await cleanup_temp_messages(context, chat_id)
    
    text = (
        "🌟 Support Our Project\n\n"
        "Your support helps us develop the bot and create new features!\n"
        "Every donation is appreciated and helps us improve."
    )
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=user_data['base_message_id'],
            text=text,
            reply_markup=support_menu_keyboard(),
            parse_mode="Markdown"
        )
    except BadRequest:
        await show_main_menu(update, context, is_new=True)

async def start_donate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start donation process"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_data = context.user_data
    
    await cleanup_temp_messages(context, chat_id)
    
    # Set donation awaiting state
    user_data['awaiting_donation'] = True
    
    try:
        message = await context.bot.send_message(
            chat_id=chat_id,
            text="💫 Enter the number of Telegram Stars for donation:",
            reply_markup=donate_amount_keyboard()
        )
        user_data.setdefault('temp_messages', []).append(message.message_id)
    except Exception as e:
        logger.error(f"Donation amount request error: {e}")

async def show_top_donators(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show top donators"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_data = context.user_data
    
    await cleanup_temp_messages(context, chat_id)
    
    top_text = format_top_donators()
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=user_data['base_message_id'],
            text=top_text,
            reply_markup=top_donators_keyboard(),
            parse_mode="Markdown"
        )
    except BadRequest:
        await show_support_menu(update, context)

async def process_donation_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process donation amount"""
    message = update.message
    chat_id = message.chat_id
    user_data = context.user_data
    
    if not user_data.get('awaiting_donation'):
        return
    
    try:
        stars = int(message.text)
        if stars < 1:
            await message.reply_text("Minimum donation is 1 star ⭐")
            return
        
        # Create payment
        prices = [LabeledPrice(label=f"{stars} Telegram Stars", amount=stars * 100)]
        
        # Send invoice
        await context.bot.send_invoice(
            chat_id=chat_id,
            title=f"Donation {stars}⭐",
            description="Thank you for supporting our project!",
            provider_token=PROVIDER_TOKEN,
            currency=CURRENCY,
            prices=prices,
            payload=f"donation_{message.from_user.id}",
            max_tip_amount=100000,
            suggested_tip_amounts=[100, 500, 1000, 5000]
        )
        
        # Reset state
        user_data['awaiting_donation'] = False
        
        # Clean temp messages
        await cleanup_temp_messages(context, chat_id)
        
    except ValueError:
        await message.reply_text("Please enter a whole number (e.g. 50)")

async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Confirm payment"""
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle successful payment"""
    message = update.message
    user = message.from_user
    payment = message.successful_payment
    stars = payment.total_amount // 100
    
    # Update donator info
    if user.id not in donators:
        donators[user.id] = {
            'name': user.full_name,
            'total': stars
        }
    else:
        donators[user.id]['total'] += stars
    
    # Format response
    text = (
        f"🎉 {user.full_name}, thank you for donating {stars}⭐!\n\n"
        "Your support means a lot to us!\n\n"
        f"Your rank in top donators: #{sorted(donators.items(), key=lambda x: x[1]['total'], reverse=True).index((user.id, donators[user.id])) + 1}🏅"
    )
    
    await message.reply_text(text)

# ==================== MAIN BOT FUNCTIONS ====================

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Collectibles", callback_data="collectible_menu")],
        [
            InlineKeyboardButton("NFT", callback_data="nft_menu"),
            InlineKeyboardButton("Stickers", callback_data="stickers_menu")
        ],
        [InlineKeyboardButton("🌟 Support Project", callback_data="support_menu")]
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
    user_data['awaiting_donation'] = False
    
    await show_main_menu(update, context, is_new=True)

async def cleanup_temp_messages(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Delete all temporary messages"""
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
    """Show main menu"""
    chat_id = update.effective_chat.id
    user_data = context.user_data
    text = (
        "🏛 **Welcome to the Digital Collectibles Showcase!** 🏛\n\n"
        "Discover rare NFTs, unique stickers, and collectible items available for acquisition. "
        "All transactions are secured via @GiftElfRobot.\n\n"
        "🛍️ How to purchase:\n"
        "1️⃣ Browse our collections below\n"
        "2️⃣ Found something you like? Contact us for purchase or exchange!\n\n"
        "⚠️ NFTs from this profile will be available for sale ONLY from 01.10.25 ⚠️\n\n"
        "🌟 Support our project with Telegram Stars!"
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
                logger.info("Message doesn't require changes (main menu)")
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

async def show_nft_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show NFT menu"""
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
        logger.info(f"NFT menu shown in message {user_data['base_message_id']}")
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.info("NFT message doesn't require changes")
        else:
            logger.error(f"NFT menu error: {e}")
            await show_main_menu(update, context, is_new=True)

async def show_nft_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, nft_name: str) -> None:
    """Show NFT details"""
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
        logger.error(f"NFT details error: {e}")
        message = await context.bot.send_message(
            chat_id=chat_id,
            text=f"✨ **{nft_name}** ✨\n\n{nft['description']}\n\n✅ Available for sale/exchange\n\n⚠️ Image temporarily unavailable",
            reply_markup=nft_detail_keyboard(nft_name),
            parse_mode="Markdown"
        )
        user_data.setdefault('temp_messages', []).append(message.message_id)
        logger.info(f"NFT text temporary message created: {message.message_id}")

async def show_stickers_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show stickers menu"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_data = context.user_data
    
    await cleanup_temp_messages(context, chat_id)
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=user_data['base_message_id'],
            text="🎭 **Sticker Collections**\n\nSelect a sticker pack:",
            reply_markup=stickers_menu_keyboard(),
            parse_mode="Markdown"
        )
        logger.info(f"Sticker menu shown in message {user_data['base_message_id']}")
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.info("Sticker message doesn't require changes")
        else:
            logger.error(f"Sticker menu error: {e}")
            await show_main_menu(update, context, is_new=True)

async def show_sticker_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, sticker_name: str) -> None:
    """Show sticker details"""
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
            logger.info("Sticker details don't require changes")
        else:
            logger.error(f"Sticker details error: {e}")
            await show_main_menu(update, context, is_new=True)

async def show_collectible_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show collectible items menu"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_data = context.user_data
    
    await cleanup_temp_messages(context, chat_id)
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=user_data['base_message_id'],
            text="⚱️ **Collectible Items**\n\nSelect a category:",
            reply_markup=collectible_menu_keyboard(),
            parse_mode="Markdown"
        )
        logger.info(f"Collectible menu shown in message {user_data['base_message_id']}")
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.info("Collectible menu doesn't require changes")
        else:
            logger.error(f"Collectible menu error: {e}")
            await show_main_menu(update, context, is_new=True)

async def show_collectible_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, item_name: str) -> None:
    """Show collectible item details"""
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
            logger.info("Collectible details don't require changes")
        else:
            logger.error(f"Collectible details error: {e}")
            await show_main_menu(update, context, is_new=True)

async def handle_back_nft(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle NFT back button"""
    query = update.callback_query
    await query.answer()
    
    await cleanup_temp_messages(context, query.message.chat_id)
    
    await show_nft_menu(update, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback buttons"""
    query = update.callback_query
    data = query.data

    try:
        if data == "nft_menu":
            await show_nft_menu(update, context)
        elif data == "stickers_menu":
            await show_stickers_menu(update, context)
        elif data == "collectible_menu":
            await show_collectible_menu(update, context)
        elif data == "support_menu":
            await show_support_menu(update, context)
        elif data == "donate_stars":
            await start_donate(update, context)
        elif data == "top_donators":
            await show_top_donators(update, context)
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
            await show_main_menu(update, context)
        elif data == "back_nft":
            await handle_back_nft(update, context)
    except Exception as e:
        logger.error(f"Button handler error: {e}")
        try:
            await query.answer("⚠️ An error occurred, please try again later")
        except:
            pass

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
    """Regularly ping server to keep bot awake"""
    while True:
        try:
            server_url = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:10000')
            health_url = f"{server_url}/health"
            
            response = requests.get(health_url, timeout=10)
            logger.info(f"Wake-up request sent! Status: {response.status_code}")
        except Exception as e:
            logger.error(f"Wake-up error: {e}")
        
        time.sleep(14 * 60)

def main() -> None:
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not set!")
        return

    server_thread = threading.Thread(target=run_flask_server)
    server_thread.daemon = True
    server_thread.start()
    logger.info(f"🌐 HTTP server running on port {os.environ.get('PORT', 10000)}")

    if os.environ.get('RENDER'):
        wakeup_thread = threading.Thread(target=keep_alive)
        wakeup_thread.daemon = True
        wakeup_thread.start()
        logger.info("🔔 Keep-alive activated (interval: 14 minutes)")
    else:
        logger.info("🖥️ Local execution - Keep-alive disabled")

    application = Application.builder().token(BOT_TOKEN).build()
    
    # Payment handlers
    application.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_donation_amount))
    
    # Main handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("donate", start_donate))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🤖 Bot started! Waiting for messages...")
    
    max_retries = 5
    retry_delay = 10
    
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
