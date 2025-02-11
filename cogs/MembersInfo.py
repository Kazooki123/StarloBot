import nextcord
from nextcord.ext import commands
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
import asyncio

load_dotenv('../.env')

MONGO_DB_URL = os.getenv('MONGO_DB_URL')

# MongoDB Connection
uri = MONGO_DB_URL

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

async def should_store_member_info(member):
    await member.send("Do you want your member information stored for bot features? (yes/no)")
    try:
        response = await bot.wait_for('message', check=lambda m: m.author == member and m.channel.is_private,
                                      timeout=60)
        if response.content.lower() == 'yes':
            return True
        else:
            return False
    except asyncio.TimeoutError:
        await member.send("Timed out waiting for your response.")
        return False


class MemberInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="memberinfo"
    )
    async def memberinfo(self, ctx, member: nextcord.Member = None):
        if member is None:
            member = ctx.author

        if not should_store_member_info(ctx):
            await ctx.send("Sorry, member information storage is not available.")
            return

        embed = nextcord.Embed(title="Member Information", color=nextcord.Color.blue())
        embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name="Username:", value=member.name, inline=True)
        embed.add_field(name="Discriminator:", value=member.discriminator, inline=True)
        embed.add_field(name="ID:", value=member.id, inline=True)
        embed.add_field(name="Joined Server:", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.add_field(name="Joined Discord:", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)

        db = client.user_data
        collection = db.member_info
        data = {
            "user_id": member.id,
            "username": member.name,
            "discriminator": member.discriminator,
            "joined_server": member.joined_at.strftime("%Y-%m-%d %H:%M:%S"),
            "joined_discord": member.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

        collection.insert_one(data)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(MemberInfo(bot))
