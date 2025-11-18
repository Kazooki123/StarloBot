import nextcord
from nextcord.ext import commands
import aiohttp
import asyncio


class Verse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(name="bibleverse", description="Outputs a bible verse from your text.")
    async def bibleverse(self, interaction: nextcord.Interaction, verse: str):
        try:
            await interaction.response.defer()
            
            verse = verse.strip()
            url = f"https://bible-api.com/{verse}"
        
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        verse_data = await response.json()
                        text = verse_data["text"]
                        
                        embed = nextcord.Embed(title="Bible Verse:", color=nextcord.Color.purple())
                        embed.add_field(name=verse, value=f"**{text}**")
                        
                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send("Failed to retrieve the Bible verse.")
        except asyncio.TimeoutError:
            await interaction.followup.send("Request timed out. Please try again.")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")


def setup(bot):
    bot.add_cog(Verse(bot))
