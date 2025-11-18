import nextcord
from nextcord.ext import commands
from nextcord.ui import View, Button

async def get_mod_channel_id(self, guild_id: int) -> int:
    async with self.bot.db_handler.pg_pool.acquire() as conn:
        record = await conn.fetchrow(
            "SELECT mod_channel_id FROM guild_settings WHERE guild_id = $1",
            guild_id
        )
    return record['mod_channel_id'] if record else None

class BanAppeal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(name="appeal", description="Send an appeal after a ban.")
    async def appeal(self, interaction: nextcord.Interaction, *, reason: str):
        """
        Allows banned users to submit a ban appeal. Only works in DMs.
        """
        if interaction.guild:
            await interaction.response.send_message("⚠️ Please send this command in **DMs** to appeal your ban.")
            return
        
        guild = self.bot.get_guild()
        if not guild:
            await interaction.response.send_message("❌ Error: The bot is not connected to the server.")
            return
        
        try:
            ban_entry = await guild.fetch_ban(interaction.author)
        except nextcord.NotFound:
            await interaction.response.send_message("⚠️ You are **not banned from this server!**")
            return
        
        mod_channel_id = await self.get_mod_channel_id(guild.id)
        if not mod_channel_id:
            await interaction.response.send_message("❌ Error: No moderation channel has been set up!")
            return
            
        mod_channel = self.bot.get_channel(mod_channel_id)
        if mod_channel:
            embed = nextcord.Embed(
                title="Ban Appeal Submitted",
                description=f"**User:** {interaction.author} ({interaction.author.id})\n**Reason:** {reason}",
                color=nextcord.Color.red()
            )
            
            view = AppealView(interaction.author.id, guild.id)
            await mod_channel.send(embed=embed, view=view)
            await interaction.response.send_message("✅ Your `appeal` has been **submitted to the moderators!**")
        else:
            await interaction.response.send_message("❌ Error: Could not find the **mod** channel.")


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
