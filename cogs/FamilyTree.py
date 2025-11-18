import nextcord
from nextcord import Embed
from nextcord.ext import commands


class FamilyTree(commands.Cog):
    def __init__(setup, bot):
        setup.bot = bot
        
    @nextcord.slash_commands(name="familytree", description="Shows your family in a graph tree.")
    async def family_tree(interaction: nextcord.Interaction):
        """
        Usage: !familytree @user
        """
