from datetime import datetime

import nextcord
import requests
from bs4 import BeautifulSoup
from nextcord.ext import commands


class Aesthetics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="aesthetic", description="Returns a aesthetic image of your choice!")
    async def aesthetic_image(self, interaction: nextcord.Interaction, *, aesthetic_name: str):
        """Fetches aesthetic details from the Aesthetic Fandom Wiki."""
        base_url = "https://aesthetics.fandom.com/wiki/"
        search_url = base_url + aesthetic_name.replace(" ", "_")

        response = requests.get(search_url)

        if response.status_code != 200:
            await interaction.response.send_message("Could not retrieve aesthetic details. Please check the name and try again.")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find("h1", class_="page-header__title").text.strip()

        # Try to find the main image first
        image_tag = soup.find("img", class_="pi-image-thumbnail")

        if not image_tag:
            image_tag = soup.find("img", class_="thumbimage")

        image_url = image_tag["src"] if image_tag else "https://via.placeholder.com/300"

        embed = nextcord.Embed(
            title=title,
            url=search_url,
            color=nextcord.Color.purple()
        )
        embed.set_image(url=image_url)
        embed.set_footer(text=f"Requested by {interaction.author.name}", icon_url=interaction.author.avatar.url)
        embed.timestamp = datetime.utcnow()

        await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(Aesthetics(bot))
