import nextcord
from nextcord.ext import commands

from main import bot_intents

bot = commands.Bot(intents=bot_intents())

class Premium(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(
        name='premium',
        description="Sends an info about the bot's premium policy.",
        guild_ids=[1237746712291049483]    
    )
    async def premium(self, interaction: nextcord.Interaction):
        message = (
            'Commands like "!ai_art" and "!question" are officially locked.'
            'You\'ll have to pay premium, contact or DM Starlo for payments.'
        )
        await interaction.response.send_message(message)

    @nextcord.slash_command(
        name="add",
        description="Admin Only: Adds a user into the premium list.",
        guild_ids=[1237746712291049483]    
    )
    @commands.has_permissions(administrator=True)
    async def add_premium(self, interaction: nextcord.Interaction, user: nextcord.User):
        async with bot.pg_pool.acquire() as connection:
            await connection.execute('UPDATE user_data SET premium_user = $1 WHERE user_id = $2', True, user.id)
        await interaction.response.send_message(f"{user.mention} has been added to the premium users list.")

    @nextcord.slash_command(
        name="remove",
        description="Admin Only: Removes a user into the premium list.",
        guild_ids=[1237746712291049483]    
    )
    @commands.has_permissions(administrator=True)
    async def remove_premium(self, interaction: nextcord.Interaction, user: nextcord.User):
        async with bot.pg_pool.acquire() as connection:
            await connection.execute('UPDATE user_data SET premium_user = $1 WHERE user_id = $2', False, user.id)
        await interaction.response.send_message(f"{user.mention} has been removed from the premium users list.")

def setup(bot):
    bot.add_cog(Premium(bot))
