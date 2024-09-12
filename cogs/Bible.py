import nextcord
from nextcord.ext import commands
import requests


class Verse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(name="verse", description="Sends a bible verse!")
    async def bibleverse(ctx, verse):
        verse = verse.strip()
        url = f"https://bible-api.com/{verse}"
    
        response = requests.get(url)
    
        if response.status_code == 200:
            verse_data = response.json()
            text = verse_data["text"]
        
            await ctx.send(f"Bible Verse: {text}")
        else:
            await ctx.send("Failed to retrieve the Bible verse.")
            
            
def setup(bot):
    bot.add_cog(Verse(bot))
