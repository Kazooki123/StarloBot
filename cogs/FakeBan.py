import nextcord
from nextcord.ext import commands
import asyncio

class FakeBan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="fakeban", help="Prank your discord members with this.")
    async def fakeban(self, ctx, user: nextcord.Member):
        """
        Pretends to ban a user (prank command).
        """
        msg = await ctx.send(f"🚨 **Banning {user.mention}...**")
        await asyncio.sleep(3)
        await msg.edit(content="🔁 **Checking Discord servers...**")
        await asyncio.sleep(2)
        await msg.edit(content="🛠️ **Verifying ban hammer...**")
        await asyncio.sleep(2)
        await msg.edit(content=f"❌ **Error! {user.mention} is too powerful to be banned!**")
        
def setup(bot):
    bot.add_cog(FakeBan(bot))