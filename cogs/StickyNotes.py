import nextcord
from nextcord.ext import commands
import json
import os


class StickyNotes(commands.Cog):
    """Manages sticky messages that stay at the bottom of channels"""
    
    def __init__(self, bot):
        self.bot = bot
        self.sticky_data_file = "../json/sticky_messages.json"
        self.sticky_messages = {}  # {channel_id: {'message': content, 'last_id': message_id}}
        self.load_sticky_messages()
        
    def load_sticky_messages(self):
        os.makedirs(os.path.dirname(self.sticky_data_file), exist_ok=True)
        try:
            if os.path.exists(self.sticky_data_file):
                with open(self.sticky_data_file, 'r') as f:
                    self.sticky_messages = json.load(f)
        except Exception as e:
            print(f"Error loading sticky messages: {e}")
            self.sticky_messages = {}
            
    def save_sticky_messages(self):
        try:
            os.makedirs(os.path.dirname(self.sticky_data_file), exist_ok=True)
            with open(self.sticky_data_file, 'w') as f:
                json.dump(self.sticky_messages, f, indent=4)
        except Exception as e:
            print(f"Error saving sticky messages: {e}")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
            
        channel_id = str(message.channel.id)
        
        if channel_id in self.sticky_messages:
            try:
                last_message_id = self.sticky_messages[channel_id].get('last_id')
                if last_message_id:
                    try:
                        old_message = await message.channel.fetch_message(int(last_message_id))
                        await old_message.delete()
                    except (nextcord.NotFound, nextcord.HTTPException):
                        pass
            except Exception as e:
                print(f"Error deleting previous sticky message: {e}")

            try:
                sticky_content = self.sticky_messages[channel_id]['message']
                embed = nextcord.Embed(
                    description=sticky_content,
                    color=0x00FF00
                )
                embed.set_footer(text="📌 Sticky Message")
                
                new_sticky = await message.channel.send(embed=embed)
                
                self.sticky_messages[channel_id]['last_id'] = str(new_sticky.id)
                self.save_sticky_messages()
                
            except Exception as e:
                print(f"Error sending new sticky message: {e}")
    
    @commands.group(name="sticknote", invoke_without_command=True)
    async def stick(self, interaction):
        await interaction.response.send_message("Available commands: `set`, `remove`, `list`, `edit`")
    
    @stick.command(name="set")
    @commands.has_permissions(manage_messages=True)
    async def set_sticky(self, interaction, *, message: str):
        channel_id = str(interaction.channel.id)
        
        self.sticky_messages[channel_id] = {
            'message': message,
            'last_id': None
        }
        
        self.save_sticky_messages()
        
        embed = nextcord.Embed(
            title="Sticky Message Set",
            description=message,
            color=0x00FF00
        )
        embed.set_footer(text="📌 Sticky Message")
        
        sticky_msg = await interaction.response.send_message(embed=embed)
        self.sticky_messages[channel_id]['last_id'] = str(sticky_msg.id)
        self.save_sticky_messages()
        
        await interaction.message.delete()
    
    @stick.command(name="remove")
    @commands.has_permissions(manage_messages=True)
    async def remove_sticky(self, interaction):
        """Remove the sticky message from the current channel"""
        channel_id = str(interaction.channel.id)
        
        if channel_id not in self.sticky_messages:
            await interaction.response.send_message("There is no sticky message in this channel.")
            return

        try:
            last_id = self.sticky_messages[channel_id].get('last_id')
            if last_id:
                try:
                    last_message = await interaction.channel.fetch_message(int(last_id))
                    await last_message.delete()
                except (nextcord.NotFound, nextcord.HTTPException):
                    pass
        except Exception as e:
            print(f"Error removing sticky message: {e}")
            
        del self.sticky_messages[channel_id]
        self.save_sticky_messages()
        
        await interaction.response.send_message("Sticky message removed from this channel.", delete_after=5)
        await interaction.message.delete()
        
    @stick.command(name="list")
    @commands.has_permissions(manage_messages=True)
    async def list_sticky(self, interaction):
        if not self.sticky_messages:
            await interaction.response.send_message("There are no sticky messages set.")
            return
            
        embed = nextcord.Embed(
            title="Active Sticky Messages",
            color=0x00FF00
        )
        
        for channel_id, data in self.sticky_messages.items():
            try:
                channel = self.bot.get_channel(int(channel_id))
                channel_name = f"#{channel.name}" if channel else f"Unknown Channel ({channel_id})"
                message_preview = data['message'][:100] + "..." if len(data['message']) > 100 else data['message']
                embed.add_field(name=channel_name, value=message_preview, inline=False)
            except Exception as e:
                print(f"Error listing sticky message: {e}")
                
        await interaction.response.send_message(embed=embed)
    
    @stick.command(name="edit")
    @commands.has_permissions(manage_messages=True)
    async def edit_sticky(self, interaction, *, new_message: str):
        channel_id = str(interaction.channel.id)
        
        if channel_id not in self.sticky_messages:
            await interaction.response.send_message("There is no sticky message in this channel.")
            return
            
        self.sticky_messages[channel_id]['message'] = new_message
        
        try:
            last_id = self.sticky_messages[channel_id].get('last_id')
            if last_id:
                try:
                    last_message = await interaction.channel.fetch_message(int(last_id))
                    await last_message.delete()
                except (nextcord.NotFound, nextcord.HTTPException):
                    pass  # Message was already deleted
        except Exception as e:
            print(f"Error editing sticky message: {e}")

        embed = nextcord.Embed(
            description=new_message,
            color=0x00FF00
        )
        embed.set_footer(text="📌 Sticky Message")
        
        new_sticky = await interaction.response.send_message(embed=embed)
        self.sticky_messages[channel_id]['last_id'] = str(new_sticky.id)
        
        self.save_sticky_messages()
        await interaction.message.delete()


def setup(bot):
    bot.add_cog(StickyNotes(bot))
    