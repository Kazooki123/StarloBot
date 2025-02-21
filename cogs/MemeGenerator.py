import os

from dotenv import load_dotenv
from nextcord.ext import commands

load_dotenv('../.env')

IMGFLIP_USERNAME = os.getenv("IMGFLIP_USERNAME")
IMGFLIP_PASSWORD = os.getenv("IMGFLIP_PASSWORD")


class MemeGenerator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.templates = self.get_meme_templates()
