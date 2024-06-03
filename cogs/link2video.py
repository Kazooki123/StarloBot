import nextcord
from nextcord.ext import commands
from pytube import YouTube

class Link2Video(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(name="link_to_video", description="Converts Youtube link to videos!")
    async def link_to_video(self, ctx: nextcord.Interaction, link):
        try:
            youtube = YouTube(link)
            video = youtube.streams.get_highest_resolution()
            video.download()
        
            file = nextcord.File(video.default_filename)
            await ctx.send(file=file)
        except Exception as e:
            await ctx.send("An error occurred while processing the video. Please try again later.")
            
def setup(bot):
    bot.add_cog(Link2Video(bot))           