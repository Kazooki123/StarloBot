import nextcord
from nextcord.ext import commands
from rule34Py import rule34Py

class Rule34Search(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_commands(name="rule34", description="Searches images from rule34 and displays it as embedded image.")
    async def rule34search(interaction, *, query):
        """Searches metadata and images from rule34"""
        

        
def setup(bot):
    bot.add_cog(Rule34Search(bot))
