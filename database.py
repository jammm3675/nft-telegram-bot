import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def create_pool():
    """Creates and returns a connection pool."""
    return await asyncpg.create_pool(DATABASE_URL)

async def init_db(pool):
    """Initializes the database by creating tables if they don't exist."""
    async with pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username VARCHAR(32),
                    first_name VARCHAR(255),
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS user_wallets (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
                    wallet_address VARCHAR(64) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user_id, wallet_address)
                );
            """)
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS user_states (
                    id BIGSERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    state VARCHAR(50),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)

async def get_or_create_user(pool, telegram_id, username, first_name):
    """Gets a user by telegram_id or creates one if they don't exist."""
    async with pool.acquire() as connection:
        user = await connection.fetchrow("SELECT id FROM users WHERE telegram_id = $1", telegram_id)
        if user:
            return user['id']

        await connection.execute(
            "INSERT INTO users (telegram_id, username, first_name) VALUES ($1, $2, $3)",
            telegram_id, str(username), str(first_name)
        )
        user = await connection.fetchrow("SELECT id FROM users WHERE telegram_id = $1", telegram_id)
        return user['id']

async def add_wallet(pool, user_id, wallet_address):
    """Adds a new wallet for a user."""
    async with pool.acquire() as connection:
        try:
            await connection.execute(
                "INSERT INTO user_wallets (user_id, wallet_address) VALUES ($1, $2)",
                user_id, wallet_address
            )
            return True
        except asyncpg.UniqueViolationError:
            return False

async def get_user_wallets(pool, user_id):
    """Retrieves all wallets for a given user."""
    async with pool.acquire() as connection:
        wallets = await connection.fetch("SELECT wallet_address FROM user_wallets WHERE user_id = $1 ORDER BY created_at DESC", user_id)
        return [dict(w) for w in wallets]

async def remove_wallet(pool, user_id, wallet_address):
    """Removes a wallet for a user."""
    async with pool.acquire() as connection:
        await connection.execute(
            "DELETE FROM user_wallets WHERE user_id = $1 AND wallet_address = $2",
            user_id, wallet_address
        )

async def set_user_state(pool, telegram_id, state):
    """Sets or updates the state for a user."""
    async with pool.acquire() as connection:
        await connection.execute(
            """
            INSERT INTO user_states (telegram_id, state) VALUES ($1, $2)
            ON CONFLICT (telegram_id) DO UPDATE SET state = $2, updated_at = NOW()
            """,
            telegram_id, state
        )

async def get_user_state(pool, telegram_id):
    """Gets the current state of a user."""
    async with pool.acquire() as connection:
        state = await connection.fetchval("SELECT state FROM user_states WHERE telegram_id = $1", telegram_id)
        return state

async def clear_user_state(pool, telegram_id):
    """Clears the state for a user."""
    async with pool.acquire() as connection:
        await connection.execute("DELETE FROM user_states WHERE telegram_id = $1", telegram_id)
