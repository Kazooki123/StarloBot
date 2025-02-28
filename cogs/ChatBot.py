import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv('../.env')

ANTHROPIC_API = os.getenv("ANTHROPIC_API")


class ChatBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="activate", help="Activate the Chatbot which uses Claude!")
    async def activate_claude(self, ctx):
        """Activate the bot to chat in a specific channel"""


def setup(bot):
    bot.add_cog(ChatBot(bot))
