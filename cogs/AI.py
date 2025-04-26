import io
import os

import nextcord
import requests
from PIL import Image
from dotenv import load_dotenv
from nextcord.ext import commands

from utils.PremiumCheck import premium_check

load_dotenv('../.env')

ANTHROPIC_API = os.getenv("ANTHROPIC_API")


class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        self.headers = {"Authorization": f"Bearer {os.getenv('HUGGING_FACE_API')}"}

    @commands.command(name='ai_art', help='Create A.I Image!')
    @premium_check()
    async def generate_image(self, ctx, prompt: str):
        try:
            response = requests.post(self.api_url, headers=self.headers, json={"inputs": prompt})
            response.raise_for_status()

            image = Image.open(io.BytesIO(response.content))
            with io.BytesIO() as image_binary:
                image.save(image_binary, "PNG")
                image_binary.seek(0)
                await ctx.send(
                    file=nextcord.File(fp=image_binary, filename='generated_image.png')
                )
        except Exception as e:
            await ctx.send(f"Error occurred while generating the image: {e}")

    @commands.command(name="activate", help="Activate the Chatbot which uses Claude!")
    async def activate_claude(self, ctx):
        """Activate the bot to chat in a specific channel"""

    @commands.command(name="deactivate", help="Deactivate the Chatbot")
    async def deactivate_claude(self, ctx):
        """
        Deactivates Claude for chatting in a discord channel
        """


def setup(bot):
    bot.add_cog(AI(bot))
