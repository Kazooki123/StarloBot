import os
import datetime
import nextcord
from dotenv import load_dotenv
from nextcord.ext import commands
import requests

load_dotenv('../.env')

WEATHER_KEY = os.getenv("WEATHER_KEY")
WEATHER_API_URL = "http://api.weatherapi.com/v1/current.json?key={key}&q={location}&aqi=no"
FORECAST_API_URL = "http://api.weatherapi.com/v1/forecast.json?key={key}&q={location}&days=3&aqi=no&alerts=yes"


class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.thumbnail = "https://avatars.githubusercontent.com/u/1743227?s=200&v=4"

    @nextcord.slash_command(name='weather', description='Get the latest real-time weather update!')
    async def get_weather(self, interaction, *, location):
        url = WEATHER_API_URL.format(key=WEATHER_KEY, location=location)

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            guild = interaction.guild

            embed = nextcord.Embed(
                title=f"Weather in {data['location']['name']}, {data['location']['country']}",
                color=0xf56e25,
                timestamp=datetime.datetime.utcnow()
            )

            if guild and guild.icon:
                embed.set_author(name=guild.name, icon_url=guild.icon.url)

            # Add weather data
            embed.add_field(name="🌡️ Temperature",
                            value=f"{data['current']['temp_c']}°C ({data['current']['temp_f']}°F)", inline=True)
            embed.add_field(name="💧 Humidity", value=f"{data['current']['humidity']}%", inline=True)
            embed.add_field(name="💨 Wind", value=f"{data['current']['wind_kph']} km/h", inline=True)
            embed.add_field(name="🌤️ Condition", value=f"{data['current']['condition']['text']}", inline=False)

            embed.set_thumbnail(url=f"https:{data['current']['condition']['icon']}")

            embed.set_footer(text=f"Last updated: {data['current']['last_updated']}")

            await interaction.response.send_message(embed=embed)

        except requests.exceptions.RequestException as e:
            await interaction.response.send_message(f"❌ Error: Could not retrieve weather data for {location}. {str(e)}")

    @nextcord.slash_command(name='forecast', description='Get a 3-day weather forecast')
    async def get_forecast(self, interaction, *, location):
        url = FORECAST_API_URL.format(key=WEATHER_KEY, location=location)

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            embed = nextcord.Embed(
                title=f"Weather Forecast for {data['location']['name']}, {data['location']['country']}",
                color=0xf56e25,
                timestamp=datetime.datetime.utcnow()
            )

            for day in data['forecast']['forecastday']:
                date = datetime.datetime.strptime(day['date'], '%Y-%m-%d').strftime('%A, %b %d')
                condition = day['day']['condition']['text']
                max_temp = day['day']['maxtemp_c']
                min_temp = day['day']['mintemp_c']
                rain_chance = day['day']['daily_chance_of_rain']

                embed.add_field(
                    name=f"📅 {date}",
                    value=f"Condition: {condition}\nTemp: {min_temp}°C to {max_temp}°C\nChance of Rain: {rain_chance}%",
                    inline=False
                )

            embed.set_thumbnail(url=f"https:{data['current']['condition']['icon']}")
            embed.set_footer(text="Data provided by WeatherAPI.com")

            await interaction.response.send_message(embed=embed)

        except requests.exceptions.RequestException as e:
            await interaction.response.send_message(f"❌ Error: Could not retrieve forecast data for {location}. {str(e)}")


def setup(bot):
    bot.add_cog(Weather(bot))
