import nextcord
from nextcord.ext import commands
import random
import asyncio

from main import bot_intents

bot = commands.Bot(intents=bot_intents())


class Currency(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(
        name="apply",
        description="Apply for a job",
        guild_ids=[1237746712291049483]
    )
    async def apply(self, ctx):
        jobs = ["Engineer", "Programmer", "Artist"]
        job_message = "\n".join([f"{i + 1}. {job}" for i, job in enumerate(jobs)])

        await ctx.send(f"{ctx.author.mention}, choose a job by replying with the corresponding number:\n{job_message}")

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        try:
            reply = await self.bot.wait_for('message', check=check, timeout=30)
            job_number = int(reply.content)

            if 1 <= job_number <= len(jobs):
                job = jobs[job_number - 1]

                async with self.bot.pg_pool.acquire() as conn:
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
            await ctx.send(f"{ctx.author.mention}, timeout. Please use /apply again.")
        except ValueError:
            await ctx.send(f"{ctx.author.mention}, please enter a valid number.")

    @nextcord.slash_command(
        name="work",
        description="Apply or do a work based on your job!",
        guild_ids=[1237746712291049483]
    )
    async def work(self, ctx):
        async with self.bot.pg_pool.acquire() as conn:
            user_data = await conn.fetchrow(
                "SELECT job, wallet FROM user_data WHERE user_id = $1",
                ctx.author.id
            )

        if user_data:
            job, _ = user_data
            earnings = random.randint(1, 500)

            async with self.bot.pg_pool.acquire() as conn:
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
            await ctx.send(f"{ctx.author.mention}, you need to /apply for a job first.")

    @nextcord.slash_command(
        name="wallet",
        description="Check your wallet!",
        guild_ids=[1237746712291049483]
    )
    async def wallet(self, ctx):
        async with self.bot.pg_pool.acquire() as conn:
            wallet_amount = await conn.fetchval(
                "SELECT wallet FROM user_data WHERE user_id = $1",
                ctx.author.id
            )

        if wallet_amount is not None:
            embed = nextcord.Embed(title="Your Wallet", color=nextcord.Color.yellow())
            embed.add_field(name="Wallet:", value=f"{ctx.author.mention}, your wallet balance is {wallet_amount} coins 🪙🪙.")
            await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(title="Failed!", color=nextcord.Color.red())
            embed.add_field(name="Error", value=f"{ctx.author.mention}, you need to /apply for a job first.")
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Currency(bot))
