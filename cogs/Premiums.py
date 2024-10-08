import nextcord
from nextcord.ext import commands
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import bot_intents

bot = commands.Bot(intents=bot_intents())


class Premium(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name='premium', description="Sends an info about the bot's premium policy.")
    async def premium(self, ctx: nextcord.Interaction):
        message = (
            'Commands like "!ai_art" and "!question" are officially locked.'
            'You\'ll have to pay premium, contact or DM Starlo for payments.'
        )
        await ctx.send(message)

    @nextcord.slash_command(description="Admin Only: Adds a user into the premium list.")
    @commands.has_permissions(administrator=True)
    async def add_premium(self, ctx: nextcord.Interaction, user: nextcord.User):
        async with bot.pg_pool.acquire() as connection:
            await connection.execute('UPDATE user_data SET premium_user = $1 WHERE user_id = $2', True, user.id)
        await ctx.send(f"{user.mention} has been added to the premium users list.")

    @nextcord.slash_command(description="Admin Only: Removes a user into the premium list.")
    @commands.has_permissions(administrator=True)
    async def remove_premium(self, ctx: nextcord.Interaction, user: nextcord.User):
        async with bot.pg_pool.acquire() as connection:
            await connection.execute('UPDATE user_data SET premium_user = $1 WHERE user_id = $2', False, user.id)
        await ctx.send(f"{user.mention} has been removed from the premium users list.")


def setup(bot):
    bot.add_cog(Premium(bot))
