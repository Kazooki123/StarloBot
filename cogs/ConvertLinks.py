import nextcord
from nextcord.ext import commands
from pytube import YouTube
import os


class ConvertLinks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="link2image", description="Convert a image link into an actual image you can save!")
    async def link_to_image(self, interaction: nextcord.Interaction, link: str):
        try:
            embed = nextcord.Embed(
                title="Image 📷",
                description="**Here is the image from the provided link:**",
                color=0xffffff
            )
            embed.set_image(url=link)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ {interaction.author.mention} **Invalid image link provided:** {e}")

    @nextcord.slash_command(name="link2video", description="Convert a Youtube video url into a actual file video!")
    async def link_to_video(self, interaction, link: str):
        try:
            youtube = YouTube(link)
            video = youtube.streams.get_highest_resolution()
            video_path = video.download()

            await interaction.response.send_message(
                f"📽️ {interaction.author.mention} **Here is your Video! :3**",
                file=nextcord.File(video_path)
            )

            os.remove(video_path)
        except Exception as e:
            await interaction.response.send_message(f"❌ {interaction.author.mention} **An error occurred while processing the video:** {e}")


def setup(bot):
    bot.add_cog(ConvertLinks(bot))
