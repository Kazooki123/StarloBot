import nextcord
from nextcord.ext import commands
import requests


class Verse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(
        name="bibleverse",
        description="Sends a bible verse!",
        guild_ids=[1237746712291049483]    
    )
    async def bibleverse(interaction: nextcord.Interaction, verse):
        verse = verse.strip()
        url = f"https://bible-api.com/{verse}"
    
        response = requests.get(url)
    
        if response.status_code == 200:
            verse_data = response.json()
            text = verse_data["text"]
        
            await interaction.response.send_message(f"Bible Verse: {text}")
        else:
            await interaction.response.send_message("Failed to retrieve the Bible verse.")
            
            
def setup(bot):
    bot.add_cog(Verse(bot))
