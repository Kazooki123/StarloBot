import nextcord
from nextcord.ext import commands

intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

class Premium(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='premium')
    async def premium(self, ctx):
        message = (
            'Commands like "!ai_art" and "!question" are officially locked.'
            'You\'ll have to pay premium, contact or DM Starlo for payments.'
        )
        await ctx.send(message)

    @commands.command(name="add")
    @commands.has_permissions(administrator=True)
    async def add_premium(self, ctx, user: nextcord.User):
        async with bot.pg_pool.acquire() as connection:
            await connection.execute('UPDATE user_data SET premium_user = $1 WHERE user_id = $2', True, user.id)
        await ctx.send(f"{user.mention} has been added to the premium users list.")

    @commands.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def remove_premium(self, ctx, user: nextcord.User):
        async with bot.pg_pool.acquire() as connection:
            await connection.execute('UPDATE user_data SET premium_user = $1 WHERE user_id = $2', False, user.id)
        await ctx.send(f"{user.mention} has been removed from the premium users list.")

def setup(bot):
    bot.add_cog(Premium(bot))
