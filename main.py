import logging
import os
import threading
import asyncio
import time
import requests
from io import BytesIO
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError, BadRequest, Conflict

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== КОНФИГУРАЦИЯ =====
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7953613164:AAF2sa_5nwE45LCcn-7dB_saJOPnPS_Z0F8')

# Описания NFT коллекций
NFT_COLLECTIONS = {
    "Postmarks: The Jaegers": {
        "image": "https://i.ibb.co/MyCJ8J33/NIX.png",
        "description": (
            "**NIX**\n"
            "by Postmarks: The Jaegers\n\n"
            "Rarity: Rare\n\n"
            "**Story**: Once one of the Jaegers tried to fight one of the ancient titans "
            "in the Pacific Ocean, but was defeated and now his body lies lifeless at a depth of 10 kilometers. "
            "But who knows, maybe he's just accumulating energy.\n"
        )
    },
    "Medieval Deck": {
        "image": "https://i.ibb.co/RTHnvCsr/TON-POKER.png",
        "description": (
            "**Ace of Strength**\n"
            "by Medieval Deck\n\n"
            "Rarity: Epic\n\n"
            "Ilya Stallone crafted this NFT together with TON Poker, the way a storyteller weaves a legend: "
            "with irony, with mystery, with fire."
        )
    },
    "Postmarks: Odds + Ends": {
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
    "Lost Dogs: The Hint": {
        "image": "https://i.ibb.co/gZ20qd68/Lost-Dogs.png",
        "description": (
            "**The League**\n"
            "by Lost Dogs: The Hint\n\n"
            "Rarity: Rare\n\n"
            "Sometimes you need to look at the bigger picture to understand the hint. "
            "During times of great resistance, the generals insisted on Tin foil hats, "
            "the leaders advocated for Evacuation, and individual dogs formed units to build a Dome. "
        )
    },
    "Gems Winter Store": {
        "image": "https://i.ibb.co/JWsYQJwH/CARTONKI.png",
        "description": (
            "**Gift box**\n"
            "by Gems Winter Store\n\n"
            "Rarity: Rare\n\n"
            "Happy New Year! May 2025 bring you inspiration, good fortune, and countless joyful moments."
        )
    },
    "The Seven Virtues": {
        "image": "https://i.ibb.co/ympwRnF8/TheSevenVirtues.png",
        "description": (
            "**Patience Postmark**\n"
            "by The Seven Virtues\n\n"
            "Rarity: Rare\n\n"
            "The Seven Virtues is a collaboration between the artist Olyabolyaboo and Cheques Corp., continuing the narrative of -The Seven Deadly Sins- "
            "While the sins made us reflect on our weaknesses, this collection inspires action. Humility, generosity, "
            "patience, purity, kindness, temperance, and diligence — seven principles that create a new story. "
            "This drop is a symbol of the bright side of your inner strength. "
        )
    },
    "Ton Space Badges": {
        "image": "https://i.ibb.co/LDDnhfXy/TonSpaceBadges.png",
        "description": (
            "**Gold Badge**\n"
            "by Ton Space Badges\n\n"
            "TON Space Badges is an exclusive NFT collection by TON Space.  "
            "Forged in the early orbit of the TON ecosystem, these badges were unlocked by users who fueled their journey with Stars. "
            "Each badge is a limited collectible — a snapshot of early activity within TON Space. No remints. "
            "No second drops. Just verifiable proof you were early. "
        )
    }
}

# Стикерпаки с описаниями
STICKER_COLLECTIONS = {
    "Not Coin": {
        "sticker_url": "https://t.me/sticker_bot/?startapp=tid_Nzg2MDgwNzY2",
        "description": (
            "• Not Meme #2015  \n\n"
            "**Price:** from 299 Ton\n\n\n"
            "Probably nothing "
        )
    },
    "Lost Dogs": {
        "sticker_url": "https://t.me/sticker_bot/?startapp=tid_Nzg2MDgwNzY2",
        "description": (
            "• Magic of the Way #2871  \n\n"
            "**Price:** from 9.99 Ton\n\n\n"
            "Who are these Lost Dogs? They have an NFT collection, a game, a cartoon, and an entire universe… all for fun? "
        )
    },
    "Not Pixel": {
        "sticker_url": "https://t.me/sticker_bot/?startapp=tid_Nzg2MDgwNzY2",
        "description": (
            "• Vice Pixel #1736  \n"
            "**Price:** from 9.99 Ton\n\n"
            "• Dogs Pixel #1023  \n"
            "**Price:** from 4.99 Ton\n\n"
            "• Grass Pixel #2536  \n"
            "**Price:** from 4.99 Ton\n\n"
            "• Mac Pixel #1736  \n"
            "**Price:** from 4.99 Ton\n\n\n"
            "Biggest Telegram Battle, biggest social experiment, and now – biggest sticker flex "
        )
    },
    "Dogs OG": {
        "sticker_url": "https://t.me/sticker_bot/?startapp=tid_Nzg2MDgwNzY2",
        "description": (
            "• Bow Tie #4780  \n"
            "**Price:** from 6.99 Ton\n\n"
            "• One Piece #6673  \n"
            "**Price:** from 5.99 Ton\n\n"
            "• Panama #1417  \n"
            "**Price:** from 3.99 Ton\n\n"
            "• Kamikaze #4812  \n\n"
            "**Price:** from 2.99 Ton\n\n\n"
            "Meet Dogs and get ready to meet your new best friend who’s always got your back (and your snacks)! "
        )
    },
    "Dogs Rewards": {
        "sticker_url": "https://t.me/sticker_bot/?startapp=tid_Nzg2MDgwNzY2",
        "description": (
            "• Full dig #4453  \n\n"
            "**Price:** from 9.99 Ton\n" 
        )
    }
}

# Контакт для покупки/обмена
CONTACT_USER = "jamside_ay_lol"

# ===== Кнопошки =====
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("NFT", callback_data="nft_menu")],
        [InlineKeyboardButton("Stickers", callback_data="stickers_menu")]
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

