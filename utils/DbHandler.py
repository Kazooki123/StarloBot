import asyncpg
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
from typing import Optional

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))


class DatabaseHandler:
    def __init__(self):
        self.pg_pool: Optional[asyncpg.Pool] = None
        self.mongo_client: Optional[MongoClient] = None

        # Load environment variables with validation
        self.postgres_url = os.getenv('POSTGRES_URL')
        self.mongo_url = os.getenv('MONGO_DB_URL')

        # Check each variable individually and report missing ones
        missing_vars = []
        if not self.postgres_url:
            missing_vars.append('POSTGRES_URL')
        if not self.mongo_url:
            missing_vars.append('MONGO_DB_URL')

        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        print("Environment variables loaded successfully:")
        print(f"POSTGRES_URL: {'Found' if self.postgres_url else 'Missing'}")
        print(f"MONGO_DB_URL: {'Found' if self.mongo_url else 'Missing'}")

    async def initialize(self):
        """Initialize all database connections"""
        await self.init_postgres()
        await self.init_mongo()

    async def init_postgres(self):
        """Initialize PostgreSQL connection pool"""
        try:
            self.pg_pool = await asyncpg.create_pool(
                self.postgres_url,
                min_size=5,
                max_size=20
            )
            await self.create_tables()
            print("PostgreSQL connection established successfully!")
        except Exception as e:
            print(f"PostgreSQL connection error: {e}")
            raise

    async def init_mongo(self):
        """Initialize MongoDB connection"""
        try:
            self.mongo_client = MongoClient(self.mongo_url, server_api=ServerApi('1'))
            self.mongo_client.admin.command('ping')
            print("MongoDB connection established successfully!")
        except Exception as e:
            print(f"MongoDB connection error: {e}")
            raise

    async def create_tables(self):
        """Create necessary database tables if they don't exist"""
        async with self.pg_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_data (
                    user_id BIGINT PRIMARY KEY,
                    premium_user BOOLEAN DEFAULT FALSE,
                    premium_expiry TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_levels (
                    user_id BIGINT,
                    guild_id BIGINT,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    last_xp_gain TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    PRIMARY KEY (user_id, guild_id)
                )
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS afk_status (
                    user_id BIGINT,
                    guild_id BIGINT,
                    reason TEXT,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    PRIMARY KEY (user_id, guild_id)
                )
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id BIGINT PRIMARY KEY,
                    level_channel_id BIGINT,
                    welcome_channel_id BIGINT,
                    log_channel_id BIGINT,
                    prefix VARCHAR(10) DEFAULT '!'
                )
            """)

    async def close(self):
        if self.pg_pool:
            await self.pg_pool.close()
        if self.mongo_client:
            self.mongo_client.close()


db_handler = DatabaseHandler()
