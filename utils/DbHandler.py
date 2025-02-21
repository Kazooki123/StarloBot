import os
from typing import Optional

import asyncpg
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from upstash_redis import Redis

load_dotenv('../.env')


class DatabaseHandler:
    def __init__(self):
        self.pg_pool: Optional[asyncpg.Pool] = None
        self.mongo_client: Optional[MongoClient] = None
        self.redis_client: Optional[Redis] = None

        # Load environment variables
        self.postgres_url = os.getenv('POSTGRES_URL')
        self.mongo_url = os.getenv('MONGO_DB_URL')

        if not all([self.postgres_url, self.mongo_url]):
            raise ValueError("Missing required environment variables")

    async def initialize(self):
        """Initialize all database connections"""
        await self.init_postgres()
        await self.init_mongo()
        await self.init_redis()

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

    async def init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = Redis.from_env()
            if await self.redis_client.ping():
                print("Redis connection established successfully!")
            else:
                raise ConnectionError("Redis ping failed")
        except Exception as e:
            print(f"Redis connection error: {e}")
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
