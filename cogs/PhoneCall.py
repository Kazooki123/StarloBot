import nextcord
from nextcord.ext import commands

class PhoneCall(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_calls = {}
        
    @commands.command(name="call")
    async def call(self, ctx, member: nextcord.Member, anonymous: bool = False):
        """Call another user. Use !call @user True for anonymous mode."""
        caller_id = ctx.author.id
        receiver_id = member.id
        
        if caller_id in self.active_calls or receiver_id in self.active_calls:
            await ctx.send("Either you or the user is already in a call!")
            return
    
        self.active_calls[caller_id] = receiver_id
        self.active_calls[receiver_id] = caller_id
        
        caller_name = "anonymous" if anonymous else ctx.author.display_name
        await member.send(f"📞 {caller_name} is calling you! Type `!answer` to connect!")
        await ctx.send(f"📞 **Calling {member.display_name} right now...**")
        
    @commands.command(name="answer")
    async def answer(self, ctx):
        """Answer a call."""
        receiver_id = ctx.author.id
        if receiver_id not in self.active_calls:
            await ctx.send("**❌ No one is calling you right now.**")
            return
        
        caller_id = self.active_calls[receiver_id]
        caller = self.bot.get_user(caller_id)
        
        await ctx.send(f"✅ Connected! You can chat with {caller.display_name} here.")
        await caller.send(f"✅ {ctx.author.display_name} has answered the call!")
        
    @commands.command(name="hangup")
    async def hangup(self, ctx):
        """End a call"""
        user_id = ctx.author.id
        if user_id not in self.active_calls:
            await ctx.send("You're not in a call!")
            return
        
        partner_id = self.active_calls[user_id]
        partner = self.bot.get_user(partner_id)
        
        await ctx.send("❌ **Call ended.**")
        await partner.send("❌ **Call ended.**")
        
        del self.active_calls[user_id]
        del self.active_calls[partner_id]
        
    @commands.command(name="reportcall")
    async def report(self, ctx, member: nextcord.Member, *, reason="No reason provided."):
        """Report a user for abusing the call system."""
        report_channel = self.bot.get_channel() # Add your report channel ID here
        await report_channel.send(f"🚨 {ctx.author.display_name} reported {member.display_name}: {reason}")
        await ctx.send("📩 Report submitted!")
        
def setup(bot):
    bot.add_cog(PhoneCall(bot))