import nextcord
from nextcord.ext import commands

class Link2Image(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(name="link_to_image", description="Converts link to images!")
    async def link_to_image(self, ctx: nextcord.Interaction, link):
        embed = nextcord.Embed(title="Image", description="Here is the image from the provided link:")
        embed.set_image(url=link)
        await ctx.send(embed=embed)
        
def setup(bot):
    bot.add_cog(Link2Image(bot))