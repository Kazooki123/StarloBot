import nextcord
from nextcord.ext import commands
import requests
import random

class Quotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="quote")
    async def quote(self, ctx):
        """Tells a quote!"""
        try:
            response = requests.get("https://type.fit/api/quotes")
            quotes = response.json()
            random_quote = random.choice(quotes)
    
            quote_text = random_quote['text']
            quote_author = random_quote['author']

            await ctx.send(f"{quote_text} - {quote_author}")
        except Exception as e:
            print(f"Error in quote command: {e}")
            await ctx.send("An error occurred while processing the command.")

def setup(bot):
    bot.add_cog(Quotes(bot))