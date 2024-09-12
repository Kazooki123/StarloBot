import nextcord
from nextcord.ext import commands
import requests
import random


class Quotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(name="quote", description="Tells a quote!")
    async def quote(self, ctx: nextcord.Interaction):
        response = requests.get("https://type.fit/api/quotes")
    
        quotes = response.json()
        random_quote = random.choice(quotes)
    
        quote_text = random_quote['text']
        quote_author = random_quote['author']

        await ctx.send(f"{quote_text} - {quote_author}")


def setup(bot):
    bot.add_cog(Quotes(bot))