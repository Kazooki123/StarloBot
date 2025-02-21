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

    async def ensure_voice(self, ctx: commands.Context):
        """Ensure the bot and command author are in a voice channel"""
        player = self.bot.lavalink.player_manager.create(ctx.guild.id)
        
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("Please join a voice channel first!")
            return False
            
        if not player.is_connected:
            permissions = ctx.author.voice.channel.permissions_for(ctx.guild.me)
            if not permissions.connect or not permissions.speak:
                await ctx.send("I need permissions to join and speak in your voice channel!")
                return False
                
            await self.bot.lavalink.connect(ctx.guild.id, ctx.author.voice.channel.id)
            player.store('channel', ctx.channel.id)
        else:
            if int(player.channel_id) != ctx.author.voice.channel.id:
                await ctx.send("You need to be in my voice channel to use this command!")
                return False
        
        return True

    @commands.command(name='play', aliases=['p'])
    async def play(self, ctx: commands.Context, *, query: str):
        """Play a song from a given query or URL"""
        if not await self.ensure_voice(ctx):
            return
            
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        query = query.strip('<>')

        if not URL_REGEX.match(query):
            query = f'ytsearch:{query}'

        results = await player.node.get_tracks(query)
        
        if not results or not results.tracks:
            return await ctx.send('Nothing found!')

        if results.load_type == 'PLAYLIST_LOADED':
            tracks = results.tracks
            for track in tracks:
                player.add(requester=ctx.author.id, track=track)
            
            await ctx.send(f'Added {len(tracks)} tracks from playlist {results.playlist_info.name}')
        else:
            track = results.tracks[0]
            player.add(requester=ctx.author.id, track=track)
            await ctx.send(f'Added **{track.title}** to the queue')

        if not player.is_playing:
            await player.play()

    @commands.command(name='stop')
    async def stop(self, ctx: commands.Context):
        """Stop the player and clear the queue"""
        if not await self.ensure_voice(ctx):
            return
            
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        player.queue.clear()
        await player.stop()
        await self.bot.lavalink.connect(ctx.guild.id, None)  # Disconnect from voice
        await ctx.send('Stopped playing and cleared the queue.')

    @commands.command(name='skip', aliases=['s'])
    async def skip(self, ctx: commands.Context):
        """Skip the current song"""
        if not await self.ensure_voice(ctx):
            return
            
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if not player.is_playing:
            return await ctx.send('Nothing is playing!')
            
        await player.skip()
        await ctx.send('Skipped the current track.')

    @commands.command(name='queue', aliases=['q'])
    async def queue(self, ctx: commands.Context):
        """Show the current queue"""
        if not await self.ensure_voice(ctx):
            return
            
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if not player.queue:
            return await ctx.send('Nothing is queued!')
            
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
            await ctx.send(embed=embed)
            current_page += 1

    @commands.command(name='pause')
    async def pause(self, ctx: commands.Context):
        """Pause the current track"""
        if not await self.ensure_voice(ctx):
            return
            
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if not player.is_playing:
            return await ctx.send('Nothing is playing!')
            
        if player.paused:
            return await ctx.send('The player is already paused!')
            
        await player.set_pause(True)
        await ctx.send('Paused the player.')

    @commands.command(name='resume')
    async def resume(self, ctx: commands.Context):
        """Resume the current track"""
        if not await self.ensure_voice(ctx):
            return
            
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if not player.is_playing:
            return await ctx.send('Nothing is playing!')
            
        if not player.paused:
            return await ctx.send('The player is not paused!')
            
        await player.set_pause(False)
        await ctx.send('Resumed the player.')

    @commands.command(name='volume', aliases=['vol'])
    async def volume(self, ctx: commands.Context, volume: int = None):
        """Set the player volume (0-100)"""
        if not await self.ensure_voice(ctx):
            return
            
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if volume is None:
            return await ctx.send(f'Current volume: {player.volume}%')
            
        if not 0 <= volume <= 100:
            return await ctx.send('Volume must be between 0 and 100!')
            
        await player.set_volume(volume)
        await ctx.send(f'Set volume to {volume}%')


def setup(bot: commands.Bot):
    bot.add_cog(MusicPlayer(bot))
    