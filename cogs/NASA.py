import nextcord
from nextcord.ext import commands
from nextcord import Embed, File
import aiohttp
import io
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('../.env')

NASA_API_KEY = os.getenv("NASA_API_KEY")


class NASA(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_commands(name="apod", description="Get NASA's astronomy Picture of the Day")
    async def astronomy_picture(interaction: nextcord.Interaction):
        async with aiohttp.ClientSession() as session:
            try:
                url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()

                        embed = Embed(
                            title=data.get("title", "Astronomy Picture of the Day"),
                            description=data.get("explanation", "")[:2048],
                            color=0x0099ff,
                            timestamp=datetime.strptime(data.get("date"), "%Y-%m-%d")
                        )

                        if data.get("media_type") == "image":
                            embed.set_image(url=data.get("url"))
                        else:
                            embed.add_field(name="Video URL", value=data.get("url"), inline=False)

                        embed.set_footer(text=f"Copyright: {data.get('copyright', 'NASA')}")
                        await interaction.response.send_message(embed=embed)
                    else:
                        await interaction.response.send_message(f"❌ Error fetching NASA APOD: {response.status}")

            except Exception as e:
                    await interaction.response.send_message(f"❌ An error occurred: {str(e)}")

    @nextcord.slash_command(name="marsrover", description="Get Mars Rover photos.")
    async def mars_rover(interaction: nextcord.Interaction, rover: str = "curiosity", sol: int = 1000):
        async with aiohttp.ClientSession() as session:
            try:
                url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/{rover.lower()}/photos?sol={sol}&api_key={NASA_API_KEY}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        photo = data.get("photos", [])

                        if not photo:
                            await interaction.response.send_message(f"❌ No photos found for {rover.capitalize()} on Sol {sol}")
                            return

                        photo = photo[0]
                        embed = Embed(
                            title=f"❤️ Mars Rover: {rover.capitalize()}",
                            description=f"**Camera:** {photo['camera']['full_name']}\n**Sol:** {sol}\n**Earth Date:** {photo['earth_date']}",
                            color=0xff4500
                        )
                        embed.set_image(url=photo["img_src"])
                        embed.set_footer(text=f"Rover: {rover.capitalize()} | **Total photos this sol**: {len(photo)}")
                        await interaction.response.send_message(embed=embed)
                    else:
                        await interaction.response.send_message(f"❌ **An error occurred:** {str(e)}")
            except Exception as e:
                await interaction.response.send_message(f"❌ **An error occurred:** {str(e)}")


def setup(bot):
    bot.add_cog(NASA(bot))
    
