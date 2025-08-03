import logging
import os
import threading
import time
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError, BadRequest, Conflict

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')

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

STICKER_COLLECTIONS = {
    "Dogs OG": {
        "sticker_url": "https://t.me/sticker_bot/?startapp=tid_Nzg2MDgwNzY2",
        "description": (
            "**Elite Dog Collection - Status Symbols on the Loose!** 🐶\n\n"
            "These aren't just stickers - they're membership cards to the most exclusive  \n"
            "Doge community on Telegram! Show off your status with these ultra-rare digital assets:  \n\n"
            "•Bow Tie #4780 - Absolutely Classic and Elegant  \n"
            "•One Piece #6673 - Iconic Character from the eponymous production  \n"
            "•Panama Hat #1417 - Summer Classic  \n\n"
            "Meet Dogs and get ready to meet your new best friend who’s always got your back (and your snacks)!  "
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
            "Not Games - It’s probably Steam for mobile games with (finally) updated interface.  "
        )
    },
    "Not Pixel": {
        "link": "https://t.me/notgames_bot/profile?startapp=786080766",
        "description": (
            "🌎 Big Bang 🌎 - the personification of anarchy and madness in the pixel world **  \n\n"
            "How Earth started. And that show. \n"
        )
    },
    "Void": {
        "link": "https://t.me/notgames_bot/profile?startapp=786080766",
        "description": (
            "🌀 **Void Collection 🌀 - Digital Artifacts of Power**  \n\n"
            "Claim these legendary items before they disappear into the void! Each item unlocks  \n"
            "unique opportunities in the expanding Void universe.  \n\n"
            "Why collectors compete for them:  \n"
            "- Psychedelic #300: The rarest skin in the game, dedicated to the birthday of Not Coin  \n"
            "- Beta #9962: An indicator of the status of one of the first through a simple skin  \n"
            "- First Flight #605: One of the First Card  \n"
            "- Not Stupid #5478: NOT STUPID. NOT STUPID.  \n"
            "- Lovepunch #762: Hits you with pureaffection. Then again.  \n"
            "- Looped Love #2895/5182/5388/5389: Stuckin a love loop. And now you are too.  \n\n"
            "These aren't just items - they're pieces of digital history.  \n"
            "Complete your collection today!  "
        )
    }
}

GIFTS = {
    "Witch Hat": {
        "description": (
            "🧙‍♀️ Witch Hat Collection 🧙‍♀️  \n\n"
            "Exclusive collectible gifts with unique characteristics:  \n\n"
            "• Rare combinations of models, backgrounds and patterns  \n\n"
            "Select an item for detailed information: \n"
            "- [Patchwork](t.me/nft/WitchHat-49198)  \n"
            "- [Old Ochre](t.me/nft/WitchHat-4941)  \n"
            "- [Vintage](t.me/nft/WitchHat-50026)  \n\n"
            "🚀 Price from 5 Ton per one  \n\n"
            "All gifts are sent via a secure bot @GiftElfRobot.  "
        )
    },
    "Snoop Dogg Collection": {
        "description": (
            "🐶 [Snoop Dogg](t.me/nft/SnoopDogg-65838) 🐶  \n\n"
            "• Exclusive gifts from the legendary @snoopdogg:  \n\n"
            "- Model: Blonde 2%  \n"
            "- Background: Ranger Green 1.5%  \n"
            "- Pattern: Headphones 0.5%  \n\n"
            "Each gift is a digital artifact with a history and a unique number.  \n\n"
            "All gifts are sent via a secure bot @GiftElfRobot.  "
        )
    }
}

CONTACT_USER = "not_jammm"

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("NFT", callback_data="nft_menu"),
            InlineKeyboardButton("Gifts", callback_data="gifts_menu")
        ],
        [
            InlineKeyboardButton("Stickers", callback_data="stickers_menu"),
            InlineKeyboardButton("Collectible Items", callback_data="collectible_menu")
        ]
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
            InlineKeyboardButton("⬅️ Back", callback_data="nft_menu"),
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

def gifts_menu_keyboard():
    buttons = []
    for gift_name in GIFTS:
        buttons.append([InlineKeyboardButton(gift_name, callback_data=f"gift_{gift_name}")])
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="home")])
    return InlineKeyboardMarkup(buttons)

def gift_detail_keyboard(gift_name):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💬 Buy", url=f"https://t.me/{CONTACT_USER}")
        ],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="gifts_menu"),
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
            logger.info(f"Deleted previous base message: {user_data['base_message_id']}")
        except TelegramError as e:
            logger.error(f"Error deleting previous base message: {e}")
    
    user_data.clear()
    user_data['temp_messages'] = []
    logger.info("User data cleared, starting new session")
    
    await show_main_menu(update, context, is_new=True)

