import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv
import os
from requests import get

load_dotenv()

WEATHER_KEY = os.getenv('WEATHER_KEY')
WEATHER_API_URL = 'http://api.weatherapi.com/v1/current.json?key={WEATHER_KEY}&q={}&aqi=no'


class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(
        name='weather',
        description="Sends an weather info!",
        guild_ids=[1237746712291049483]
    )
    async def get_weather(self, interaction: nextcord.Interaction, location):
        url = WEATHER_API_URL.format(location)
        guild = interaction.guild

        response = get(url)

        if response.status_code == 200:
            data = response.json()
            embed = nextcord.Embed(title=f"Weather in {location.title()}", color=0x00ffff)
            embed.set_thumbnail(url=guild.icon.url)
            embed.add_field(name="Temperature:", value=f"{data['current']['temp_c']}°C", inline=False)  
            embed.add_field(name="Condition:", value=f"{data['current']['condition']['text']}", inline=False)
            embed.set_footer(text=f"More info: https://www.weatherapi.com/weather/{location}")      

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"Error: Could not retrieve weather data for {location}.")
            

def setup(bot):
    bot.add_cog(Weather(bot))
