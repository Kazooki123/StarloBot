import nextcord
from nextcord.ext import commands

class CurrencyConverter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="convert", help="Converts currency!")
    async def convert(self, ctx):
        """
        Convert currency in real time!
        """

def setup(bot):
    bot.add_cog(CurrencyConverter(bot))