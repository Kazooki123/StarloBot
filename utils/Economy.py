# This holds all money from users that uses a command that involves money

from utils.DbHandler import db_handler
from typing import Optional

class EconomySystem:
    def __init__(self):
        self.db = db_handler

    async def initialize(self):
        """Initialize database and create economy tables"""
        await self.db.initialize()

        async with self.db.pg_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_economy (
                    user_id BIGINT PRIMARY KEY,
                    balance BIGINT DEFAULT 1000,
                    last_daily TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)


    async def get_balance(self, user_id: int) -> int:
        """Get user's current balance"""
        async with self.db.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT balance FROM user_economy WHERE user_id = $1',
                user_id
            )
            if not row:
                await self.create_account(user_id)
                return 1000
            return row['balance']

    async def create_account(self, user_id: int) -> None:
        """Create new user account with default balance"""
        async with self.db.pg_pool.acquire() as conn:
            await conn.execute(
                'INSERT INTO user_economy (user_id) VALUES ($1) ON CONFLICT DO NOTHING',
                user_id
            )

    async def add_money(self, user_id: int, amount: int) -> int:
        """Add money to user's balance"""
        async with self.db.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                '''
                INSERT INTO user_economy (user_id, balance) 
                VALUES ($1, $2)
                ON CONFLICT (user_id) 
                DO UPDATE SET balance = user_economy.balance + $2
                RETURNING balance
                ''',
                user_id, amount
            )
            return row['balance']

    async def remove_money(self, user_id: int, amount: int) -> Optional[int]:
        """Remove money from user's balance if they have enough"""
        async with self.db.pg_pool.acquire() as conn:
            current_balance = await self.get_balance(user_id)
            if current_balance < amount:
                return None

            row = await conn.fetchrow(
                '''
                UPDATE user_economy 
                SET balance = balance - $2
                WHERE user_id = $1
                RETURNING balance
                ''',
                user_id, amount
            )
            return row['balance']

economy_system = EconomySystem()