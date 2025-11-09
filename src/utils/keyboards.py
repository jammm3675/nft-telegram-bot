from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.texts import get_text

def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Returns the main menu keyboard."""
    keyboard = [
        [InlineKeyboardButton(get_text('my_wallet'), callback_data='my_wallet')],
        [InlineKeyboardButton(get_text('my_nft'), callback_data='my_nft')],
        [InlineKeyboardButton(get_text('help'), callback_data='help')],
    ]
    return InlineKeyboardMarkup(keyboard)

def wallets_menu_keyboard(wallets: list) -> InlineKeyboardMarkup:
    """Returns the wallets menu keyboard."""
    keyboard = []
    for wallet in wallets:
        keyboard.append([InlineKeyboardButton(f"👛 {wallet[:6]}...{wallet[-4:]}", callback_data=f'wallet_{wallet}')])

    keyboard.append([InlineKeyboardButton(get_text('add_wallet'), callback_data='add_wallet')])
    keyboard.append([InlineKeyboardButton(get_text('back_to_menu'), callback_data='main_menu')])
    return InlineKeyboardMarkup(keyboard)

def nft_list_keyboard(current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Returns the keyboard for the NFT list."""
    keyboard = [
        [
            InlineKeyboardButton("◀️", callback_data=f'prev_nft_page_{current_page - 1}'),
            InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data='page_info'),
            InlineKeyboardButton("▶️", callback_data=f'next_nft_page_{current_page + 1}'),
        ],
        [InlineKeyboardButton(get_text('update'), callback_data='update_nfts')],
        [InlineKeyboardButton(get_text('back_to_menu'), callback_data='main_menu')],
    ]
    return InlineKeyboardMarkup(keyboard)

def share_nft_keyboard(owner_id: int, getgems_url: str) -> InlineKeyboardMarkup:
    """Returns the keyboard for sharing an NFT."""
    keyboard = [
        [InlineKeyboardButton(get_text('write_to_owner'), url=f"tg://user?id={owner_id}")],
        [InlineKeyboardButton(get_text('open_in_getgems'), url=getgems_url)],
    ]
    return InlineKeyboardMarkup(keyboard)
