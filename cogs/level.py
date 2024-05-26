import discord
from discord.ext import commands

class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="rank")
    async def rank(self, ctx: discord.ApplicationContext):
        user_id = ctx.author.id
        async with self.bot.pg_pool.acquire() as connection:
            record = await connection.fetchrow('SELECT level FROM user_data WHERE user_id = $1', user_id)
            if record:
                level = record['level']
                await ctx.send(f"{ctx.author.mention}, you're level {level}!")
            else:
                await ctx.send("You don't have a level yet.")

    @commands.slash_command(name="leaderboard")
    async def leaderboard(self, ctx: discord.ApplicationContext, type: str):
        if type.lower() not in ["money", "level"]:
            await ctx.send("Invalid type! Please use '/leaderboard money' or '/leaderboard level'.")
            return

        async with self.bot.pg_pool.acquire() as connection:
            if type.lower() == "money":
                query = 'SELECT user_id, wallet FROM user_data ORDER BY wallet DESC LIMIT 10'
            else:
                query = 'SELECT user_id, level FROM user_data ORDER BY level DESC LIMIT 10'
            
            records = await connection.fetch(query)

        if not records:
            await ctx.send("No data available for the leaderboard.")
            return

        embed = discord.Embed(title=f"Top 10 Users by {type.capitalize()}", color=discord.Color.blue())
        
        for i, record in enumerate(records):
            user_id = record['user_id']
            value = record['wallet'] if type.lower() == "money" else record['level']
            user = await self.bot.fetch_user(user_id)
            medal = ""
            if i == 0:
                medal = "🥇"
            elif i == 1:
                medal = "🥈"
            elif i == 2:
                medal = "🥉"
            embed.add_field(name=f"{medal} {user}", value=f"{type.capitalize()}: {value}", inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Level(bot))