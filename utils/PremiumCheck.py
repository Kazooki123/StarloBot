from datetime import datetime

from nextcord.ext import commands
from utils.DbHandler import db_handler


class PremiumManager:
    def __init__(self, bot):
        self.bot = bot

    async def is_premium(self, user_id: int) -> bool:
        """
        Check if a user has premium status and if it's still valid
        """
        async with self.bot.db_handler.pg_pool.acquire() as conn:
            record = await conn.fetchrow("""
                SELECT premium_user, premium_expiry 
                FROM user_data 
                WHERE user_id = $1
                """, user_id)

            if not record:
                return False

            if not record['premium_user']:
                return False

            # Check if premium has expired
            if record['premium_expiry'] and record['premium_expiry'] < datetime.now():
                # Premium has expired, update the database
                await conn.execute("""
                    UPDATE user_data 
                    SET premium_user = FALSE 
                    WHERE user_id = $1
                    """, user_id)
                return False

            return True

    async def add_premium(self, user_id: int, duration_days: int) -> bool:
        """
        Add or extend premium status for a user
        """
        try:
            async with self.bot.db_handler.pg_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO user_data (user_id, premium_user, premium_expiry)
                    VALUES ($1, TRUE, NOW() + interval '1 day' * $2)
                    ON CONFLICT (user_id) 
                    DO UPDATE SET 
                        premium_user = TRUE,
                        premium_expiry = CASE 
                            WHEN user_data.premium_expiry > NOW() 
                            THEN user_data.premium_expiry + interval '1 day' * $2
                            ELSE NOW() + interval '1 day' * $2
                        END
                    """, user_id, duration_days)
                return True
        except Exception as e:
            print(f"Error adding premium status: {e}")
            return False


def premium_check():
    """
    Decorator to check if a user has premium status
    """

    async def predicate(ctx):
        if not hasattr(ctx.bot, 'premium_manager'):
            ctx.bot.premium_manager = PremiumManager(ctx.bot)

        is_premium = await ctx.bot.premium_manager.is_premium(ctx.author.id)

        if is_premium:
            return True
        else:
            await ctx.send(
                f'⚠️ {ctx.author.mention} **This command requires premium status!** Use !premium to learn more about premium features.')
            return False

    return commands.check(predicate)
