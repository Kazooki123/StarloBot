import nextcord
from nextcord.ext import commands, tasks
import json
import datetime
import random
import os


async def get_random_fact():
    facts_file_path = os.path.join(os.path.dirname(__file__), "../json/facts.json")
    
    try:
        with open(facts_file_path, "r") as file:
            data = json.load(file)
            fact = random.choice(data)
            
            # Handle both string facts and dictionary facts
            if isinstance(fact, dict):
                return fact["fact"]
            return fact
    except FileNotFoundError:
        return "Error: Facts file not found."
    except json.JSONDecodeError:
        return "Error: Invalid JSON format in facts file."


class FunFact(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.send_daily_fact.start()

    @tasks.loop(hours=24)
    async def send_daily_fact(self):
        fact = await get_random_fact()
        
        async with self.bot.pg_pool.acquire() as conn:
            channels = await conn.fetch("SELECT channel_id FROM fact_channels;")
            for record in channels:
                channel = self.bot.get_channel(record['channel_id'])
                if channel:
                    embed = nextcord.Embed(
                        title="🎯 Fact of the Day",
                        description=fact,
                        color=nextcord.Color.blue(),
                        timestamp=datetime.datetime.now()
                    )
                    await channel.send(embed=embed)

    @send_daily_fact.before_loop
    async def before_send_daily_fact(self):
        await self.bot.wait_until_ready()

    @commands.command(
        name="setfactchannel"
    )
    @commands.has_permissions(administrator=True)
    async def setfactchannel(self, ctx):
        async with self.bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO fact_channels (channel_id)
                VALUES ($1)
                ON CONFLICT (channel_id) DO NOTHING
                """,
                ctx.channel.id
            )
        await ctx.send("This channel will now receive daily facts!")

    def cog_unload(self):
        self.send_daily_fact.cancel()


def setup(bot):
    bot.add_cog(FunFact(bot))
