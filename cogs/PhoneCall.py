import nextcord
from nextcord.ext import commands
import random

class PhoneCall(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_calls = {}
        
    @nextcord.slash_command(
        name="call",
        description="Chat with a stranger a cross servers!",
        guild_ids=[1237746712291049483]    
    )
    async def call(self, interaction: nextcord.Interaction, member: nextcord.Member, anonymous: bool = False):
        """"
        Call Another user. Use `/call @user True` for anonymous mode.
        """
        caller_id = interaction.author.id
        receiver_id = member.id
        
        if caller_id in self.active_calls or receiver_id in self.active_calls:
            await interaction.response.send_message("Either you or the user is already in a call!")
            return
    
        self.active_calls[caller_id] = receiver_id
        self.active_calls[receiver_id] = caller_id
        
        caller_name = "anonymous" if anonymous else interaction.author.display_name
        await member.send(f"📞 {caller_name} is calling you! Type `/answer` to connect!")
        await interaction.response.send_message(f"📞 Calling {member.display_name} right now...")
        
    @nextcord.slash_command(
        name="answer",
        description="Answer a call from a stranger!",
        guild_ids=[1237746712291049483]    
    )
    async def answer(self, interaction: nextcord.Interaction):
        """
        Answer a call.
        """
        receiver_id = interaction.author.id
        if receiver_id not in self.active_calls:
            await interaction.response.send_message("No one is calling you right now.")
            return
        
        caller_id = self.active_calls[receiver_id]
        caller = self.bot.get_user(caller_id)
        
        await interaction.response.send_message(f"✅ Connected! You can chat with {caller.display_name} here.")
        await caller.send(f"✅ {interaction.display_name} has answered the call!")
        
    @nextcord.slash_command(
        name="hangup",
        description="Hang up a call",
        guild_ids=[1237746712291049483]
    )
    async def hangup(self, interaction: nextcord.Interaction):
        """
        End a call
        """
        user_id = interaction.author.id
        if user_id not in self.active_calls:
            await interaction.response.send_message("You're not in a call!")
            return
        
        partner_id = self.active_calls[user_id]
        partner = self.bot.get_user(partner_id)
        
        await interaction.response.send_message("❌ Call ended.")
        await partner.send("❌ Call ended.")
        
        del self.active_calls[user_id]
        del self.active_calls[partner_id]
        
    @nextcord.slash_command(
        name="report",
        description="Report a call user and we'll take actions",
        guild_id=[1237746712291049483]
    )
    async def report(self, interaction: nextcord.Interaction, member: nextcord.Member, *, reason="No reason provided."):
        """
        Report a user for abusing the call system.
        """
        report_channel = self.bot.get_channel()
        await report_channel.send(f"🚨 {interaction.author.display_name} reported {member.display_name}: {reason}")
        await interaction.response.send_message("📩 Report submitted!")
        
def setup(bot):
    bot.add_cog(PhoneCall(bot))
