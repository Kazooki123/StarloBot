import os

import nextcord
import requests
from dotenv import load_dotenv
from nextcord.ext import commands

load_dotenv("../.env")
NINJA_API_KEY = os.getenv("NINJA_API_KEY")


class Animal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_animal_fact(self, animal):
        url = f"https://api.api-ninjas.com/v1/animals?name={animal}"
        headers = {"X-Api-Key": NINJA_API_KEY}
        response = requests.get(url, headers=headers)

        if response.status_code == 200 and response.json():
            return response.json()[0]["characteristics"]["slogan"]

        return "No fact available."

    def get_animal_image(self, animal):
        urls = {
            "cat": "https://api.thecatapi.com/v1/images/search",
            "dog": "https://api.thedogapi.com/v1/images/search",
            "duck": "https://random-d.uk/api/random",
            "panda": "https://source.unsplash.com/400x300/?panda"
        }

        if animal in urls:
            response = requests.get(urls[animal]).json()
            if animal == "duck":
                return response["url"]
            return response[0]["url"]

        return None
        
    @nextcord.slash_command(name="animal", description="Send a random animal image and their facts!")
    async def animal_info(self, interaction: nextcord.Interaction, animal: str):
        """
        Send an animal random animal image of either a cat, dog, duck or panda with their facts.
        Usage: !animal <animal_name>
        """
        animal = animal.lower()
        if animal not in ["cat", "dog", "duck", "panda"]:
            await interaction.response.send_message(f"❌ {interaction.author.mention} **Supported animals:** `cat, dog, duck, panda`")
            return

        fact = self.get_animal_fact(animal)
        image_url = self.get_animal_image(animal)

        embed = nextcord.Embed(
            title=f"🐾 {animal.capitalize()} Fact!",
            description=fact,
            color=nextcord.Color.teal()
        )
        if image_url:
            embed.set_image(url=image_url)

        await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(Animal(bot))
