import nextcord
from nextcord.ext import commands
import requests


class Jokes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(name='jokes', description="Tells a funny joke!")
    async def jokes(self, ctx: nextcord.Interaction):

        try:
            # Fetch a random joke from JokeAPI
            response = requests.get('https://v2.jokeapi.dev/joke/Programming,Miscellaneous,Pun,Spooky,Christmas?blacklistFlags=nsfw,religious,political,racist,sexist')
            response.raise_for_status()  # Raise an HTTPError for bad responses
            data = response.json()

            # Check if it's a two-part joke or a single-part joke
            if 'delivery' in data:
                embed = nextcord.Embed(title="JOKE!", color=nextcord.Color.red())
                embed.add_field(name="Joke for you", value=f"{ctx.author.mention}, here's a joke for you:\n{data['setup']}\n{data['delivery']}", inline=False)
                await ctx.send(embed=embed)
            else:
                embed.add_field(name="Joke for you", value=f"{ctx.author.mention}, here's a joke for you:\n{data['joke']}", inline=False)
                await ctx.send(embed=embed)
        except Exception as e:
            print(f"Error in !jokes command: {e}")
            await ctx.send("An error occurred while processing the command.")


def setup(bot):
    bot.add_cog(Jokes(bot))