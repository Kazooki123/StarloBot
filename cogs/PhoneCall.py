import nextcord
from nextcord.ext import commands
import json
import os
import re

BADWORDS_JSON = os.path.join(os.path.dirname(__file__), '..', 'json', 'badwords.json')


class PhoneCall(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_calls = {}

        try:
            with open(BADWORDS_JSON, 'r') as f:
                data = json.load(f)
                self.badwords = data.get('badwords', [])
        except Exception as e:
            print(f"⚠️ Error loading badwords json file: {e}")
            self.badwords = []

    def filter_message(self, message):
        filtered = message
        for word in self.badwords:
            pattern = rf'\b({word})\b'
            filtered = re.sub(pattern, r'||\1||', filtered, flags=re.IGNORECASE)
        return filtered

    @nextcord.slash_command(name="userphone", description="Text with your friend or even a stranger in Discord (Yggdrasil inspired)")
    async def userphone(self, interaction: nextcord.Interaction, member: nextcord.Member, anonymous: bool = False):
        if interaction.author.id == member.id:
            await interaction.response.send_message(f"❌ {interaction.author.mention} **You can't call yourself!**")
            return

        caller_id = interaction.author.id
        receiver_id = member.id

        if caller_id in self.active_calls or receiver_id in self.active_calls:
            await interaction.response.send_message(f"⚠️ {interaction.author.mention} **Either you or the user is already in a call!**")
            return

        self.active_calls[caller_id] = receiver_id
        self.active_calls[receiver_id] = caller_id

        caller_name = "Anonymous caller" if anonymous else interaction.author.display_name

        await member.send(
            f"📞 **Incoming Call**\n{caller_name} is calling you! Type `!answer` to connect or `!decline` to reject.")
        await interaction.response.send_message(f"📞 **Dialing...**\nCalling {member.display_name}. Please wait for them to answer.")

    @nextcord.slash_command(name="answer", description="Answer the phone silly!")
    async def answer(self, interaction):
        """Answer a call."""
        receiver_id = interaction.author.id
        if receiver_id not in self.active_calls:
            await interaction.response.send_message(f"❌ {interaction.author.mention} **No one is calling you right now.**")
            return

        caller_id = self.active_calls[receiver_id]
        caller = self.bot.get_user(caller_id)

        await interaction.response.send_message(f"✅ **Call Connected!**\nYou are now chatting with {caller.display_name}.")
        await caller.send(f"✅ **Call Connected!**\n{interaction.author.display_name} has answered your call.")

    @nextcord.slash_command(name="decline", description="Reject caller")
    async def decline(self, interaction):
        """Decline an incoming call."""
        receiver_id = interaction.author.id
        if receiver_id not in self.active_calls:
            await interaction.response.send_message(f"❌ {interaction.author.mention} **No one is calling you right now.**")
            return

        caller_id = self.active_calls[receiver_id]
        caller = self.bot.get_user(caller_id)

        await interaction.response.send_message(f"📞 **Call Declined**\nYou declined the call.")
        await caller.send(f"📞 **Call Declined**\n{interaction.author.display_name} declined your call.")

        del self.active_calls[receiver_id]
        del self.active_calls[caller_id]

    @nextcord.slash_command(name="hangup", description="Ends call.")
    async def hangup(self, interaction):
        user_id = interaction.author.id
        if user_id not in self.active_calls:
            await interaction.response.send_message(f"⚠️ {interaction.author.mention} **You're not in a call!**")
            return

        partner_id = self.active_calls[user_id]
        partner = self.bot.get_user(partner_id)

        await interaction.response.send_message("❌ **Call Ended**\nYou have ended the call.")
        await partner.send(f"❌ **Call Ended**\n{interaction.author.display_name} has ended the call.")

        del self.active_calls[user_id]
        del self.active_calls[partner_id]

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for messages and filter call content."""
        if message.author.bot:
            return

        if message.author.id in self.active_calls:
            if isinstance(message.channel, nextcord.DMChannel):
                interaction = await self.bot.get_context(message)
                if interaction.valid:
                    return

                partner_id = self.active_calls[message.author.id]
                partner = self.bot.get_user(partner_id)

                filtered_content = self.filter_message(message.content)

                # Forward the message
                await partner.send(f"💬 **{message.author.display_name}**: {filtered_content}")

    @nextcord.slash_command(name="reportcall", description="Report caller")
    async def reportcaller(self, interaction, member: nextcord.Member, *, reason="No reason provided."):
        """Report a user for abusing the call system."""
        report_channel_id = 123546864356

        if not report_channel_id:
            await interaction.response.send_message("⚠️ Report functionality is currently unavailable. Please contact a server admin directly.")
            return

        report_channel = self.bot.get_channel(report_channel_id)
        if not report_channel:
            await interaction.response.send_message("⚠️ Report channel not found. Please contact a server admin directly.")
            return

        await report_channel.send(
            f"🚨 **User Report**\n**Reporter:** {interaction.author.display_name} ({interaction.author.id})\n**Reported:** {member.display_name} ({member.id})\n**Reason:** {reason}")
        await interaction.response.send_message(f"📩 {interaction.author.mention} **Your report has been submitted to the moderators!**")


def setup(bot):
    bot.add_cog(PhoneCall(bot))
