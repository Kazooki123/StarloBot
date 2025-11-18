import nextcord
from nextcord.ext import commands
import os
import requests
from dotenv import load_dotenv

load_dotenv("../.env")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")


class Movies(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="movie", description="Search for a movie using TMDb")
    async def search_movie(self, interaction: nextcord.Interaction, *, movie_name: str):
        """
        Search for a movie using TMDb API!
        """
        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}"
        response = requests.get(url).json()

        if not response["results"]:
            await interaction.response.send_message(f"❌ {interaction.author.mention} **No movie found!**")
            return

        movie = response["results"][0]
        title = movie["title"]
        release_date = movie.get("release_date", "Unknown")
        rating = movie.get("vote_average", "N/A")
        description = movie.get("overview", "No description available.")
        poster_path = movie.get("poster_path")

        embed = nextcord.Embed(
            title=title,
            description=description,
            color=nextcord.Color.magenta()
        )
        embed.add_field(name="📅 Release Date", value=release_date, inline=True)
        embed.add_field(name="⭐ Rating", value=str(rating), inline=True)

        if poster_path:
            embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w500{poster_path}")

        await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(Movies(bot))
