import nextcord
import asyncio
from nextcord.ext import commands


class HackSimulator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="hack", help="Do a hack prank on someone!")
    async def hack_prank(self, ctx, user: nextcord.Member):
        """
        Simulates hacking a user for prank XD
        """
        msg = await ctx.send(f"💻 **Hacking {user.mention}...**")

        steps = [
            "🔍 Finding IP Address...",
            "🗝️ Accessing the Discord database...",
            "🔐 Extracting Passwords...",
            "⬇️ Downloading Private Messages...",
            "❌ Error! Target is too secure!"
        ]

        for step in steps:
            await asyncio.sleep(3)
            await msg.edit(content=step)


def setup(bot):
    bot.add_cog(HackSimulator(bot))
