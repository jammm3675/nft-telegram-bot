import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== КОНФИГУРАЦИЯ =====
BOT_TOKEN = "В7953613164:AAF2sa_5nwE45LCcn-7dB_saJOPnPS_Z0F8"

# Описания коллекций
COLLECTIONS = {
    "Not Coin": {
        "description": "🔥 Цифровые активы для будущей экономики\n\n"
                       "✅ Готов к продаже/обмену\n\n"
                       "Коллекция крипто-стикеров с уникальным дизайном и утилитами в экосистеме Notcoin",
        "price": "0.5 TON",
        "items": "150 NFT",
        "sticker_url": "https://t.me/sticker_bot?start=notcoin_stickers"
    },
    "Lost Dogs": {
        "description": "🐶 Коллекция потерянных пиксельных псов\n\n"
                       "✅ Готов к продаже/обмену\n\n"
                       "Эксклюзивные NFT с историей каждого пса, ищите своих фаворитов!",
        "price": "0.8 TON",
        "items": "200 NFT",
        "sticker_url": "https://t.me/sticker_bot?start=lostdogs_stickers"
    },
    "Not pixel": {
        "description": "🎮 Минималистичные пиксельные арты\n\n"
                       "✅ Готов к продаже/обмену\n\n"
                       "Ретро-стиль в современном исполнении. Коллекция для истинных ценителей пиксельного искусства",
        "price": "0.6 TON",
        "items": "180 NFT",
        "sticker_url": "https://t.me/sticker_bot?start=notpixel_stickers"
    },
    "Dogs OG": {
        "description": "🐕 Эксклюзивные собаки оригинальной генерации\n\n"
                       "✅ Готов к продаже/обмену\n\n"
                       "Легендарная коллекция первых NFT-собак с особыми привилегиями для владельцев",
        "price": "1.2 TON",
        "items": "100 NFT",
        "sticker_url": "https://t.me/sticker_bot?start=dogsog_stickers"
    }
}

# ===== КЛАВИАТУРЫ =====
def main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Not Coin", callback_data="Not Coin"),
            InlineKeyboardButton("Lost Dogs", callback_data="Lost Dogs"),
        ],
        [
            InlineKeyboardButton("Not pixel", callback_data="Not pixel"),
            InlineKeyboardButton("Dogs OG", callback_data="Dogs OG"),
        ],
        [InlineKeyboardButton("🎭 Стикеры", callback_data="stickers")]
    ]
    return InlineKeyboardMarkup(keyboard)

def collection_keyboard(collection_name):
    keyboard = [
        [InlineKeyboardButton("🖼️ Посмотреть стикеры", url=COLLECTIONS[collection_name]["sticker_url"])],
        [InlineKeyboardButton("🔙 Назад к коллекциям", callback_data="back_collections")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="home")]
    ]
    return InlineKeyboardMarkup(keyboard)

def stickers_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Not Coin", url=COLLECTIONS["Not Coin"]["sticker_url"]),
            InlineKeyboardButton("Lost Dogs", url=COLLECTIONS["Lost Dogs"]["sticker_url"]),
        ],
        [
            InlineKeyboardButton("Not pixel", url=COLLECTIONS["Not pixel"]["sticker_url"]),
            InlineKeyboardButton("Dogs OG", url=COLLECTIONS["Dogs OG"]["sticker_url"]),
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ===== ОБРАБОТЧИКИ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "🌟 *NFT Marketplace*\n\n"
        "Добро пожаловать в наш магазин NFT! Выберите коллекцию для просмотра "
        "или перейдите в раздел стикеров.\n\n"
        "Все представленные NFT готовы к продаже или обмену!"
    )
    
    if update.message:
        await update.message.reply_text(
            text=text,
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )
    else:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            text=text,
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )

async def show_collection(update: Update, context: ContextTypes.DEFAULT_TYPE, collection_name: str) -> None:
    query = update.callback_query
    await query.answer()
    
    collection = COLLECTIONS[collection_name]
    caption = (
        f"✨ *{collection_name}* ✨\n\n"
        f"{collection['description']}\n\n"
        f"🔢 *Количество:* {collection['items']}\n"
        f"💰 *Цена:* {collection['price']}\n\n"
        "_Выберите действие ниже_"
    )
    
    await query.edit_message_text(
        text=caption,
        reply_markup=collection_keyboard(collection_name),
        parse_mode="Markdown"
    )

async def show_stickers_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    text = (
        "🎭 *Стикерпаки NFT коллекций*\n\n"
        "Выберите коллекцию, чтобы посмотреть стикеры в @sticker_bot:\n\n"
        "После нажатия кнопки вы перейдете в бот стикеров, "
        "где сможете просмотреть и добавить стикеры в свой Telegram."
    )
    
    await query.edit_message_text(
        text=text,
        reply_markup=stickers_menu_keyboard(),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data
    
    if data in COLLECTIONS:
        await show_collection(update, context, data)
    elif data == "stickers":
        await show_stickers_menu(update, context)
    elif data == "back_collections":
        text = (
            "🌟 *NFT Коллекции*\n\n"
            "Выберите интересующую вас коллекцию для просмотра деталей:"
        )
        await query.answer()
        await query.edit_message_text(
            text=text,
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )
    elif data == "back" or data == "home":
        await show_main_menu(update, context)

# ===== ЗАПУСК БОТА =====
def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.run_polling()

if __name__ == "__main__":
    main()
