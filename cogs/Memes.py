from nextcord.ext import commands
import requests
import random


class Memes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(
        name="memes"
    )
    async def meme(ctx):
        response = requests.get("https://api.imgflip.com/get_memes")
        if response.status_code == 200:
            meme_data = response.json()
            meme = random.choice(meme_data)
            meme_url = meme['url']
            await ctx.send(meme_url)
        else:
            await ctx.send("Failed to fetch a meme. Please try again later.")
        
        
def setup(bot):
    bot.add_cog(Memes(bot))
