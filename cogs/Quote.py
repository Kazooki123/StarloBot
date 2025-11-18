import nextcord
import asyncio
from nextcord.ext import commands
import aiohttp
import random

class Quotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(name="quote")
    async def quote(self, interaction: nextcord.Interaction):
        """Tells a quote!"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://type.fit/api/quotes", timeout=aiohttp.ClientTimeout(total=10)) as response:
                    # Check if response is successful
                    if response.status != 200:
                        await interaction.response.send_message(f"Failed to fetch quote (Status: {response.status}). Please try again later.")
                        return
                    
                    # Get response text and check if it's empty
                    text = await response.text()
                    if not text:
                        await interaction.response.send_message("Received empty response from API. Please try again later.")
                        return
                    
                    quotes = await response.json()
                    
                    if not quotes or len(quotes) == 0:
                        await interaction.response.send_message("No quotes available. Please try again later.")
                        return
                    
                    random_quote = random.choice(quotes)
        
                    quote_text = random_quote.get('text', 'No text available')
                    quote_author = random_quote.get('author', 'Unknown').replace(', type.fit', '')

                    await interaction.response.send_message(f"*{quote_text}*\n\n— {quote_author}")
        except asyncio.TimeoutError:
            print(f"Error in quote command: Request timeout")
            await interaction.response.send_message("The request took too long. Please try again later.")
        except aiohttp.ClientError as e:
            print(f"Error in quote command: Network error - {e}")
            await interaction.response.send_message("Failed to connect to the quote API. Please try again later.")
        except Exception as e:
            print(f"Error in quote command: {e}")
            await interaction.response.send_message("An error occurred while processing the command.")


def setup(bot):
    bot.add_cog(Quotes(bot))
