import nextcord
import json
import random
import os
from nextcord.ext import commands

WYR_FOLDER = os.path.join(os.path.dirname(__file__), "..", "json")
WYR = os.path.join(WYR_FOLDER, "wouldyourather.json")

class WouldYouRather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.questions = json.load(open(WYR, "r"))["questions"]
        
    @commands.command(name="wouldyourather", help="Asks a random question from the list.")
    async def wouldyourather(self, ctx):
        """
        Asks a random question from the list.
        """
        await ctx.send(f"🤔 **Would you rather...?**\n{random.choice(self.questions)}")

def setup(bot):
    bot.add_cog(WouldYouRather(bot))