# ===== Обработка =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user_data = context.user_data
    
    # Полная очистка предыдущего состояния
    if 'base_message_id' in user_data:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=user_data['base_message_id']
            )
        except TelegramError:
            pass
    
    # Сбрасываем состояние
    user_data.clear()
    user_data['temp_messages'] = []
    
    # Создаем новое основное сообщение
    await show_main_menu(update, context, is_new=True)

async def cleanup_temp_messages(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Удаляет все временные сообщения и очищает список"""
    user_data = context.user_data
    if 'temp_messages' not in user_data:
        return
    
    # Удаляем сообщения в обратном порядке (новые сначала)
    for msg_id in reversed(user_data['temp_messages']):
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            logger.info(f"Удалено временное сообщение: {msg_id}")
        except TelegramError as e:
            if "message to delete not found" not in str(e).lower():
                logger.error(f"Ошибка удаления сообщения {msg_id}: {e}")
    
    # Очищаем список
    user_data['temp_messages'] = []

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, is_new=False) -> None:
    """Показывает главное меню"""
    chat_id = update.effective_chat.id
    user_data = context.user_data
    text = (
        "🌟 **NFTs for sale** 🌟\n\n"
        "This bot represents all NFTs that are ready to pass into the hands of a new owner :) \n\n"
        "To avoid scams, transactions are conducted through: @GiftElfRobot \n\n"
        "⚠️ NFTs from the profile are put up for sale ONLY from 01.10.25 ⚠️\n"
    )
    
    # Всегда очищаем временные сообщения при показе главного меню
    await cleanup_temp_messages(context, chat_id)
    
    if is_new or 'base_message_id' not in user_data:
        # Создаем новое основное сообщение
        message = await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )
        user_data['base_message_id'] = message.message_id
        logger.info(f"Создано новое основное сообщение: {message.message_id}")
    else:
        try:
            # Редактируем существующее сообщение
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=user_data['base_message_id'],
                text=text,
                reply_markup=main_menu_keyboard(),
                parse_mode="Markdown"
            )
            logger.info(f"Обновлено основное сообщение: {user_data['base_message_id']}")
        except BadRequest as e:
            if "message is not modified" in str(e).lower():
                # Игнорируем если сообщение не изменилось
                logger.info("Сообщение не требует изменений (main menu)")
            else:
                logger.error(f"Ошибка главного меню: {e}")
                # Создаем новое сообщение при серьезной ошибке
                message = await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=main_menu_keyboard(),
                    parse_mode="Markdown"
                )
                user_data['base_message_id'] = message.message_id
                logger.info(f"Создано новое основное сообщение из-за ошибки: {message.message_id}")

async def show_nft_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает меню NFT"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_data = context.user_data
    
    # Очищаем временные сообщения
    await cleanup_temp_messages(context, chat_id)
    
    try:
        # Редактируем основное сообщение
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=user_data['base_message_id'],
            text="🎨 **NFT Collections**\n\nSelect an NFT to view:",
            reply_markup=nft_menu_keyboard(),
            parse_mode="Markdown"
        )
        logger.info(f"Показано меню NFT в сообщении {user_data['base_message_id']}")
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.info("Сообщение NFT не требует изменений")
        else:
            logger.error(f"Ошибка меню NFT: {e}")
            # При критической ошибке создаем новое основное сообщение
            await show_main_menu(update, context, is_new=True)

async def show_nft_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, nft_name: str) -> None:
    """Показывает детали NFT"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_data = context.user_data
    
    # Очищаем предыдущие временные сообщения
    await cleanup_temp_messages(context, chat_id)
    
    nft = NFT_COLLECTIONS[nft_name]
    
    try:
        # Отправляем временное сообщение с изображением
        message = await context.bot.send_photo(
            chat_id=chat_id,
            photo=nft['image'],
            caption=f"✨ **{nft_name}** ✨\n\n{nft['description']}\n\n✅ Ready for sale/exchange",
            reply_markup=nft_detail_keyboard(nft_name),
            parse_mode="Markdown"
        )
        
        # Сохраняем ID временного сообщения
        user_data.setdefault('temp_messages', []).append(message.message_id)
        logger.info(f"Создано временное сообщение NFT: {message.message_id}")
        
    except Exception as e:
        logger.error(f"Ошибка деталей NFT: {e}")
        # Отправляем текстовое сообщение как запасной вариант
        message = await context.bot.send_message(
            chat_id=chat_id,
            text=f"✨ **{nft_name}** ✨\n\n{nft['description']}\n\n✅ Ready for sale/exchange\n\n⚠️ Image is temporarily unavailable",
            reply_markup=nft_detail_keyboard(nft_name),
            parse_mode="Markdown"
        )
        user_data.setdefault('temp_messages', []).append(message.message_id)
        logger.info(f"Создано текстовое временное сообщение NFT: {message.message_id}")

async def show_stickers_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает меню стикеров"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_data = context.user_data
    
    # Очищаем временные сообщения
    await cleanup_temp_messages(context, chat_id)
    
    try:
        # Редактируем основное сообщение
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=user_data['base_message_id'],
            text="🎭 **Stickerpacks**\n\nSelect a sticker collection:",
            reply_markup=stickers_menu_keyboard(),
            parse_mode="Markdown"
        )
        logger.info(f"Показано меню стикеров в сообщении {user_data['base_message_id']}")
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.info("Сообщение стикеров не требует изменений")
        else:
            logger.error(f"Ошибка меню стикеров: {e}")
            # При критической ошибке создаем новое основное сообщение
            await show_main_menu(update, context, is_new=True)

