import nextcord
from nextcord.ext import commands
import re

class SendDM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="dm")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def dm(self, ctx, member: nextcord.Member, *, message: str):
        """
        Send a anonymous DM.
        """
        bad_words = ["badword"]
        
        if any(re.search(rf"\b{word}\b", message, re.IGNORECASE) for word in bad_words):
            await ctx.send("❌ Message blocked for inappropriate content.")
            return
        
        try:
            await member.send(f"📩 Anonymous Message: {message}")
            await ctx.send("✅ Message sent anonymously!")
        except nextcord.Forbidden:
            await ctx.send("❌ Cannot send DM. User may have DMs disabled.")
            
def setup(bot):
    bot.add_cog(SendDM(bot))