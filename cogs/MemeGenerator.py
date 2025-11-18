import nextcord
from dotenv import load_dotenv
from nextcord.ext import commands
import os
import requests
from dotenv import load_dotenv

load_dotenv('../.env')

IMGFLIP_USERNAME = os.getenv("IMGFLIP_USERNAME")
IMGFLIP_PASSWORD = os.getenv("IMGFLIP_PASSWORD")


def get_meme_templates():
    url = "https://api.imgflip.com/get_memes"
    response = requests.get(url).json()
    if response["success"]:
        return {meme["name"].lower(): meme["id"] for meme in response["data"]["memes"]}
    return {}


class MemeGenerator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.templates = get_meme_templates()

    @nextcord.slash_command(name="meme", description="Generate a meme!")
    async def generate_meme(self, interaction, *, input_text: str):
        """
        Generate a meme using ImgFlip API
        Usage: !meme <template_name> | <top_text> | <bottom_text>
        """
        parts = input_text.split(" | ", 1)

        if len(parts) < 2:
            return await interaction.response.send_message(
                f"❌ {interaction.author.mention} **Invalid format!** Use `!meme <template_name> | <top_text> | <bottom_text>`")

        template_name = parts[0].lower()
        text = parts[1]

        matching_template = None
        for template in self.templates:
            if template_name in template:
                matching_template = template
                break

        if not matching_template:
            return await interaction.response.send_message(
                f"❌ {interaction.author.mention} **Invalid Template!** Use `!meme_list` to see available templates.")

        if "|" in text:
            top_text, bottom_text = text.split("|", 1)
        else:
            top_text, bottom_text = text, ""

        url = "https://api.imgflip.com/caption_image"
        payload = {
            "template_id": self.templates[matching_template],
            "username": IMGFLIP_USERNAME,
            "password": IMGFLIP_PASSWORD,
            "text0": top_text.strip(),
            "text1": bottom_text.strip()
        }
        response = requests.post(url, data=payload).json()

        if response["success"]:
            meme_url = response["data"]["url"]
            embed = nextcord.Embed(
                title="Your Meme is Ready!",
                color=0x00ff00
            )
            embed.set_image(url=meme_url)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"⚠️ {interaction.author.mention} **Failed to generate meme!** Try again.")

    @nextcord.slash_command(name="meme_list", description="List meme templates available!")
    async def list_memes(self, interaction):
        meme_list = "\n".join([f"• {name.title()}" for name in list(self.templates.keys())[:10]])
        embed = nextcord.Embed(
            title="Available Meme Templates",
            description=f"{meme_list}\n\n*Showing 10 of {len(self.templates)} templates*",
            color=0x3498db
        )
        await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(MemeGenerator(bot))
