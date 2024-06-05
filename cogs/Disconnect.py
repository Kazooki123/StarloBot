import nextcord
from nextcord.ext import commands

class Disconnect(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(name='disconnect', description="Disconnects the bot from a voice channel.")
    async def disconnect(self, ctx: nextcord.Interaction):

        voice_client = ctx.message.guild.voice_client
        if voice_client.is_connected():
            await voice_client.disconnect()
            await ctx.send('Disconnected from the voice channel.')
        else:
            await ctx.send('The bot is not connected to any voice channels.') 
            
def setup(bot):
    bot.add_cog(Disconnect(bot))