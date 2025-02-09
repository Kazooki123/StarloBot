import nextcord
from nextcord.ext import commands


class StopMusic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(
        name='stop', 
        description="Stops the music and clears queue.",
        guild_ids=[1237746712291049483]    
    )
    async def stop(self, interaction: nextcord.Interaction):
        
        voice_client = interaction.message.guild.voice_client
        if voice_client.is_playing():
            voice_client.stop()
            await interaction.response.send_message('Music stopped')
        else:
            await interaction.response.send_message('No music is playing at the moment.')
            
            
def setup(bot):
    bot.add_cog(StopMusic(bot))
