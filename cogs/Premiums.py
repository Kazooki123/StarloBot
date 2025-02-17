import nextcord
from nextcord.ext import commands

intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


async def is_premium(user_id):
    async with bot.pg_pool.acquire() as connection:
        record = await connection.fetchrow(
            """
            SELECT premium_user FROM user_data
            WHERE user_id = $1;
            """, user_id
        )
        return record and record['premium_user']


def premium_check():
    async def predicate(ctx):
        if await is_premium(ctx.author.id):
            return True
        else:
            await ctx.send('Looks like you haven\'t been premium yet, please type !premium, Thank you.')
            return False

    return commands.check(predicate)


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
