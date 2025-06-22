import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN, COLLECTIONS, MAIN_MENU_IMAGE

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =КЛАВИАТУРА=
def main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Not Coin", callback_data="Not Coin"),
            InlineKeyboardButton("Lost Dogs", callback_data="Lost Dogs"),
        ],
        [
            InlineKeyboardButton("Not pixel", callback_data="Not pixel"),
            InlineKeyboardButton("Dogs OG", callback_data="Dogs OG"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def collection_keyboard(collection_name):
    keyboard = [
        [InlineKeyboardButton("🖼️ Посмотреть стикер", url=COLLECTIONS[collection_name]["sticker_url"])],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="back"),
            InlineKeyboardButton("🏠 Home", callback_data="home")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# =ОБРАБОТЧИКИ КОМАНД=
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_photo(
            photo=MAIN_MENU_IMAGE,
            caption="🌟 **NFT Marketplace**\nВыберите коллекцию:",
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )
    else:
        query = update.callback_query
        await query.answer()
        media = InputMediaPhoto(
            media=MAIN_MENU_IMAGE,
            caption="🌟 **NFT Marketplace**\nВыберите коллекцию:",
            parse_mode="Markdown"
        )
        await query.edit_message_media(media=media)
        await query.edit_message_reply_markup(reply_markup=main_menu_keyboard())

async def show_collection(update: Update, context: ContextTypes.DEFAULT_TYPE, collection_name: str) -> None:
    query = update.callback_query
    await query.answer()
    
    collection = COLLECTIONS[collection_name]
    caption = (
        f"✨ **{collection_name}** ✨\n\n"
        f"{collection['description']}\n\n"
        f"🔢 Количество: {collection['items']}\n"
        f"💰 Цена: {collection['price']}"
    )
    
    media = InputMediaPhoto(
        media=collection['image'],
        caption=caption,
        parse_mode="Markdown"
    )
    
    await query.edit_message_media(media=media)
    await query.edit_message_reply_markup(reply_markup=collection_keyboard(collection_name))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data
    
    if data in COLLECTIONS:
        await show_collection(update, context, data)
    elif data == "back" or data == "home":
        await show_main_menu(update, context)

# =ЗАПУСК БОТА=
def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    application.run_polling()

if __name__ == "__main__":
    main()
