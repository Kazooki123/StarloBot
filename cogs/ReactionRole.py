import nextcord
from nextcord.ext import commands


class ReactionRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.role_message_id = None
        
    @nextcord.slash_command(name="setreactionrole")
    @commands.has_permissions(manage_roles=True)
    async def setreactionrole(self, interaction: nextcord.Interaction, role: nextcord.Role, emoji: str):
        """
        Sets up a reaction
        Usage: !setreactionrole @role 🍨
        """
        message = await interaction.response.send_message(f"**React with {emoji}** to get the **{role.name} role!**")
        self.role_message_id = message.id
        
        await message.add_reaction(emoji)
        self.bot.reaction_roles[message.id] = {role.id, emoji}
        
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """
        Assigns role when a user reacts.
        """
        if payload.message_id in self.bot.reaction_roles:
            role_id, emoji = self.bot.reaction_roles[payload.message_id]
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(role_id)
            member = guild.get_member(payload.user_id)
            if role and member:
                await member.add_roles(role)
                
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """
        Removes role when a user removes their reaction
        """
        if payload.message_id in self.bot.reaction_roles:
            role_id, emoji = self.bot.reaction_roles[payload.message_id]
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(role_id)
            member = guild.get_member(payload.user_id)
            if role and member:
                await member.remove_roles(role)


def setup(bot):
    bot.reaction_roles = {}
    bot.add_cog(ReactionRole(bot))
