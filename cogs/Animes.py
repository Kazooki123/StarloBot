import nextcord
from nextcord import Embed, Color
from nextcord.ext import commands


class Animes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_commands(name="anime", description="")
    

