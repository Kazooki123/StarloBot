import os

import nextcord
from nextcord.ext import commands
from pytube import YouTube


class ConvertLinks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="link2image", help="Convert a image link into an actual image you can save!")
    async def link_to_image(self, ctx, link: str):
        try:
            embed = nextcord.Embed(title="Image", description="Here is the image from the provided link:")
            embed.set_image(url=link)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Invalid image link provided: {e}")

    @commands.command(name="link2video", help="Convert a Youtube video url into a actual file video!")
    async def link_to_video(self, ctx, link: str):
        try:
            youtube = YouTube(link)
            video = youtube.streams.get_highest_resolution()
            video_path = video.download()

            await ctx.send(f"📽️ {ctx.author.mention} **Here is your Video! :3**")
            await ctx.send(file=nextcord.File(video_path))
            os.remove(video_path)
        except Exception as e:
            await ctx.send(f"An error occurred while processing the video: {e}")


def setup(bot):
    bot.add_cog(ConvertLinks(bot))
