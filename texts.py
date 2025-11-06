from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.helpers import escape_markdown

# ... (existing functions) ...

def get_share_card(nft_data, owner_username):
    """Creates the text and keyboard for an NFT share card."""
    name = nft_data.get('metadata', {}).get('name', 'Unnamed NFT')
    collection = nft_data.get('collection', {}).get('name', 'Unknown Collection')
    nft_address = nft_data.get('address', '')
    collection_address = nft_data.get('collection', {}).get('address', '')

    getgems_url = f"https://getgems.io/collection/{collection_address}/{nft_address}"

    text = f"""
🎴 *{escape_markdown(name, 2)}*

*Коллекция:* {escape_markdown(collection, 2)}
*Владелец:* @{owner_username}

🔗 [Открыть в Getgems]({getgems_url})

💬 _Хотите связаться с владельцем? Нажмите на кнопку ниже\\!_
"""

    keyboard = [
        [InlineKeyboardButton("💌 Написать владельцу", url=f"https://t.me/{owner_username}")],
        [InlineKeyboardButton("🔗 Поделиться", switch_inline_query=nft_address)]
    ]

    return text, InlineKeyboardMarkup(keyboard)

# This is a placeholder for the rest of the file
def shorten_address(address: str, start=4, end=4):
    """Shortens a wallet address for display."""
    return f"{address[:start]}...{address[-end:]}"

def get_start_menu():
    """Returns the text and keyboard for the main menu."""
    disclaimer_raw = "Быстрый шаринг одной командой • Ссылки на Getgems и TonViewer • Прямой контакт с владельцем"
    disclaimer_text_md = f">_{escape_markdown(disclaimer_raw, 2)}_"

    text = f"""
*Добро пожаловать!*

• Привяжите TON кошелек
• Показывайте свои NFT друзьям
• Получайте предложения о покупке

{disclaimer_text_md}
"""
    keyboard = [
        [InlineKeyboardButton("👛 Мои кошельки", callback_data='wallets_menu')],
        [InlineKeyboardButton("🖼️ Мои NFT", callback_data='my_nft_menu')],
        [InlineKeyboardButton("❓ Как поделиться?", callback_data='help_menu')]
    ]
    return text, InlineKeyboardMarkup(keyboard)

def get_wallets_menu(wallets=None):
    """Returns the text and keyboard for the wallet management menu."""
    if wallets is None:
        wallets = []

    wallets_list = [f"• `{shorten_address(w['wallet_address'])}`" for w in wallets] if wallets else ["У вас пока нет привязанных кошельков."]
    wallets_text = "\n".join(wallets_list)

    disclaimer_raw = "Вы можете добавить или удалить кошельки в любое время."
    disclaimer_text_md = f">_{escape_markdown(disclaimer_raw, 2)}_"

    text = f"""
👛 *Ваши кошельки*

{wallets_text}

{disclaimer_text_md}
"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить кошелек", callback_data='add_wallet')],
        [InlineKeyboardButton("➖ Удалить кошелек", callback_data='remove_wallet_menu')] if wallets else [],
        [InlineKeyboardButton("🔙 В меню", callback_data='main_menu')]
    ]
    # A bit of a hack to filter out the empty list from the keyboard
    keyboard = [row for row in keyboard if row]
    return text, InlineKeyboardMarkup(keyboard)

def get_add_wallet_prompt():
    """Returns the text and keyboard for the add wallet prompt."""
    text = "Отправьте мне адрес вашего TON кошеля для привязки."
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='wallets_menu')]]
    return text, InlineKeyboardMarkup(keyboard)

def get_remove_wallet_menu(wallets):
    """Returns a menu to select which wallet to remove."""
    keyboard = []
    for wallet in wallets:
        address = wallet['wallet_address']
        keyboard.append([InlineKeyboardButton(f"🗑️ {shorten_address(address)}", callback_data=f"confirm_remove_{address}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='wallets_menu')])
    text = "Выберите кошелек, который хотите удалить:"
    return text, InlineKeyboardMarkup(keyboard)

def get_confirm_remove_wallet_menu(wallet_address):
    """Asks for confirmation before removing a wallet."""
    text = f"Вы уверены, что хотите удалить кошелек `{shorten_address(wallet_address)}`?"
    keyboard = [
        [InlineKeyboardButton("✅ Да, удалить", callback_data=f"remove_{wallet_address}")],
        [InlineKeyboardButton("❌ Нет, отмена", callback_data='wallets_menu')]
    ]
    return text, InlineKeyboardMarkup(keyboard)

def get_help_menu():
    """Returns the text and keyboard for the help menu."""
    disclaimer_raw = "Это самый быстрый способ поделиться NFT с друзьями в любом чате!"
    disclaimer_text_md = f">_{escape_markdown(disclaimer_raw, 2)}_"
    text = f"""
