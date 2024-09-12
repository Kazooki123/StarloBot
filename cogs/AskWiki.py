import nextcord
from nextcord.ext import commands
import wikipediaapi
import json


class Wiki(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    # Wikipedia Search command
    @nextcord.slash_command(description="Searches from Wikipedia! (Has limitations)")
    async def askwiki(self, ctx: nextcord.Interaction, *, query):
        try:
            headers = {'User-Agent': 'StarloExo Bot/1.0 (Discord Bot)'}
            wiki_wiki = wikipediaapi.Wikipedia('en', headers=headers)
            page = wiki_wiki.page(query)
            page_summary = page.summary

            if page_summary:
                image_url = f"https://en.wikipedia.org/wiki/File:{page.title.replace(' ', '_')}.png"
            
                embed = nextcord.Embed(title=query, description=page_summary)
                embed.set_image(url=image_url)
                await ctx.send(embed=embed)
            else:
                await ctx.send("No Wikipedia page found for the given query.")
        except json.JSONDecodeError:
            await ctx.send("Error: Invalid JSON response from the Wikipedia API.")
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")


def setup(bot):
    bot.add_cog(Wiki(bot))
