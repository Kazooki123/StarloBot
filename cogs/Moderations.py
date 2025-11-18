import nextcord
from nextcord.ext import commands
import asyncio


class Moderations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.deleted_messages = []

    async def is_admin(interaction):
        return interaction.author.guild_permissions.administrator or interaction.author.guild_permissions.manage_guild
    
    @nextcord.slash_command(name="modsetchannel", description="Set the moderation channel. Only works when the channel is private")
    @commands.check(is_admin)
    async def modsetchannel(self, interaction):
        if not interaction.channel.overwrites_for(interaction.guild.default_role).send_messages is False:
            return await interaction.response.send_message("❌ This command only works in private/mod-only channels!")
            
        async with self.bot.db_handler.pg_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO guild_settings (guild_id, mod_channel_id)
                VALUES ($1, $2)
                ON CONFLICT (guild_id) 
                DO UPDATE SET mod_channel_id = $2
            """, interaction.guild.id, interaction.channel.id)
            
        await interaction.response.send_message(f"✅ Set {interaction.channel.mention} as the moderation channel!")
        
        
    @nextcord.slash_command(name="ban", description="Ban a user.")
    @commands.check(is_admin)
    async def ban(self, interaction, member: nextcord.Member, *, reason="No reason provided"):
        if interaction.author.top_role <= member.top_role:
            return await interaction.response.send_message("❌ **You can't ban a member with a higher or equal role!**")

        await member.ban(reason=reason)
        await interaction.response.send_message(f"👩🏼‍⚖️ {member.mention} **has been banned!** Reason: **{reason}**")

    @nextcord.slash_command(name="kick", description="Kick a user out of the server.")
    @commands.check(is_admin)
    async def kick(self, interaction, member: nextcord.Member, *, reason="No reason provided"):
        if interaction.author.top_role <= member.top_role:
            return await interaction.response.send_message("❌ **You can't ban a member with a higher or equal role!**")

        await member.kick(reason=reason)
        await interaction.response.send_message(f"👢 {member.mention} **has been kicked!** Reason: **{reason}**")

    @nextcord.slash_command(name="warn", description="Warn a user.")
    @commands.check(is_admin)
    async def warn(self, interaction, member: nextcord.Member, *, reason="No reason provided"):
        await interaction.response.send_message(f"⚠️ {member.mention} **has been warned!** Reason: **{reason}**")

    @nextcord.slash_command(name="mute", description="Mute a user.")
    @commands.check(is_admin)
    async def mute(self, interaction, member: nextcord.Member, time: int = 5):
        muted_role = nextcord.utils.get(interaction.guild.roles, name="Muted")

        if not muted_role:
            muted_role = await interaction.guild.create_role(name="Muted")
            for channel in interaction.guild.channels:
                await channel.set_permissions(muted_role, send_messages=False)

        await member.add_roles(muted_role)
        await interaction.response.send_message(f"🔇 {member.mention} **has been muted** for **{time}** minutes!")

        await asyncio.sleep(time * 60)
        await member.remove_roles(muted_role)
        await interaction.response.send_message(f"🔊 {member.mention} is now **unmuted**.")

    @nextcord.slash_command(name="editnickname", description="Edit the nickname of a user.")
    @commands.check(is_admin)
    async def editnickname(self, interaction, member: nextcord.Member, *, new_nickname: str):
        await member.edit(nick=new_nickname)
        await interaction.response.send_message(f"✏️ {member.mention}'s Nickname changed to **{new_nickname}**")

    @nextcord.slash_command(name="channellock", description="Lock a specific channel.")
    @commands.check(is_admin)
    async def channellock(self, interaction):
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        await interaction.response.send_message("🔒 **This channel has been locked!**")

    @nextcord.slash_command(name="channelunlock", description="Unlock a specific channel.")
    @commands.check(is_admin)
    async def channelunlock(self, interaction):
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
        await interaction.response.send_message("🔓 **This channel has been unlocked!**")

    @nextcord.slash_command(name="archive", description="Archive a channel, creates a new category when a channel is archived!")
    @commands.check(is_admin)
    async def archive_channels(self, interaction):
        """
        Archive channels that locked
        Will create an empty category and place it very below
        """

    @nextcord.slash_command(name="raidalert", description="Alert the staff and admin that there's a Raid!")
    @commands.check(is_admin)
    async def raidalert(self, interaction):
        for channel in interaction.guild.channels:
            await channel.set_permissions(interaction.guild.default_role, send_messages=False)
            await interaction.response.send_message("🚨 **RAID ALERT!!** All channels are locked. Admins, check logs!")

    @nextcord.slash_command(name="purge", description="Purge a channel (be cautious)")
    @commands.check(is_admin)
    async def purge(self, interaction: nextcord.Interaction, amount: int = 10):
        deleted = await interaction.channel.purge(limit=amount)
        self.deleted_messages.extend(deleted)
        await interaction.response.send_message(f"🧹 **Purged {len(deleted)} messages!**", delete_after=5)

    @nextcord.slash_command(name="restore", description="Restore member messages after an accident (There are limits)")
    @commands.check(is_admin)
    async def restore(self, interaction: nextcord.Interaction):
        if not self.deleted_messages:
            return await interaction.response.send_message("⚠️ **No messages to restore!**")

        await interaction.response.send_message("🔁 **Restoring messages...**")
        for msg in reversed(self.deleted_messages):
            embed = nextcord.Embed(
                description=msg.content,
                color=0xffffff
            )

        embed.set_author(name=msg.author.display_name, icon_url=msg.author.avatar.url)
        await interaction.response.send_message(embed=embed)

        self.deleted_messages = []


def setup(bot):
    bot.add_cog(Moderations(bot))
