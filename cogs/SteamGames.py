import nextcord
from nextcord.ext import commands
import requests


class SteamGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="steam", description="Search steam games with their rates and price!")
    async def steam_game_search(self, interaction, *, game_name: str):
        """
        Search for a Steam game and display its details
        """
        search_url = f"https://store.steampowered.com/api/storesearch?term={game_name}&l=english&cc=US"
        response = requests.get(search_url).json()

        if not response.get("total", 0) > 0:
            await interaction.response.send_message(f"❌ {interaction.author.mention} **No game found!**")
            return

        game = response["items"][0]
        app_id = game["id"]

        details_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc=US"
        details_response = requests.get(details_url).json()

        if not details_response[str(app_id)]["success"]:
            await interaction.response.send_message(f"❌ {interaction.author.mention} **Failed to fetch game details!**")
            return

        game_data = details_response[str(app_id)]["data"]

        embed = nextcord.Embed(
            title=game_data["name"],
            description=game_data.get("short_description", "No description available."),
            color=nextcord.Color.gold(),
            url=f"https://store.steampowered.com/app/{app_id}"
        )

        if "price_overview" in game_data:
            price = game_data["price_overview"]["final_formatted"]
            embed.add_field(name="💰 Price", value=price, inline=True)
        else:
            embed.add_field(name="💰 Price", value="Free/Not Available", inline=True)

        if game_data.get("metacritic"):
            rating = f"{game_data['metacritic']['score']}/100"
            embed.add_field(name="⭐ Metacritic", value=rating, inline=True)

        if "release_date" in game_data:
            embed.add_field(name="📅 Release Date",
                            value=game_data["release_date"].get("date", "Unknown"),
                            inline=True)

        if "header_image" in game_data:
            embed.set_thumbnail(url=game_data["header_image"])

        await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(SteamGames(bot))
