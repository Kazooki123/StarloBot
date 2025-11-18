import nextcord
from nextcord import Embed
from nextcord.ext import commands
import aiohttp


class KanyeQuotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="kanye", description="Sends a random quote by Kanye West")
    async def kanye_quote(interaction: nextcord.Interaction):
        async with aiohttp.ClientSession() as session:
            try:
                url = "https://api.kanye.rest/"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        quote = data.get("quote", "No quote available")

                        embed = Embed(
                            title="Kanye West be like:",
                            description=f"*\"{quote}\"*",
                            color=0xf6b9d
                        )
                        embed.set_author(name="Kanye West", icon_url="https://imgur.com/gallery/if-arya-stark-was-idiot-p1bDLwl/t/kanye_west")
                        embed.set_footer(text="Kanye West Quote ❣️")

                        await interaction.response.send_message(embed=embed)

                    else:
                        await interaction.response.send_message(f"❌ Error fetching Kanye quote: {response.status}")
            except Exception as e:
                await interaction.response.send_message(f"✖️ **An error occurred:** {str(e)}")


def setup(bot):
    bot.add_cog(KanyeQuotes(bot))
