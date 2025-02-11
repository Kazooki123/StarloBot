import nextcord
from nextcord.ext import commands
import requests

class Jokes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(
        name='jokes'
    )
    async def jokes(self, ctx):
        try:
            response = requests.get('https://v2.jokeapi.dev/joke/Programming,Miscellaneous,Pun,Spooky,Christmas?blacklistFlags=nsfw,religious,political,racist,sexist')
            response.raise_for_status()
            data = response.json()

            embed = nextcord.Embed(title="JOKE!", color=nextcord.Color.red())
            
            if 'delivery' in data:
                joke_text = f"{data['setup']}\n{data['delivery']}"
            else:
                joke_text = data['joke']
                
            embed.add_field(name="Joke for you", value=f"{ctx.user.mention}, here's a joke for you:\n{joke_text}", inline=False)
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"Error in jokes command: {e}")
            await ctx.send("An error occurred while processing the command.")

def setup(bot):
    bot.add_cog(Jokes(bot))