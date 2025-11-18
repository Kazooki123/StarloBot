import nextcord
from nextcord.ext import commands
import re
import json
import os

BADWORDS_JSON = os.path.join(os.path.dirname(__file__), '..', 'json', 'badwords.json')


class SendDM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

    @nextcord.slash_command(name="dm")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def dm(self, interaction, member: nextcord.Member, *, message: str):
        anonymous = False
        if " | anonymous" in message.lower():
            anonymous = True
            message = message.lower().replace(" | anonymous", "")

        # Prevent self-DMs
        if interaction.author.id == member.id:
            await interaction.response.send_message("❌ **Error:** You can't send DMs to yourself!")
            return

        filtered_message = self.filter_message(message)

        try:
            if anonymous:
                await member.send(f"📩 **Anonymous Message**\n{filtered_message}")
                sender_feedback = "anonymously"
            else:
                await member.send(f"📩 **Message from {interaction.author.display_name}**\n{filtered_message}")
                sender_feedback = "with your name visible"

            if filtered_message != message:
                await interaction.response.send_message(f"✅ **Message sent {sender_feedback}!** (Some content was spoiler-tagged)")
            else:
                await interaction.response.send_message(f"✅ **Message sent {sender_feedback}!**")

            try:
                await interaction.message.delete()
            except:
                pass

        except nextcord.Forbidden:
            await interaction.response.send_message("❌ **Cannot send DM.** User may have DMs disabled or blocked the bot.")

    @nextcord.slash_command(name="reply")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def reply(self, interaction, *, message: str):
        if not isinstance(interaction.channel, nextcord.DMChannel):
            await interaction.response.send_message(f"❌ {interaction.author.mention} **This command can only be used in DMs with the bot!**")
            return

        anonymous = False
        if " | anonymous" in message.lower():
            anonymous = True
            message = message.lower().replace(" | anonymous", "")

        filtered_message = self.filter_message(message)

        await interaction.response.send_message("⚠️ The reply feature is still in development.")


def setup(bot):
    bot.add_cog(SendDM(bot))
