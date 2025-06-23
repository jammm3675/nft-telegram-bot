import logging
import os
import threading
import asyncio
import requests
from io import BytesIO
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError, BadRequest

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== КОНФИГУРАЦИЯ =====
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7953613164:AAF2sa_5nwE45LCcn-7dB_saJOPnPS_Z0F8')

# Описания NFT коллекций с ПРЯМЫМИ ссылками на изображения
NFT_COLLECTIONS = {
    "NIX": {
        "image": "https://i.ibb.co/MyCJ8J33/NIX.png",
        "description": (
            "**NIX**\n"
            "by Postmarks: The Jaegers\n\n"
            "**Story**: Once one of the Jaegers tried to fight one of the ancient titans "
            "in the Pacific Ocean, but was defeated and now his body lies lifeless at a depth of 10 kilometers. "
            "But who knows, maybe he's just accumulating energy.\n"
        )
    },
    "TON POKER": {
        "image": "https://i.ibb.co/RTHnvCsr/TON-POKER.png",
        "description": (
            "**Ace of Strength**\n"
            "by Medieval Deck\n\n"
            "Ilya Stallone crafted this NFT together with TON Poker, the way a storyteller weaves a legend: "
            "with irony, with mystery, with fire."
        )
    },
    "Fool moon": {
        "image": "https://i.ibb.co/1tvKy4HV/Fool-moon.png",
        "description": (
            "**Fool Moon**\n"
            "by Postmarks: Odds + Ends\n\n"
            "The fool moon, the worm-eaten luminary: a drunken sanctuary of the bewildered, "
            "a lighthouse flickering from all sides. You get distracted, wandering like a sleeper – "
            "that's how the zodiacs died, my friend. Not overthrown by force, not defeated by intellect, "
            "but lost in delirium."
        )
    },
    "The League": {
        "image": "https://i.ibb.co/gZ20qd68/Lost-Dogs.png",
        "description": (
            "**The League**\n"
            "by Lost Dogs: The Hint\n\n"
            "Sometimes you need to look at the bigger picture to understand the hint. "
            "During times of great resistance, the generals insisted on Tin foil hats, "
            "the leaders advocated for Evacuation, and individual dogs formed units to build a Dome. "
        )
    },
    "CARTONKI": {
        "image": "https://i.ibb.co/JWsYQJwH/CARTONKI.png",
        "description": (
            "**Gift box**\n"
            "by Gems Winter Store\n\n"
            "Happy New Year! May 2025 bring you inspiration, good fortune, and countless joyful moments."
        )
    }
}

# Стикерпаки с описаниями
STICKER_COLLECTIONS = {
    "Not Coin": {
        "sticker_url": "https://t.me/sticker_bot/?startapp=tid_Nzg2MDgwNzY2",
        "description": (
            "**- Not Meme**\n"
            "Price: from 299 Ton\n\n"
        )
    },
    "Lost Dogs": {
        "sticker_url": "https://t.me/sticker_bot/?startapp=tid_Nzg2MDgwNzY2",
        "description": (
            "**- Magic of the Way**\n"
            "Price: from 9.99 Ton\n\n"
        )
    },
    "Not pixel": {
        "sticker_url": "https://t.me/sticker_bot/?startapp=tid_Nzg2MDgwNzY2",
        "description": (
            "**- Vice City**\n"
            "Price: from 9.99 Ton\n\n"
            "**- Dogs pixel**\n"
            "Price: from 4.99 Ton\n\n"
            "**- Grass**\n"
            "Price: from 4.99 Ton\n\n"
        )
    },
    "Dogs OG": {
        "sticker_url": "https://t.me/sticker_bot/?startapp=tid_Nzg2MDgwNzY2",
        "description": (
            "**- Bow Tie**\n"
            "Price: from 6.99 Ton\n\n"
            "**- One Piece**\n"
            "Price: from 5.99 Ton\n\n"
            "**- Panama**\n"
            "Price: from 3.99 Ton\n\n"
            "**- Kamikaze**\n"
            "Price: from 2.99 Ton\n\n"
        )
    }
}

# Контакт для покупки/обмена
CONTACT_USER = "jamside_ay_lol"

# ===== КЛАВИАТУРЫ =====
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("NFT", callback_data="nft_menu")],
        [InlineKeyboardButton("Stickers", callback_data="stickers_menu")]
    ])

def nft_menu_keyboard():
    buttons = []
    for nft_name in NFT_COLLECTIONS:
        buttons.append([InlineKeyboardButton(nft_name, callback_data=f"nft_{nft_name}")])
    buttons.append([InlineKeyboardButton("🏠 Home", callback_data="home")])
    return InlineKeyboardMarkup(buttons)

def nft_detail_keyboard(nft_name):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 DM(exchange)", url=f"https://t.me/{CONTACT_USER}"),
            InlineKeyboardButton("🏠 Home", callback_data="home")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="nft_menu")]
    ])

def stickers_menu_keyboard():
    buttons = []
    for sticker_name in STICKER_COLLECTIONS:
        buttons.append([InlineKeyboardButton(sticker_name, callback_data=f"sticker_{sticker_name}")])
    buttons.append([InlineKeyboardButton("🏠 Home", callback_data="home")])
    return InlineKeyboardMarkup(buttons)

