import nextcord
from nextcord.ext import commands
from pytube import YouTube
import os

class ConvertLinks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(
        name="link_to_image", 
        description="Converts link to images!",
        guild_ids=[1237746712291049483]
    )
    async def link_to_image(self, interaction: nextcord.Interaction, link: str):
        try:
            embed = nextcord.Embed(title="Image", description="Here is the image from the provided link:")
            embed.set_image(url=link)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message("Invalid image link provided.")

    @nextcord.slash_command(
        name="link_to_video", 
        description="Converts Youtube link to videos!",
        guild_ids=[1237746712291049483]
    )
    async def link_to_video(self, interaction: nextcord.Interaction, link: str):
        try:
            youtube = YouTube(link)
            video = youtube.streams.get_highest_resolution()
            video_path = video.download()
            
            await interaction.response.send_message(file=nextcord.File(video_path))
            os.remove(video_path)  # Clean up downloaded file
        except Exception as e:
            await interaction.response.send_message("An error occurred while processing the video.")
            
def setup(bot):
    bot.add_cog(ConvertLinks(bot))
