import json

import nextcord
import wikipediaapi
from nextcord.ext import commands


class Wiki(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="wikipedia", description="Search Wikipedia Articles")
    async def search_wikipedia(self, interaction, *, query):
        try:
            headers = {'User-Agent': 'StarloExo Bot/1.0 (Discord Bot)'}
            wiki_wiki = wikipediaapi.Wikipedia('en', headers=headers)
            page = wiki_wiki.page(query)
            page_summary = page.summary

            if page_summary:
                image_url = f"https://en.wikipedia.org/wiki/File:{page.title.replace(' ', '_')}.png"
            
                embed = nextcord.Embed(
                    title=query,
                    description=page_summary,
                    color=0xffffff
                )
                embed.set_image(url=image_url)
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f"❌ {interaction.author.mention} **No Wikipedia page found for the given query!**")
        except json.JSONDecodeError:
            await interaction.response.send_message("⚠️ Error: **Invalid JSON response from the Wikipedia API.**")
        except Exception as e:
            await interaction.response.send_message(f"**Error:** {str(e)}")


def setup(bot):
    bot.add_cog(Wiki(bot))
