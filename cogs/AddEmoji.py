import aiohttp
from nextcord.ext import commands


class AddEmoji(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="addemoji")
    @commands.has_permissions(manage_emojis=True)
    async def addemoji(self, ctx, name: str, url: str):
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
                        emoji = await ctx.guild.create_custom_emoji(name=name, image=image_data)
                        await ctx.send(f"**📦 Added emoji:** {emoji}")
                    else:
                        await ctx.send("❌ Failed to download the image or it's too big.")
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** {e}")


def setup(bot):
    bot.add_cog(AddEmoji(bot))
