import nextcord
from nextcord.ext import commands
import random


class Ship(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(name="ship", description="Ship you and your partner and see the results!")
    async def ship(self, interaction, user1: nextcord.Member, user2: nextcord.Member):
        """
        Checks love compatibility between two users.
        """
        love_percentage = random.randint(1, 100)
        
        if love_percentage > 80:
            message = f"{user1.mention} and {user2.mention} **are in love! 💕**"
        elif love_percentage > 60:
            message = f"{user1.mention} and {user2.mention} **are in love! 💖**"
        elif love_percentage > 50:
            message = f"{user1.mention} and {user2.mention} **have the potential! Maybe a few dates could work. 💗**"
        elif love_percentage > 30:
            message = f"{user1.mention} and {user2.mention}😅 it's very complicated.. Maybe as friends for now?"
        else:
            message = "💔 This **ship sank** before it even sailed..."
            
        embed = nextcord.Embed(
            title="💘 Love Compatibility 💘",
            description=f"**{user1.mention}💖{user2.mention}**\n💗 **{love_percentage}% Compatibility**\n{message}",
            color=nextcord.Color.purple()
        )
        await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(Ship(bot))
