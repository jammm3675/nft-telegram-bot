# NFT Telegram Bot

Бот для продажи NFT в Telegram с возможностью просмотра стикеров.

## Особенности
- Витрина NFT коллекций
- Просмотр деталей каждой коллекции
- Ссылки на стикерпаки в @sticker_bot
- Минималистичный дизайн
- Навигация между экранами

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/ваш-username/nft-telegram-bot.git
cd nft-telegram-bot
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Настройте бота:
   - Создайте файл `config.py` на основе примера
   - Получите токен у [@BotFather](https://t.me/BotFather)
   - Загрузите изображения и получите их file_id

4. Запустите бота:
```bash
python bot.py
```

## Получение file_id изображений

Создайте временный скрипт `get_file_id.py`:
```python
from telegram import Bot
import asyncio

async def main():
    bot = Bot(token="ВАШ_ТОКЕН")
    async with bot:
        file = await bot.send_photo(chat_id="ВАШ_CHAT_ID", photo=open("image.png", "rb"))
        print("File ID:", file.photo[-1].file_id)

asyncio.run(main())
```

Запустите для каждого изображения и обновите `config.py`

## Развертывание
Бот может работать на любом сервере с Python 3.8+
