import nextcord
from nextcord.ext import commands
import os

SHARD_ID = int(os.environ.get('SHARD_ID', 0))
SHARD_COUNT = int(os.environ.get('SHARD_COUNT', 1))

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="ping", description="Pings the bot and its shard info")
    async def ping(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(title="PONG!", color=nextcord.Color.red())
        embed.add_field(name="Latency:", value=f"{round(self.bot.latency * 1000)}ms")
        embed.add_field(name="Shards:", value=SHARD_ID/SHARD_COUNT)
    
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="shardinfo", description="More infos for the SHARDS")
    async def shardinfo(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(title="Shard Information", color=nextcord.Color.blue())
        embed.add_field(name="Shard ID", value=SHARD_ID, inline=True)
        embed.add_field(name="Total Shards", value=SHARD_COUNT, inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="Guilds on this shard", value=len(self.bot.guilds), inline=True)
    
        await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(Ping(bot))
