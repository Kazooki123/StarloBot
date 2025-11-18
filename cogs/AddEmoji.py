import nextcord
import aiohttp
from nextcord.ext import commands


class AddEmoji(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(name="addemoji")
    @commands.has_permissions(manage_emojis=True)
    async def addemoji(self, interaction: nextcord.Interaction, name: str, url: str):
        """
        Adds a custom emoji.
        Usage: !addemoji <emoji_name> <image_url>
        Example: !addemoji uwu https://image.uwu
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        emoji = await interaction.guild.create_custom_emoji(name=name, image=image_data)
                        await interaction.response.send_message(f"**📦 Added emoji:** {emoji}")
                    else:
                        await interaction.response.send_message("❌ Failed to download the image or it's too big.")
        except Exception as e:
            await interaction.response.send_message(f"⚠️ **Error:** {e}")


def setup(bot):
    bot.add_cog(AddEmoji(bot))

