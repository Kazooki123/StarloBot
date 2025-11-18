import nextcord
from nextcord.ext import commands
import requests


class Bored(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(name="bored", description="Suggests a random activity when you're bored!")
    async def bored(self, interaction: nextcord.Interaction):
        """Suggests a random activity when you're bored!"""
        try:
            response = requests.get("https://bored.api.lewagon.com/api/activity/")
            data = response.json()
            
            activity = data['activity']
            activity_type = data['type']
            participants = data['participants']
            
            embed = nextcord.Embed(
                title="🎯 Random Activity",
                description=f"**{activity}**",
                color=nextcord.Color.gold()
            )
            embed.add_field(name="Type", value=activity_type.capitalize(), inline=True)
            embed.add_field(name="Participants needed", value=str(participants), inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            print(f"Error in bored command: {e}")
            await interaction.response.send_message("Sorry, I couldn't find an activity right now. Try again later!")


def setup(bot):
    bot.add_cog(Bored(bot))
