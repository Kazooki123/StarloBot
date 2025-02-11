import io
from PIL import Image
import nextcord
from nextcord.ext import commands
import requests
import os

from dotenv import load_dotenv

load_dotenv('../.env')

intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

async def is_premium(user_id):
    async with bot.pg_pool.acquire() as connection:
        record = await connection.fetchrow(
            """
            SELECT premium_user FROM user_data
            WHERE user_id = $1;
            """, user_id
        )
        return record and record['premium_user']
        
def premium_check():
    async def predicate(ctx):
        if await is_premium(ctx.author.id):
            return True
        else:
            await ctx.send('Looks like you haven\'t been premium yet, please type !premium, Thank you.')
            return False

    return commands.check(predicate)

class Art(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        self.headers = {"Authorization": f"Bearer {os.getenv('HUGGING_FACE_API')}"}

    @commands.command(
        name='ai_art'
    )
    @premium_check()
    async def generate_image(self, ctx, prompt: str):
        try:
            response = requests.post(self.api_url, headers=self.headers, json={"inputs": prompt})
            response.raise_for_status()

            image = Image.open(io.BytesIO(response.content))
            with io.BytesIO() as image_binary:
                image.save(image_binary, 'JPEG')
                image_binary.seek(0)
                await ctx.send(
                    file=nextcord.File(fp=image_binary, filename='generated_image.jpg')
                )
        except Exception as e:
            await ctx.send("Error occurred while generating the image.")
            
def setup(bot):
    bot.add_cog(Art(bot))
