import nextcord
from nextcord.ext import commands
import random


class EightBall(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="8ball", help="Ask a random question for random Yes/No answers!")
    async def eight_ball(self, ctx, *, question: str):
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
        await ctx.send(f"🎱 {ctx.author.display_name}: {question}\nAnswer: {answer}")


def setup(bot):
    bot.add_cog(EightBall(bot))