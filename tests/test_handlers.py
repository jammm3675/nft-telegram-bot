import pytest
from unittest.mock import AsyncMock, MagicMock
from src.handlers.start import start

@pytest.mark.asyncio
async def test_start_command():
    """Tests the /start command handler."""
    # Mock update and context objects
    update = AsyncMock()
    context = AsyncMock()

    # Mock user data
    user = MagicMock()
    user.id = 12345
    user.username = 'testuser'
    user.first_name = 'Test'
    user.last_name = 'User'
    update.effective_user = user
    update.message.reply_text = AsyncMock()

    # Mock db_pool
    db_pool = MagicMock()
    context.bot_data = {"db_pool": db_pool}

    # Call the handler
    await start(update, context)

    # Assertions
    update.message.reply_text.assert_called_once()
    # A more detailed test would check the content of the reply_text
