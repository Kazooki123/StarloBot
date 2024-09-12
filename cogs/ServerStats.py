import nextcord
from nextcord.ext import commands


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(description="Shows the servers stats!")
    async def serverstats(self, ctx: nextcord.Interaction):
        guild = ctx.guild
    
        embed = nextcord.Embed(title="Server Statistics:", color=nextcord.Color.green())
    
        embed.set_thumbnail(url=guild.icon.url)
    
        embed.add_field(name="Server Name:", value=guild.name, inline=True)
        embed.add_field(name="Server ID:", value=guild.id, inline=True)
        embed.add_field(name="Owner:", value=guild.owner.name if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Member Count:", value=guild.member_count, inline=True)
        embed.add_field(name="Creation Date:", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
    
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Stats(bot))
