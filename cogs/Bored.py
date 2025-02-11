import nextcord
from nextcord.ext import commands
import requests

class Bored(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="bored")
    async def bored(self, ctx):
        """Suggests a random activity when you're bored!"""
        try:
            response = requests.get("https://www.boredapi.com/api/activity")
            data = response.json()
            
            activity = data['activity']
            activity_type = data['type']
            participants = data['participants']
            
            embed = nextcord.Embed(
                title="🎯 Random Activity",
                description=f"**{activity}**",
                color=0x00ff00
            )
            embed.add_field(name="Type", value=activity_type.capitalize(), inline=True)
            embed.add_field(name="Participants needed", value=str(participants), inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"Error in bored command: {e}")
            await ctx.send("Sorry, I couldn't find an activity right now. Try again later!")

def setup(bot):
    bot.add_cog(Bored(bot))