async def cleanup_temp_messages(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Deletes all temporary messages and clears the list"""
    user_data = context.user_data
    if 'temp_messages' not in user_data:
        return
    
    logger.info(f"Cleaning up {len(user_data['temp_messages'])} temporary messages")
    
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
        "Discover rare NFTs, unique stickers, collectible items and exclusive gifts. "
        "All transactions are secure via @GiftElfRobot.\n\n"
        "🛍️ How to buy:\n"
        "1️⃣ Browse our collections below\n"
        "2️⃣ Found something? DM us for purchase/exchange!\n\n"
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
                logger.info("Main menu message not modified")
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
        logger.info(f"NFT menu shown in message {user_data['base_message_id']}")
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.info("NFT menu message not modified")
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
        logger.info(f"Temporary NFT message created: {message.message_id}")
        
    except Exception as e:
        logger.error(f"Error showing NFT details: {e}")
        message = await context.bot.send_message(
            chat_id=chat_id,
            text=f"✨ **{nft_name}** ✨\n\n{nft['description']}\n\n✅ Ready for sale/exchange\n\n⚠️ Image unavailable",
            reply_markup=nft_detail_keyboard(nft_name),
            parse_mode="Markdown"
        )
        user_data.setdefault('temp_messages', []).append(message.message_id)
        logger.info(f"NFT text temporary message created: {message.message_id}")

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
            text="🎭 **Stickerpacks**\n\nSelect a sticker collection:",
            reply_markup=stickers_menu_keyboard(),
            parse_mode="Markdown"
        )
        logger.info(f"Sticker menu shown in message {user_data['base_message_id']}")
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.info("Sticker menu message not modified")
        else:
            logger.error(f"Sticker menu error: {e}")
            await show_main_menu(update, context, is_new=True)

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
        logger.info(f"Showing sticker details in message {user_data['base_message_id']}")
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.info("Sticker details message not modified")
        else:
            logger.error(f"Sticker details error: {e}")
            await show_main_menu(update, context, is_new=True)

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
            text="⚱️ **Collectible Items**\n\nSelect a category:",
            reply_markup=collectible_menu_keyboard(),
            parse_mode="Markdown"
        )
        logger.info(f"Collectible menu shown in message {user_data['base_message_id']}")
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.info("Collectible menu message not modified")
        else:
            logger.error(f"Collectible menu error: {e}")
            await show_main_menu(update, context, is_new=True)

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
        logger.info(f"Showing collectible details in message {user_data['base_message_id']}")
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.info("Collectible details message not modified")
        else:
            logger.error(f"Collectible details error: {e}")
            await show_main_menu(update, context, is_new=True)

async def show_gifts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the gifts menu"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_data = context.user_data
    
    await cleanup_temp_messages(context, chat_id)
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=user_data['base_message_id'],
            text="🎁 **Exclusive Gifts**\n\nSelect a gift collection:",
            reply_markup=gifts_menu_keyboard(),
            parse_mode="Markdown"
        )
        logger.info(f"Gifts menu shown in message {user_data['base_message_id']}")
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.info("Gifts menu message not modified")
        else:
            logger.error(f"Gifts menu error: {e}")
            await show_main_menu(update, context, is_new=True)

async def show_gift_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, gift_name: str) -> None:
    """Shows gift details"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_data = context.user_data
    
    await cleanup_temp_messages(context, chat_id)
    
    gift_data = GIFTS[gift_name]
    text = f"✨ **{gift_name}** ✨\n\n{gift_data['description']}\n"
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=user_data['base_message_id'],
            text=text,
            reply_markup=gift_detail_keyboard(gift_name),
            parse_mode="Markdown"
        )
        logger.info(f"Showing gift details in message {user_data['base_message_id']}")
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.info("Gift details message not modified")
        else:
            logger.error(f"Gift details error: {e}")
            await show_main_menu(update, context, is_new=True)

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
        elif data == "gifts_menu":
            await show_gifts_menu(update, context)
        elif data.startswith("nft_"):
            nft_name = data[4:]
            await show_nft_detail(update, context, nft_name)
        elif data.startswith("sticker_"):
            sticker_name = data[8:]
            await show_sticker_detail(update, context, sticker_name)
        elif data.startswith("collectible_"):
            item_name = data[12:]
            await show_collectible_detail(update, context, item_name)
        elif data.startswith("gift_"):
            gift_name = data[5:]
            await show_gift_detail(update, context, gift_name)
        elif data == "home":
            await show_main_menu(update, context)
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
    """Regularly sends requests to keep the bot alive"""
    while True:
        try:
            server_url = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:10000')
            health_url = f"{server_url}/health"
            
            response = requests.get(health_url, timeout=10)
            logger.info(f"Wake up request sent! Status: {response.status_code}")
        except Exception as e:
            logger.error(f"Error while waking up: {e}")
        
        time.sleep(14 * 60)

def main() -> None:
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not installed!")
        return

    server_thread = threading.Thread(target=run_flask_server)
    server_thread.daemon = True
    server_thread.start()
    logger.info(f"🌐 HTTP server running on port {os.environ.get('PORT', 10000)}")

    if os.environ.get('RENDER'):
        wakeup_thread = threading.Thread(target=keep_alive)
        wakeup_thread.daemon = True
        wakeup_thread.start()
        logger.info("🔔 Keep-alive function started (interval: 14 minutes)")
    else:
        logger.info("🖥️ Local Launch - Keep Alive feature disabled")

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
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
                poll_interval=1.35
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
