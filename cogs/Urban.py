import nextcord
from nextcord.ext import commands
import requests


class Urban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="urban", help="Search words and their meanings using the Urban Dictionary")
    async def urban(self, ctx, *, term):
        url = f"https://api.urbandictionary.com/v0/define?term={term}"
    
        response = requests.get(url)
        data = response.json()
    
        if len(data["list"]) > 0:
            definition = data["list"][0]["definition"]
            example = data["list"][0]["example"]
            embed = nextcord.Embed(
                title="📖 Urban Dictionary",
                color=nextcord.Color.yellow()
            )
            embed.add_field(name=f"Definition of **{term}**", value=definition, inline=True)
            embed.add_field(name="**Example:**", value=example)
        else:
            ctx.send(f"❌ **No definition for {term}!")
        
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Urban(bot))
