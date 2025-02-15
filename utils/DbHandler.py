import asyncpg
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
from upstash_redis import Redis

load_dotenv('../.env')

MONGO_DB_URL = os.getenv('MONGO_DB_URL')

uri = MONGO_DB_URL

client = MongoClient(uri, server_api=ServerApi('1'))

async def create_pool(DATABASE_URL):
    return await asyncpg.create_pool(DATABASE_URL)

async def create_table(pool):
    async with pool.acquire() as conn:
        async with conn.transaction():
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

def redis_conns():
    redis = Redis.from_env()
    if redis.ping():
        print("Connection to Redis successful!")
    else:
        print("Connection to Redis failed. Please check credentials and network connectivity.")

def mongo_conns():
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)