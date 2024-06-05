import nextcord
from nextcord.ext import commands
import random
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import bot_intents

bot = commands.Bot(intents=bot_intents())

class Currency(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    # Command to apply for a job
    @nextcord.slash_command(description="Apply for a job")
    async def apply(ctx):
        jobs = ["Engineer", "Programmer", "Artist"]
        job_message = "\n".join([f"{i+1}. {job}" for i, job in enumerate(jobs)])

        await ctx.send(f"{ctx.author.mention}, choose a job by replying with the corresponding number:\n{job_message}")

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        try:
            reply = await bot.wait_for('message', check=check, timeout=30)
            job_number = int(reply.content)

            if 1 <= job_number <= len(jobs):
                job = jobs[job_number - 1]

                async with bot.pg_pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO user_data (user_id, job, wallet)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (user_id) DO NOTHING
                        """,
                        ctx.author.id, job, 0
                    )

                await ctx.send(f"{ctx.author.mention}, applied as {job}.")
            else:
                await ctx.send(f"{ctx.author.mention}, invalid job number.")
        except asyncio.TimeoutError:
            await ctx.send(f"{ctx.author.mention}, timeout. Please use !apply again.")


    # Command to work
    @nextcord.slash_command(description="Apply or do a work base on your job!")
    async def work(ctx):
        async with bot.pg_pool.acquire() as conn:
            user_data = await conn.fetchrow(
                "SELECT job, wallet FROM user_data WHERE user_id = $1",
                ctx.author.id
            )

        if user_data:
            job, _ = user_data
            earnings = random.randint(1, 500)  # Simulate random earnings

            async with bot.pg_pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE user_data
                    SET wallet = wallet + $1
                    WHERE user_id = $2
                    """,
                    earnings, ctx.author.id
                )

            await ctx.send(f"{ctx.author.mention}, you worked as a {job} and earned {earnings} coins.")
        else:
            await ctx.send(f"{ctx.author.mention}, you need to !apply for a job first.")


    # Command to check wallet
    @nextcord.slash_command(description="Check your wallet!")
    async def wallet(ctx):
        async with bot.pg_pool.acquire() as conn:
            wallet_amount = await conn.fetchval(
                "SELECT wallet FROM user_data WHERE user_id = $1",
                ctx.author.id
            )

        if wallet_amount is not None:
            embed = nextcord.Embed(title="Your Wallet", color=nextcord.Color.yellow())
            embed.add_field(name="Wallet:", value=f"{ctx.author.mention}, your wallet balance is {wallet_amount} coins 🪙🪙.")
            await ctx.send(embed=embed)
        else:
            embed.add_field(name="Failed!", value=f"{ctx.author.mention}, you need to !apply for a job first.")
            await ctx.send(embed=embed)
            
def setup(bot):
    bot.add_cog(Currency(bot))