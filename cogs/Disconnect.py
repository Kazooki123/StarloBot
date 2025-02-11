import nextcord
from nextcord.ext import commands


class Disconnect(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(
        name='disconnect'  
    )
    async def disconnect(self, ctx):

        voice_client = ctx.message.guild.voice_client
        if voice_client.is_connected():
            await voice_client.disconnect()
            await ctx.send('Disconnected from the voice channel.')
        else:
            await ctx.send('The bot is not connected to any voice channels.') 
            
def setup(bot):
    bot.add_cog(Disconnect(bot))