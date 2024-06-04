import nextcord
from nextcord.ext import commands
import requests
from dotenv import load_dotenv
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import premium_check

load_dotenv('../.env')


HUGGING_FACE_API_TOKEN = os.getenv("HUGGING_FACE_API")

class Art(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(name='ai_art')
    @premium_check()
    async def generate_image(self, ctx: nextcord.Interaction, *, prompt):
        api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {HUGGING_FACE_API_TOKEN}"}
        # payload = {
        #     "inputs": prompt,
        #     "options": {
        #         "wait_for_model": True
        #     }
        # }
        def query(payload):
            response = requests.post(api_url, headers=headers, json=payload)
	                             
            return response.content
    
        try:
        
            bytes = query(
                {
                    "inputs": prompt
                }
            )
            import io
            from PIL import Image
            image = Image.open(io.BytesIO(bytes))
            with io.BytesIO() as image_binary:
                image.save(image_binary, 'JPEG')
                image_binary.seek(0)
                await ctx.send(file=nextcord.File(fp=image_binary, filename='generated_image.jpg'))


        except requests.exceptions.RequestException as e:
            print(f"API Request Error: {e}")
            await ctx.send("Error occurred while making the API request.")

        except json.JSONDecodeError as e:
            print(f"JSON Decoding Error: {e}")
            await ctx.send("Error occurred while decoding the API response.")
            
def setup(bot):
    bot.add_cog(Art(bot))