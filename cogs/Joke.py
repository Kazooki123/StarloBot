import nextcord
from nextcord.ext import commands
import requests


class Jokes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(name="jokes", description="Tells a random joke")
    async def jokes(self, interaction):
        try:
            response = requests.get('https://v2.jokeapi.dev/joke/Programming,Miscellaneous,Pun,Spooky,Christmas?blacklistFlags=nsfw,religious,political,racist,sexist')
            response.raise_for_status()
            data = response.json()

            embed = nextcord.Embed(title="JOKE!", color=nextcord.Color.red())
            
            if 'delivery' in data:
                joke_text = f"{data['setup']}\n{data['delivery']}"
            else:
                joke_text = data['joke']
                
            embed.add_field(name="Joke for you", value=f"{interaction.author.mention}, here's a joke for you:\n{joke_text}", inline=False)
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            print(f"Error in jokes command: {e}")
            await interaction.response.send_message("An error occurred while processing the command.")


def setup(bot):
    bot.add_cog(Jokes(bot))
