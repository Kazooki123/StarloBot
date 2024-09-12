import nextcord
from nextcord.ext import commands, tasks
import json
import os
import sys
import datetime
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import bot_intents

bot = commands.Bot(intents=bot_intents())


async def get_random_fact():
    # Path to JSON file containing facts
    facts_file_path = "facts.json"

    # Read the JSON file
    try:
        with open(facts_file_path, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        # Handle case where "facts.json" is not found
        return "Error: Facts file 'facts.json' not found."
    except json.JSONDecodeError:
        # Handle case where "facts.json" is invalid JSON
        return "Error: 'facts.json' is not valid JSON."

    # Pick a random fact from the list
    random_fact_index = random.randint(0, len(data) - 1)
    return data[random_fact_index]


class Modding(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(description="Bans a member.")
    @commands.has_permissions(administrator=True)
    async def ban(self, ctx: nextcord.Interaction, member: nextcord.Member):
        await member.ban()
        await ctx.send(f"{member.mention} has been banned. You naughty bastard.")

    @nextcord.slash_command(description="Kicks a member.")
    @commands.has_permissions(administrator=True)
    async def kick(self, ctx: nextcord.Interaction, member: nextcord.Member):
        await member.kick()
        await ctx.send(f"{member.mention} has been kicked.")

    @nextcord.slash_command(description="Timeouts a member")
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, interaction: nextcord.Interaction, member: nextcord.Member, seconds: int = 0,
                      minutes: int = 0, hours: int = 0, days: int = 0, reason: str = None):
        duration = datetime.timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days)
        await member.timeout(duration, reason=reason)

        await interaction.response.send_message(f'{member.mention} was timeout until for {duration}', ephemeral=True)

        # Command to start sending daily facts

    @nextcord.slash_command(description="Setups and sends facts daily")
    async def factstart(self, ctx: nextcord.Interaction):
        channel_id = ctx.channel.id
        guild = ctx.guild

        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                    INSERT INTO fact_channels (channel_id)
                    VALUES ($1)
                    ON CONFLICT (channel_id) DO NOTHING;
                    """, channel_id
            )
        embed = nextcord.Embed(title="Facts Channel Set Up",
                               description="Daily facts will now be posted in this channel!")

        embed.set_thumbnail(url=guild.icon.url)
        await ctx.send(embed=embed)

    # Background task to send daily facts
    @tasks.loop(hours=24)
    async def send_daily_fact():
        fact = await get_random_fact()

        async with bot.pg_pool.acquire() as conn:
            channels = await conn.fetch(
                """
                SELECT channel_id FROM fact_channels;
                """
            )
            for record in channels:
                channel = bot.get_channel(record['channel_id'])
                if channel:
                    await channel.send(f"Facts Of the Day: {fact}")

    @send_daily_fact.before_loop
    async def before_send_daily_fact():
        await bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Modding(bot))