❓ *Как поделиться NFT?*

1️⃣ *Через команду /share*:
   \\- Отправьте команду `/share <адрес_NFT>` в чат со мной\\.
   \\- Пример: `/share EQ...`

2️⃣ *Через инлайн\\-режим*:
   \\- В любом чате введите `@имя_бота <адрес_NFT>`\\.
   \\- Выберите NFT из появившегося списка\\.

{disclaimer_text_md}
"""
    keyboard = [[InlineKeyboardButton("🔙 В меню", callback_data='main_menu')]]
    return text, InlineKeyboardMarkup(keyboard)

def get_my_nft_menu_loading():
    """Returns a loading message for the NFT menu."""
    text = "🔄 *Загружаем ваши NFT...*\n\nПожалуйста, подождите. Это может занять некоторое время."
    keyboard = [[InlineKeyboardButton("🔙 В меню", callback_data='main_menu')]]
    return text, InlineKeyboardMarkup(keyboard)

def get_my_nft_menu(nfts, page=0, items_per_page=5):
    """Returns the text and keyboard for the NFT viewing menu with pagination."""
    if not nfts:
        text = "🖼️ *Ваши NFT*\n\nУ вас пока нет NFT или не удалось их загрузить. Попробуйте обновить."
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data='my_nft_menu_refresh')],
            [InlineKeyboardButton("🔙 В меню", callback_data='main_menu')]
        ]
        return text, InlineKeyboardMarkup(keyboard)

    start_index = page * items_per_page
    end_index = start_index + items_per_page
    paginated_nfts = nfts[start_index:end_index]

    nft_list_text = []
    for nft in paginated_nfts:
        name = nft.get('metadata', {}).get('name', 'Unnamed NFT')
        collection = nft.get('collection', {}).get('name', 'Unknown Collection')
        nft_list_text.append(f"🎴 *{escape_markdown(name, 2)}*\n_{escape_markdown(collection, 2)}_")

    text = "🖼️ *Ваши NFT для шаринга*\n\n" + "\n\n".join(nft_list_text)

    # Pagination buttons
    total_pages = (len(nfts) + items_per_page - 1) // items_per_page
    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data=f'nft_page_{page - 1}'))

    if total_pages > 1:
        pagination_buttons.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data='noop')) # noop button

    if end_index < len(nfts):
        pagination_buttons.append(InlineKeyboardButton("▶️ Вперед", callback_data=f'nft_page_{page + 1}'))

    # Share buttons for each NFT
    keyboard = []
    for i, nft in enumerate(paginated_nfts):
        nft_address = nft.get('address')
        name = nft.get('metadata', {}).get('name', 'Unnamed NFT')
        keyboard.append([InlineKeyboardButton(f"🔗 Поделиться \"{name[:20]}\"", callback_data=f"share_{nft_address}")])

    if pagination_buttons:
        keyboard.append(pagination_buttons)

    keyboard.append([InlineKeyboardButton("🔄 Обновить", callback_data='my_nft_menu_refresh')])
    keyboard.append([InlineKeyboardButton("🔙 В меню", callback_data='main_menu')])

    return text, InlineKeyboardMarkup(keyboard)
