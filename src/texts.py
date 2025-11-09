from telegram.helpers import escape_markdown

def get_text(key: str, lang: str = 'ru') -> str:
    """
    Returns the text for a given key and language.
    In the future, this can be expanded to support multiple languages.
    """
    texts = {
        'welcome': {
            'ru': (
                "Добро пожаловать!\n\n"
                "• Привяжите TON кошелек\n"
                "• Показывайте свои NFT друзьям\n"
                "• Получайте предложения о покупке\n\n"
                "• Быстрый шаринг одной командой\n"
                "• Ссылки на Getgems и TonViewer\n"
                "• Прямой контакт с владельцем"
            )
        },
        'horoscope_disclaimer': {
            'ru': "This is a disclaimer text that will be formatted."
        },
        'main_menu': {
            'ru': "Главное меню"
        },
        'my_wallet': {
            'ru': "Мой кошелёк"
        },
        'my_nft': {
            'ru': "Мои NFT"
        },
        'help': {
            'ru': "Помощь"
        },
        'wallets_menu': {
            'ru': "👛 Ваши кошельки"
        },
        'add_wallet_prompt': {
            'ru': "Отправьте адрес TON кошелька для привязки:"
        },
        'no_wallets': {
            'ru': "Здесь ничего нет"
        },
        'add_wallet': {
            'ru': "Добавить кошелек"
        },
        'back_to_menu': {
            'ru': "В меню"
        },
        'loading_nfts': {
            'ru': "🖼️ Ваши NFT для шаринга\n\nЗагружаем ваши NFT..."
        },
        'update': {
            'ru': "Обновить"
        },
        'share': {
            'ru': "Поделиться"
        },
        'nft_card_template': {
            'ru': (
                "🎴 {nft_name}\n"
                "Коллекция: {collection_name}\n"
                "Владелец: 👤 {owner_username}\n\n"
                "Ссылка: 🔗 Getgems\n\n"
                "💬 Хотите связаться с владельцем?"
            )
        },
        'write_to_owner': {
            'ru': "💌 Написать владельцу"
        },
        'open_in_getgems': {
            'ru': "🔗 Открыть в Getgems"
        },
    }
    return texts.get(key, {}).get(lang, f"Missing text for key: {key}")

def get_disclaimer_text() -> str:
    """Returns the formatted disclaimer text."""
    disclaimer_raw = get_text('horoscope_disclaimer', 'ru')
    return f">{escape_markdown(disclaimer_raw, 2)}"
