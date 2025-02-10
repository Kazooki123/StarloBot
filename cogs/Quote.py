import nextcord
from nextcord.ext import commands
import requests
import random


class Quotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(
        name="quote",
        description="Tells a quote!",
        guild_ids=[1237746712291049483]    
    )
    async def quote(self, interaction: nextcord.Interaction):
        try:
            response = requests.get("https://type.fit/api/quotes")
    
            quotes = response.json()
            random_quote = random.choice(quotes)
    
            quote_text = random_quote['text']
            quote_author = random_quote['author']

            await interaction.response.send_message(f"{quote_text} - {quote_author}")
        except Exception as e:
            print(f"Error in quote command: {e}")
            await interaction.response.send_message("An error occurred while processing the command.")

def setup(bot):
    bot.add_cog(Quotes(bot))