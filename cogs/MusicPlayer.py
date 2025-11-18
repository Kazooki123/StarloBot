import os
import re
import logging
import nextcord
from nextcord.ext import commands
import lavalink
from dotenv import load_dotenv

load_dotenv('../.env')

logging.getLogger('lavalink').setLevel(logging.INFO)

URL_REGEX = re.compile(r'https?://(?:www\.)?.+')


class LavalinkVoiceClient(nextcord.VoiceClient):
    """
    Custom Voice Client implementation for Lavalink
    """
    def __init__(self, client: nextcord.Client, channel: nextcord.VoiceChannel):
        self.client = client
        self.channel = channel
        self.guild = channel.guild if channel else None
        super().__init__(client, channel)

    async def on_voice_server_update(self, data):
        lavalink_client = self.client.lavalink
        await lavalink_client._dispatch_voice_server_update(self.guild.id, data)

    async def on_voice_state_update(self, data):
        lavalink_client = self.client.lavalink
        await lavalink_client._dispatch_voice_state_update(self.guild.id, data)

    async def connect(self, *, timeout: float, reconnect: bool, self_deaf: bool = False, self_mute: bool = False) -> None:
        await self.guild.change_voice_state(channel=self.channel, self_deaf=self_deaf, self_mute=self_mute)
        self._connected = True

    async def disconnect(self, *, force: bool = False) -> None:
        if not force and not self.is_connected():
            return
        await self.guild.change_voice_state(channel=None)
        self._connected = False


class LavalinkClient(lavalink.Client):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot.user.id)
        self.bot = bot
        self.bot.lavalink = self

        # Register custom voice client implementation
        if not hasattr(bot, '_get_voice_client'):
            self.bot._get_voice_client = self.get_voice_client

    def get_voice_client(self, guild_id: int):
        """Get or create a LavalinkVoiceClient"""
        return self.bot.get_guild(guild_id).voice_client

    async def connect(self, guild_id: int, channel_id: int):
        ws = self.bot._connection._get_websocket(guild_id)
        await ws.voice_state(str(guild_id), str(channel_id))


