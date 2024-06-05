# DbHandler.py

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
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_data (
                user_id bigint PRIMARY KEY,
                job text,
                wallet integer,
                experience integer,
                level integer,
                birthday date,
                premium_user boolean DEFAULT FALSE
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS fact_channels (
                channel_id bigint UNIQUE
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                guild_id BIGINT PRIMARY KEY,
                level_channel_id BIGINT
            )
            """
        )

def redis_conns():
    redis = Redis.from_env()
    # Explicitly check connection using ping
    if redis.ping():
        print("Connection to Redis successful!")
    else:
        print("Connection to Redis failed. Please check credentials and network connectivity.")
            
         
def mongo_conns():
    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
        
        