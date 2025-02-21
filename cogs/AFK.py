import datetime

import nextcord
from nextcord.ext import commands


class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_users = {}
        
    @commands.command(name="afk")
    async def afk(self, ctx, *, reason="AFK"):
        """
        Marks a user as AFK with an optional reason.
        Usage: !afk [reason]
        """
        if ctx.author.id in self.afk_users:
            return
            
        self.afk_users[ctx.author.id] = {
            'reason': reason,
            'time': datetime.datetime.utcnow()
        }
    
        embed = nextcord.Embed(
            title="🌙 AFK Status Set",
            description=f"{ctx.author.mention} is now AFK",
            color=nextcord.Color.blue()
        )
        embed.add_field(name="Reason", value=reason)
        
        await ctx.send(embed=embed)
      
        try:
            if ctx.author.guild_permissions.change_nickname:
                original_name = ctx.author.display_name
                if not original_name.startswith("[AFK] "):
                    await ctx.author.edit(nick=f"[AFK] {original_name}")
        except Exception as e:
            print(f"Could not update nickname: {e}")
        
    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Handles AFK-related message events
        """
        if message.author.bot:
            return None
            
        if message.author.id in self.afk_users:
            afk_time = datetime.datetime.utcnow() - self.afk_users[message.author.id]['time']
            minutes = int(afk_time.total_seconds() / 60)
            
            embed = nextcord.Embed(
                title="👋 Welcome Back!",
                description=f"{message.author.mention} is no longer AFK",
                color=nextcord.Color.green()
            )
            embed.add_field(name="Time AFK", value=f"{minutes} minutes")
            
            await message.channel.send(embed=embed)
            
            del self.afk_users[message.author.id]
            
            try:
                if message.author.guild_permissions.change_nickname:
                    current_name = message.author.display_name
                    if current_name.startswith("[AFK] "):
                        await message.author.edit(nick=current_name[6:])
            except Exception as e:
                print(f"Could not update nickname: {e}")
            
        for mention in message.mentions:
            if mention.id in self.afk_users:
                afk_info = self.afk_users[mention.id]
                afk_time = datetime.datetime.utcnow() - afk_info['time']
                minutes = int(afk_time.total_seconds() / 60)
                
                embed = nextcord.Embed(
                    title="⚠️ User is AFK",
                    description=f"{mention.display_name} is currently AFK",
                    color=nextcord.Color.gold()
                )
                embed.add_field(name="Reason", value=afk_info['reason'])
                embed.add_field(name="For", value=f"{minutes} minutes")
                
                await message.channel.send(embed=embed)


def setup(bot):
    return bot.add_cog(AFK(bot))
