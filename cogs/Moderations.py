import asyncio

import nextcord
from nextcord.ext import commands


class Moderations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.deleted_messages = []

    async def is_admin(ctx):
        return ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild

    @commands.command(name="ban")
    @commands.check(is_admin)
    async def ban(self, ctx, member: nextcord.Member, *, reason="No reason provided"):
        if ctx.author.top_role <= member.top_role:
            return await ctx.send("❌ **You can't ban a member with a higher or equal role!**")

        await member.ban(reason=reason)
        await ctx.send(f"👩🏼‍⚖️ {member.mention} **has been banned!** Reason: **{reason}**")

    @commands.command(name="kick")
    @commands.check(is_admin)
    async def kick(self, ctx, member: nextcord.Member, *, reason="No reason provided"):
        if ctx.author.top_role <= member.top_role:
            return await ctx.send("❌ **You can't ban a member with a higher or equal role!**")

        await member.kick(reason=reason)
        await ctx.send(f"👢 {member.mention} **has been kicked!** Reason: **{reason}**")

    @commands.command(name="warn")
    @commands.check(is_admin)
    async def warn(self, ctx, member: nextcord.Member, *, reason="No reason provided"):
        await ctx.send(f"⚠️ {member.mention} **has been warned!** Reason: **{reason}**")

    @commands.command(name="mute")
    @commands.check(is_admin)
    async def mute(self, ctx, member: nextcord.Member, time: int = 5):
        muted_role = nextcord.utils.get(ctx.guild.roles, name="Muted")

        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, send_messages=False)

        await member.add_roles(muted_role)
        await ctx.send(f"🔇 {member.mention} **has been muted** for **{time}** minutes!")

        await asyncio.sleep(time * 60)
        await member.remove_roles(muted_role)
        await ctx.send(f"🔊 {member.mention} is now **unmuted**.")

    @commands.command(name="editnickname")
    @commands.check(is_admin)
    async def editnickname(self, ctx, member: nextcord.Member, *, new_nickname: str):
        await member.edit(nick=new_nickname)
        await ctx.send(f"✏️ {member.mention}'s Nickname changed to **{new_nickname}**")

    @commands.command(name="channellock")
    @commands.check(is_admin)
    async def channellock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send("🔒 **This channel has been locked!**")

    @commands.command(name="channelunlock")
    @commands.check(is_admin)
    async def channelunlock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send("🔓 **This channel has been unlocked!**")

    @commands.command(name="raidalert")
    @commands.check(is_admin)
    async def raidalert(self, ctx):
        for channel in ctx.guild.channels:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False)
            await ctx.send("🚨 **RAID ALERT!!** All channels are locked. Admins, check logs!")

    @commands.command(name="purge")
    @commands.check(is_admin)
    async def purge(self, ctx, amount: int = 10):
        deleted = await ctx.channel.purge(limit=amount)
        self.deleted_messages.extend(deleted)
        await ctx.send(f"🧹 **Purged {len(deleted)} messages!**", delete_after=5)

    @commands.command(name="restore")
    @commands.check(is_admin)
    async def restore(self, ctx):
        if not self.deleted_messages:
            return await ctx.send("⚠️ **No messages to restore!**")

        await ctx.send("🔁 **Restoring messages...**")
        for msg in reversed(self.deleted_messages):
            embed = nextcord.Embed(
                description=msg.content,
                color=0x00ff00
            )

        embed.set_author(name=msg.author.display_name, icon_url=msg.author.avatar.url)
        await ctx.send(embed=embed)

        self.deleted_messages = []


def setup(bot):
    bot.add_cog(Moderations(bot))
