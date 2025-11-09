import asyncpg
from src.config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
import logging

logger = logging.getLogger(__name__)

async def get_pool():
    """Creates and returns a database connection pool."""
    try:
        pool = await asyncpg.create_pool(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        return pool
    except Exception as e:
        logger.error(f"Could not connect to the database: {e}")
        return None

async def setup_database():
    """Sets up and migrates the database tables."""
    pool = await get_pool()
    if pool:
        async with pool.acquire() as connection:
            # Create users table if it doesn't exist
            await connection.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    first_name VARCHAR(255)
                );
            ''')

            # Add last_name column if it doesn't exist (for migration)
            await connection.execute('''
                ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(255);
            ''')

            # Create wallets table
            await connection.execute('''
                CREATE TABLE IF NOT EXISTS wallets (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(id),
                    address VARCHAR(255) UNIQUE NOT NULL
                );
            ''')
            logger.info("Database tables checked/created successfully.")
        await pool.close()

async def add_user(pool, user_id: int, username: str, first_name: str, last_name: str):
    """Adds or updates a user in the database."""
    async with pool.acquire() as connection:
        # last_name can be None, which will be stored as NULL
        await connection.execute(
            """
            INSERT INTO users (id, username, first_name, last_name)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE SET
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name;
            """,
            user_id,
            username or '',
            first_name or '',
            last_name or '',
        )

async def add_wallet(pool, user_id: int, address: str) -> bool:
    """Adds a wallet for a user."""
    try:
        async with pool.acquire() as connection:
            await connection.execute(
                "INSERT INTO wallets (user_id, address) VALUES ($1, $2)",
                user_id,
                address,
            )
        return True
    except asyncpg.UniqueViolationError:
        logger.warning(f"Wallet address {address} already exists.")
        return False

async def get_wallets(pool, user_id: int) -> list:
    """Gets all wallets for a user."""
    async with pool.acquire() as connection:
        rows = await connection.fetch("SELECT address FROM wallets WHERE user_id = $1", user_id)
        return [row['address'] for row in rows]
