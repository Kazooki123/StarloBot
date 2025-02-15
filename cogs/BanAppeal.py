import nextcord
from nextcord.ext import commands
from nextcord.ui import View, Button

MOD_CHANNEL_ID = 1338726351326150687

class BanAppeal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="appeal")
    async def appeal(self, ctx, *, reason: str):
        """
        Allows banned users to submit a ban appeal. Only works in DMs.
        """
        if ctx.guild:
            await ctx.send("⚠️ Please send this command in **DMs** to appeal your ban.")
            return
        
        guild = self.bot.get_guild(1237746712291049483)
        if not guild:
            await ctx.send("❌ Error: The bot is not connected to the server.")
            return
        
        try:
            ban_entry = await guild.fetch_ban(ctx.author)
        except nextcord.NotFound:
            await ctx.send("⚠️ You are **not banned from this server!**")
            return
        
        mod_channel = self.bot.get_channel(MOD_CHANNEL_ID)
        if mod_channel:
            embed = nextcord.Embed(
                title="Ban Appeal Submitted",
                description=f"**User:** {ctx.author} ({ctx.author.id})\n**Reason:** {reason}",
                color=nextcord.Color.red()
            )
            
            view = AppealView(ctx.author.id, guild.id)
            await mod_channel.send(embed=embed, view=view)
            await ctx.send("✅ Your `appeal` has been **submitted to the moderators!**")
        else:
            await ctx.send("❌ Error: Could not find the **mod** channel.")
            
class AppealView(View):
    def __init__(self, user_id, guild_id):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.guild_id = guild_id
        
    @nextcord.ui.button(label="Approve", style=nextcord.ButtonStyle.green)
    async def approve(self, button: Button, interaction: nextcord.Interaction):
        """
        Unban the user when approved.
        """
        guild = self.bot.get_guild(self.guild_id)
        if guild:
            try:
                await guild.unban(nextcord.Object(id=self.user_id))
                await interaction.response.send_message(f"✅ Unbanned <@{self.user_id}>", ephemeral=False)
            except Exception as e:
                await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
                
    @nextcord.ui.button(label="Reject", style=nextcord.ButtonStyle.red)
    async def reject(self, button: Button, interaction: nextcord.Interaction):
        """
        Rejects the appeal.
        """
        await interaction.response.send_message(f"❌ Appeal from <@{self.user_id}> rejected.", ephemeral=False)
        
def setup(bot):
    bot.add_cog(BanAppeal(bot))