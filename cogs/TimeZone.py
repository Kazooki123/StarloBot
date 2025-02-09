import nextcord
from nextcord.ext import commands
import requests
import datetime


class Timezone(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(
        name="timezone",
        description="Sends a timezone!",
        guild_ids=[1237746712291049483]
    )
    async def timezone(self, ctx: nextcord.Interaction, country_or_city):
        try:
            response = requests.get(f"https://worldtimeapi.org/api/timezon/{country_or_city}")
            data = response.json()
        
            if response.status_code == 400 or "error" in data:
                await ctx.send("Cannot find. Please provide a valid country or city.")
            else:
                timezone = data["timezone"]
                current_time = datetime.strptime(data["datetime", "%Y-%m-%dT%H:%M:%S.%f%z"])
                formatted_time = current_time.strftime("%Y-%m-%d%H:%M:%S")
                await ctx.send(f"Timezone: {timezone}\nCurrent Time: {formatted_time}")
        except requests.exceptions.RequestException as e:
            await ctx.send(f"An error occurred: {str(e)}")


def setup(bot):
    bot.add_cog(Timezone(bot))
