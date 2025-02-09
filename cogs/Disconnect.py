import nextcord
from nextcord.ext import commands


class Disconnect(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(
        name='disconnect',
        description="Disconnects the bot from a voice channel.",
        guild_ids=[1237746712291049483]    
    )
    async def disconnect(self, interaction: nextcord.Interaction):

        voice_client = interaction.message.guild.voice_client
        if voice_client.is_connected():
            await voice_client.disconnect()
            await interaction.response.send_message('Disconnected from the voice channel.')
        else:
            await interaction.response.send_message('The bot is not connected to any voice channels.') 
            
def setup(bot):
    bot.add_cog(Disconnect(bot))