import nextcord
from nextcord.ext import commands
import requests
from dotenv import load_dotenv
import os

load_dotenv('../.env')

API_URL = "https://libretranslate.com/translate"
API_KEY = os.getenv("TRANSLATE_API_KEY")


class Translate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="translate")
    async def translate(self, ctx, target_lang: str, *, text: str):
        """
        Translate texts to the specified language.
        Usage: !translate <language_code> <text>
        Example: !translate es Hello, how are you?
        """
        supported_langs = ["en", "es", "fr", "de", "it", "ru", "zh", "ja", "ko"]
        if target_lang not in supported_langs:
            await ctx.send(f"❌ {ctx.author.mention} **Unsupported language!** Try: {','.join(supported_langs)}")
            return
        
        try:
            response = requests.post(API_URL, json={
                "q": text,
                "source": "auto",
                "target": target_lang,
                "format": "text",
                "api_key": API_KEY
            })
            
            data = response.json()
            if "translatedText" in data:
                await ctx.send(f"**Translated:** {data['translatedText']}")
            else:
                await ctx.send("❌ Translation failed! **API might be down.**")
        except requests.exceptions.RequestException:
            await ctx.send("⚠️Error: Could not connect to the translation server!")


def setup(bot):
    bot.add_cog(Translate(bot))
