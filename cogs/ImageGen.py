import io
from PIL import Image
import nextcord
from nextcord.ext import commands
import requests
import os
from dotenv import load_dotenv
from main import premium_check

load_dotenv()

class Art(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        self.headers = {"Authorization": f"Bearer {os.getenv('HUGGING_FACE_API')}"}

    @nextcord.slash_command(
        name='ai_art', 
        description="Generates an AI image based on your prompt!",
        guild_ids=[1237746712291049483]
    )
    @premium_check()
    async def generate_image(self, interaction: nextcord.Interaction, prompt: str):
        try:
            response = requests.post(self.api_url, headers=self.headers, json={"inputs": prompt})
            response.raise_for_status()

            image = Image.open(io.BytesIO(response.content))
            with io.BytesIO() as image_binary:
                image.save(image_binary, 'JPEG')
                image_binary.seek(0)
                await interaction.response.send_message(
                    file=nextcord.File(fp=image_binary, filename='generated_image.jpg')
                )
        except Exception as e:
            await interaction.response.send_message("Error occurred while generating the image.")
            
def setup(bot):
    bot.add_cog(Art(bot))
