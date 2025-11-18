import nextcord
from nextcord.ext import commands
import random


class EightBall(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="8ball", description="Ask random questions for a random Yes/No answers!")
    async def eight_ball(self, interaction: nextcord.Interaction, *, question: str):
        """
        Answers a yes/no question with a random response
        """
        responses = [
            "**Yes**",
            "**No**",
            "**Maybe**",
            "**Absolutely!**",
            "**Very doubtful**",
            "**Ask again later**",
            "**Signs point to yes**",
            "**Certainly!**",
            "**My sources say no**",
            "**Without a doubt!**",
            "**It is certain!**",
            "**I have no idea**",
            "**Better not tell you now**"
        ]

        answer = random.choice(responses)
        await interaction.response.send_message(f"🎱 {interaction.author.mention}: {question}\nAnswer: {answer}")


def setup(bot):
    bot.add_cog(EightBall(bot))
