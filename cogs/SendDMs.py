import nextcord
from nextcord.ext import commands
import re

class SendDM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(
        name="dm",
        description="Send a DM to a user!",
        guild_ids=[1237746712291049483]
    )
    async def dm(self, interaction: nextcord.Interaction, member: nextcord.Member, *, message: str):
        """
        Send a anonymous DM.
        """
        bad_words = ["fuck", "shit", "pussy", "kill", "k1ll", "fck", "sh1t", "shitty", "kys", "keys", "retard", "nigga", "nigger", "dickhead", "dipshit", "retarded", "shithead", "bullshit", "whore", "slut", "nazi", "nazis", "butthole", "sex", "porn", "s3x", "p0rn", "pornography", "fuckoff", "fuckyou", "murder", "dox", "doxx", "doxxing", "dumbass", "stupid", "idiot", "rape", "bitch", "ass", "bitchass", "faggot", "gay", "homophobic"]
        
        if any(re.search(rf"\b{word}\b", message, re.IGNORECASE) for word in bad_words):
            await interaction.response.send_message("❌ Message blocked for inappropriate content.")
            return
        
        try:
            await member.send(f"📩 Anonymous Message: {message}")
            await interaction.response.send_message("✅ Message sent anonymously!")
        except nextcord.Forbidden:
            await interaction.response.send_message("❌ Cannot send DM. User may have DMs disabled.")
            
def setup(bot):
    bot.add_cog(SendDM(bot))