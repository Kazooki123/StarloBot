import nextcord
from nextcord.ext import commands
import requests
import random
from dotenv import load_dotenv
import os

load_dotenv('../.env')

API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")

class SearchImage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command()
    async def searchimage(self, ctx: nextcord.Interaction, *, query):
        url = f"https://www.googleapis.com/customsearch/v1"
        params = {
            "key": API_KEY,
            "cx": SEARCH_ENGINE_ID,
            "searchType": "image",
            "q": query
        }  
    
        response = requests.get(url, params=params).json()
        items = response.get("items", [])
        if not items:
            await ctx.send("No image found.")
            return
    
        image_url = random.choice(items)["link"]
        await ctx.send(image_url)
        