class MusicPlayer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        if not hasattr(bot, 'lavalink'):
            self.bot.lavalink = LavalinkClient(bot)
            
            # Initialize node
            self.bot.lavalink.add_node(
                host=os.getenv('LAVALINK_HOST'),
                port=int(os.getenv('LAVALINK_PORT')),
                password=os.getenv('LAVALINK_PASSWORD'),
                region=os.getenv('LAVALINK_REGION'),
                identifier=os.getenv('LAVALINK_NAME', 'Main Node')
            )

    async def ensure_voice(self, interaction: nextcord.Interaction):
        """Ensure the bot and command author are in a voice channel"""
        player = self.bot.lavalink.player_manager.create(interaction.guild.id)
        
        if not interaction.author.voice or not interaction.author.voice.channel:
            await interaction.response.send_message("Please join a voice channel first!")
            return False
            
        if not player.is_connected:
            permissions = interaction.author.voice.channel.permissions_for(interaction.guild.me)
            if not permissions.connect or not permissions.speak:
                await interaction.response.send_message("I need permissions to join and speak in your voice channel!")
                return False
                
            await self.bot.lavalink.connect(interaction.guild.id, interaction.author.voice.channel.id)
            player.store('channel', interaction.channel.id)
        else:
            if int(player.channel_id) != interaction.author.voice.channel.id:
                await interaction.response.send_message("You need to be in my voice channel to use this command!")
                return False
        
        return True

    @nextcord.slash_command(name='play', aliases=['p'], description='Play a song')
    async def play(self, interaction: nextcord.Interaction, *, query: str):
        """Play a song from a given query or URL"""
        if not await self.ensure_voice(interaction):
            return
            
        player = self.bot.lavalink.player_manager.get(interaction.guild.id)
        query = query.strip('<>')

        if not URL_REGEX.match(query):
            query = f'ytsearch:{query}'

        results = await player.node.get_tracks(query)
        
        if not results or not results.tracks:
            return await interaction.response.send_message('Nothing found!')

        if results.load_type == 'PLAYLIST_LOADED':
            tracks = results.tracks
            for track in tracks:
                player.add(requester=interaction.author.id, track=track)
            
            await interaction.response.send_message(f'Added {len(tracks)} tracks from playlist {results.playlist_info.name}')
        else:
            track = results.tracks[0]
            player.add(requester=interaction.author.id, track=track)
            await interaction.response.send_message(f'Added **{track.title}** to the queue')

        if not player.is_playing:
            await player.play()

    @nextcord.slash_command(name='stop', aliases=['stp'], description='Stop the song from playing.')
    async def stop(self, interaction: nextcord.Interaction):
        """Stop the player and clear the queue"""
        if not await self.ensure_voice(interaction):
            return
            
        player = self.bot.lavalink.player_manager.get(interaction.guild.id)
        
        player.queue.clear()
        await player.stop()
        await self.bot.lavalink.connect(interaction.guild.id, None)  # Disconnect from voice
        await interaction.response.send_message('Stopped playing and cleared the queue.')

    @nextcord.slash_command(name='skip', aliases=['s'], description='Skip a song')
    async def skip(self, interaction: nextcord.Interaction):
        """Skip the current song"""
        if not await self.ensure_voice(interaction):
            return
            
        player = self.bot.lavalink.player_manager.get(interaction.guild.id)
        
        if not player.is_playing:
            return await interaction.response.send_message('Nothing is playing!')
            
        await player.skip()
        await interaction.response.send_message('Skipped the current track.')

    @nextcord.slash_command(name='queue', aliases=['q'], description='Displays the current Queue.')
    async def queue(self, interaction: nextcord.Interaction):
        """Show the current queue"""
        if not await self.ensure_voice(interaction):
            return
            
        player = self.bot.lavalink.player_manager.get(interaction.guild.id)
        
        if not player.queue:
            return await interaction.response.send_message('Nothing is queued!')
            
        queue_list = []
        for i, track in enumerate(player.queue, start=1):
            queue_list.append(f'**{i}.** {track.title}')
            
        # Split into chunks if queue is too long
        queue_chunks = [queue_list[i:i + 10] for i in range(0, len(queue_list), 10)]
        current_page = 1
        
        for chunk in queue_chunks:
            embed = nextcord.Embed(
                title=f'Queue - Page {current_page}/{len(queue_chunks)}',
                description='\n'.join(chunk),
                color=nextcord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)
            current_page += 1

    @nextcord.slash_command(name='pause', aliases=['pse'], description='Pause the current song.')
    async def pause(self, interaction: nextcord.Interaction):
        """Pause the current track"""
        if not await self.ensure_voice(interaction):
            return
            
        player = self.bot.lavalink.player_manager.get(interaction.guild.id)
        
        if not player.is_playing:
            return await interaction.response.send_message('Nothing is playing!')
            
        if player.paused:
            return await interaction.response.send_message('The player is already paused!')
            
        await player.set_pause(True)
        await interaction.response.send_message('Paused the player.')

    @nextcord.slash_command(name='resume', aliases=['rsm'], description='Resume the current song.')
    async def resume(self, interaction: nextcord.Interaction):
        """Resume the current track"""
        if not await self.ensure_voice(interaction):
            return
            
        player = self.bot.lavalink.player_manager.get(interaction.guild.id)
        
        if not player.is_playing:
            return await interaction.response.send_message('Nothing is playing!')
            
        if not player.paused:
            return await interaction.response.send_message('The player is not paused!')
            
        await player.set_pause(False)
        await interaction.response.send_message('Resumed the player.')

    @nextcord.slash_command(name='volume', aliases=['vol'], description='Adjust the volume.')
    async def volume(self, interaction: nextcord.Interaction, volume: int = None):
        """Set the player volume (0-100)"""
        if not await self.ensure_voice(interaction):
            return
            
        player = self.bot.lavalink.player_manager.get(interaction.guild.id)
        
        if volume is None:
            return await interaction.response.send_message(f'Current volume: {player.volume}%')
            
        if not 0 <= volume <= 100:
            return await interaction.response.send_message('Volume must be between 0 and 100!')
            
        await player.set_volume(volume)
        await interaction.response.send_message(f'Set volume to {volume}%')


def setup(bot: commands.Bot):
    bot.add_cog(MusicPlayer(bot))
    