def sticker_detail_keyboard(sticker_name):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🖼️ Look at the stickers", url=STICKER_COLLECTIONS[sticker_name]["sticker_url"]),
            InlineKeyboardButton("💰 DM(purchase)", url=f"https://t.me/{CONTACT_USER}")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="stickers_menu"),
            InlineKeyboardButton("🏠 Home", callback_data="home")
        ]
    ])

# ===== ОБРАБОТЧИКИ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "🌟 **NFTs for sale**\n\n"
        "This bot represents all NFTs that are ready to pass into the hands of a new owner :) \n\n"
        "To avoid scams, transactions are conducted through: @GiftElfRobot \n\n"
        "⚠️ NFTs from the profile are put up for sale ONLY from 01.10.25 ⚠️\n\n\n"
        "bot by jammm 🐱"
    )

    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")
    else:
        query = update.callback_query
        await query.answer()
        try:
            await query.edit_message_text(text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")
        except BadRequest:
            # Если сообщение не содержит текста (например, это фото), отправляем новое
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=text,
                reply_markup=main_menu_keyboard(),
                parse_mode="Markdown"
            )

async def show_nft_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        await query.edit_message_text(
            "🎨 **NFT Collections**\nSelect an NFT to view:",
            reply_markup=nft_menu_keyboard(),
            parse_mode="Markdown"
        )
    except BadRequest:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🎨 **NFT Collections**\nSelect an NFT to view:",
            reply_markup=nft_menu_keyboard(),
            parse_mode="Markdown"
        )

async def show_nft_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, nft_name: str) -> None:
    query = update.callback_query
    await query.answer()
    await asyncio.sleep(0.5)  # Задержка для предотвращения конфликтов

    nft = NFT_COLLECTIONS[nft_name]
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    
    logger.info(f"Отправка изображения для {nft_name}: {nft['image']}")
    
    try:
        # Отправляем изображение по прямой ссылке
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=nft['image'],
            caption=f"✨ **{nft_name}** ✨\n\n{nft['description']}\n\n✅ Ready for sale/exchange",
            reply_markup=nft_detail_keyboard(nft_name),
            parse_mode="Markdown"
        )
        
        # Удаляем предыдущее сообщение
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except BadRequest as e:
            logger.warning(f"Не удалось удалить сообщение: {e}")
        
    except TelegramError as e:
        logger.error(f"Ошибка при отправке изображения: {e}")
        try:
            # Скачиваем изображение и отправляем как файл
            response = requests.get(nft['image'])
            response.raise_for_status()
            
            photo_file = BytesIO(response.content)
            photo_file.name = f"{nft_name}.png"
            
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo_file,
                caption=f"✨ **{nft_name}** ✨\n\n{nft['description']}\n\n✅ Ready for sale/exchange",
                reply_markup=nft_detail_keyboard(nft_name),
                parse_mode="Markdown"
            )
            
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            except BadRequest as e:
                logger.warning(f"Не удалось удалить сообщение: {e}")
            
        except Exception as e2:
            logger.error(f"Ошибка при альтернативной отправке изображения: {e2}")
            # Отправляем текстовое сообщение
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"✨ **{nft_name}** ✨\n\n{nft['description']}\n\n✅ Ready for sale/exchange\n\n⚠️ Image is temporarily unavailable",
                    reply_markup=nft_detail_keyboard(nft_name),
                    parse_mode="Markdown"
                )
            except Exception as e3:
                logger.error(f"Ошибка при отправке текста: {e3}")

async def show_stickers_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        await query.edit_message_text(
            "🎭 **Stickerpacks**\nSelect a sticker collection:",
            reply_markup=stickers_menu_keyboard(),
            parse_mode="Markdown"
        )
    except BadRequest:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🎭 **Stickerpacks**\nSelect a sticker collection:",
            reply_markup=stickers_menu_keyboard(),
            parse_mode="Markdown"
        )

async def show_sticker_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, sticker_name: str) -> None:
    query = update.callback_query
    await query.answer()

    sticker_data = STICKER_COLLECTIONS[sticker_name]
    description = sticker_data["description"]

    text = f"✨ **{sticker_name}** ✨\n\n{description}\n\nSelect action:"

    try:
        await query.edit_message_text(
            text,
            reply_markup=sticker_detail_keyboard(sticker_name),
            parse_mode="Markdown"
        )
    except BadRequest:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=sticker_detail_keyboard(sticker_name),
            parse_mode="Markdown"
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data

    if data == "nft_menu":
        await show_nft_menu(update, context)
    elif data == "stickers_menu":
        await show_stickers_menu(update, context)
    elif data.startswith("nft_"):
        nft_name = data[4:]
        await show_nft_detail(update, context, nft_name)
    elif data.startswith("sticker_"):
        sticker_name = data[8:]
        await show_sticker_detail(update, context, sticker_name)
    elif data == "home":
        await show_main_menu(update, context)

# ===== ВЕБ-СЕРВЕР ДЛЯ UPTIMEROBOT =====
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

# ===== ЗАПУСК БОТА И СЕРВЕРА =====
def main() -> None:
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не установлен!")
        return

    # Запускаем HTTP сервер в отдельном потоке
    server_thread = threading.Thread(target=run_flask_server)
    server_thread.daemon = True
    server_thread.start()
    logger.info(f"🌐 HTTP server running on port {os.environ.get('PORT', 10000)}")

    # Создаем и запускаем бота в основном потоке
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🤖 Бот запущен! Ожидание сообщений...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
