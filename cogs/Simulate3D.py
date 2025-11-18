import nextcord
from nextcord.ext import commands


class Simulate3D(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_commands(name="simulate3d", description="Simulates a and displays a 3D object.")
    async def simulate3d(self, interaction):
        """Simulates 3D objects as .gif"""

