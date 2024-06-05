import nextcord
from nextcord.ext import commands

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(description="Replies with pong!")
    async def ping(self, interaction: nextcord.Interaction):
        await interaction.send("Pong!", ephemeral=True)
        
def setup(bot):
    bot.add_cog(Ping(bot))