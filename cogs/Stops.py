import nextcord
from nextcord.ext import commands


class StopMusic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(name='stop', description="Stops the music and clears queue.")
    async def stop(self, ctx: nextcord.Interaction):
        
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_playing():
            voice_client.stop()
            await ctx.send('Music stopped')
        else:
            await ctx.send('No music is playing at the moment.')
            
            
def setup(bot):
    bot.add_cog(StopMusic(bot))