async def show_sticker_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, sticker_name: str) -> None:
    """Показывает детали стикерпака"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_data = context.user_data
    
    # Очищаем временные сообщения
    await cleanup_temp_messages(context, chat_id)
    
    sticker_data = STICKER_COLLECTIONS[sticker_name]
    text = f"✨ **{sticker_name}** ✨\n\n{sticker_data['description']}\n"
    
    try:
        # Редактируем основное сообщение
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=user_data['base_message_id'],
            text=text,
            reply_markup=sticker_detail_keyboard(sticker_name),
            parse_mode="Markdown"
        )
        logger.info(f"Показаны детали стикера в сообщении {user_data['base_message_id']}")
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.info("Сообщение деталей стикера не требует изменений")
        else:
            logger.error(f"Ошибка деталей стикера: {e}")
            # При критической ошибке создаем новое основное сообщение
            await show_main_menu(update, context, is_new=True)

async def handle_back_nft(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки Back в NFT"""
    query = update.callback_query
    await query.answer()
    
    # Очищаем временные сообщения
    await cleanup_temp_messages(context, query.message.chat_id)
    
    # Возвращаемся в меню NFT
    await show_nft_menu(update, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик всех callback-кнопок"""
    query = update.callback_query
    data = query.data

    try:
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
        elif data == "back_nft":
            await handle_back_nft(update, context)
    except Exception as e:
        logger.error(f"Ошибка в обработчике кнопок: {e}")
        try:
            await query.answer("⚠️ An error occurred, please try again later")
        except:
            pass

# ===== ВЕБ-СЕРВЕР =====
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

# ===== ФУНКЦИЯ ДЛЯ ПОДДЕРЖАНИЯ АКТИВНОСТИ НА RENDER =====
def keep_alive():
    """Регулярно отправляет запросы к серверу, чтобы бот не отключался"""
    while True:
        try:
            # Получаем URL сервера из переменной окружения
            server_url = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:10000')
            health_url = f"{server_url}/health"
            
            # Отправляем запрос к health-эндпоинту
            response = requests.get(health_url, timeout=10)
            logger.info(f"Отправлен запрос на пробуждение! Статус: {response.status_code}")
        except Exception as e:
            logger.error(f"Ошибка при пробуждении: {e}")
        
        time.sleep(14 * 60)  # 14 минут

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

    # Запускаем фоновый процесс для поддержания активности
    if os.environ.get('RENDER'):
        # Только на Render запускаем пробуждение
        wakeup_thread = threading.Thread(target=keep_alive)
        wakeup_thread.daemon = True
        wakeup_thread.start()
        logger.info("🔔 Запущена функция поддержания активности (интервал: 14 минут)")
    else:
        logger.info("🖥️ Локальный запуск - функция поддержания активности отключена")

    # Создаем и запускаем бота в основном потоке
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🤖 Бот запущен! Ожидание сообщений...")
    
    # Настройки для работы с несколькими пользователями
    max_retries = 5
    retry_delay = 10  # секунды
    
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
