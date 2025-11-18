import nextcord
from nextcord.ext import commands
import requests
import random


class Memes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(name="memes", description="Displays funny memes!")
    async def meme(interaction: nextcord.Interaction):
        response = requests.get("https://api.imgflip.com/get_memes")
        if response.status_code == 200:
            meme_data = response.json()
            meme = random.choice(meme_data)
            meme_url = meme['url']
            await interaction.response.send_message(meme_url)
        else:
            await interaction.response.send_message("Failed to fetch a meme. Please try again later.")
        
        
def setup(bot):
    bot.add_cog(Memes(bot))
