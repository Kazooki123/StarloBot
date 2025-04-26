import nextcord
from nextcord.ext import commands
import requests
import datetime


class TimeZone(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="timezone")
    async def timezone(self, ctx, country_or_city):
        try:
            response = requests.get(f"https://worldtimeapi.org/api/timezone/{country_or_city}")
            data = response.json()
        
            if response.status_code == 400 or "error" in data:
                await ctx.send(f"❌ {ctx.author.mention} **Cannot find {country_or_city}!** Please provide a valid country or city.")
            else:
                timezone = data["timezone"]
                current_time = datetime.strptime(data["datetime", "%Y-%m-%dT%H:%M:%S.%f%z"])
                formatted_time = current_time.strftime("%Y-%m-%d%H:%M:%S")
                embed = nextcord.Embed(
                    title="⏱️ Timezone",
                    color=nextcord.Color.magenta()
                )
                embed.add_field(name="TimeZone:", value=f"**{timezone}**", inline=True)
                embed.add_field(name="Current Time:", value=f"**{current_time}**", inline=True)
                await ctx.send(embed=embed)
        except requests.exceptions.RequestException as e:
            await ctx.send(f"⚠️ **An error occurred:** {str(e)}")


def setup(bot):
    bot.add_cog(TimeZone(bot))
