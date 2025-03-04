from nextcord.ext import commands
import requests

class Urban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(
        name="urban"
    )
    async def urban(self, ctx, *, term):
        url = f"https://api.urbandictionary.com/v0/define?term={term}"
    
        response = requests.get(url)
        data = response.json()
    
        if len(data["list"]) > 0:
            definition = data["list"][0]["definition"]
            example = data["list"][0]["example"]
            output = f"Definition of **{term}**:\n\n{definition}\n\nExample:\n{example}"
        else:
            output = f"No definition found for **{term}**."
        
        await ctx.send(output)


def setup(bot):
    bot.add_cog(Urban(bot))
