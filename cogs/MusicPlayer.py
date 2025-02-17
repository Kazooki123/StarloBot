import nextcord
from nextcord.ext import commands
import yt_dlp as youtube_dl
from collections import deque
import asyncio
from async_timeout import timeout
import functools
from typing import Optional

youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn',
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(nextcord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')

    @classmethod
    async def from_url(cls, url, *, loop=None):
        loop = loop or asyncio.get_running_loop()
        
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
            
            if 'entries' in data:
                data = data['entries'][0]

            return cls(nextcord.FFmpegPCMAudio(data['url'], **ffmpeg_options), data=data)
        except Exception as e:
            print(f"Error in from_url: {e}")
            raise e


class MusicPlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.current_players = {}

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = deque()
        return self.queues[guild_id]

    async def ensure_voice_connection(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                try:
                    return await ctx.author.voice.channel.connect()
                except Exception as e:
                    print(f"Connection error: {e}")
                    await ctx.send(f"❌ Failed to connect to voice channel: {str(e)}")
                    return None
            else:
                await ctx.send("❌ You are not connected to a voice channel.")
                return None
        return ctx.voice_client

    async def play_next(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        if not queue:
            return
            
        try:
            url = queue.popleft()
            async with ctx.typing():
                player = await YTDLSource.from_url(url, loop=self._loop)
                
                def after_callback(error):
                    if error:
                        print(f'Player error: {error}')
                    future = asyncio.run_coroutine_threadsafe(self.play_next(ctx), self._loop)
                    try:
                        future.result()
                    except Exception as e:
                        print(f'Error in play_next callback: {e}')

                ctx.voice_client.play(player, after=after_callback)
                self.current_players[ctx.guild.id] = player
                await ctx.send(f'🎵 Now playing: **{player.title}**')
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')
            await self.play_next(ctx)

    @commands.command(name="play")
    async def play(self, ctx, *, url):
        """Play a song from YouTube."""
        vc = await self.ensure_voice_connection(ctx)
        if not vc:
            return
        
        async with ctx.typing():
            try:
                queue = self.get_queue(ctx.guild.id)
                queue.append(url)
                
                if not ctx.voice_client.is_playing():
                    await self.play_next(ctx)
                else:
                    # Try to get the title before adding to queue
                    data = await self._loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
                    title = data.get('title', url) if 'entries' not in data else data['entries'][0].get('title', url)
                    await ctx.send(f'✅ Added to queue: **{title}**')
            except Exception as e:
                await ctx.send(f'An error occurred: {str(e)}')

    @commands.command(name="skip")
    async def skip(self, ctx):
        """Skip the current song."""
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.send("❌ Nothing is playing right now.")
        
        ctx.voice_client.stop()
        await ctx.send("⏭️ Skipped the current song.")

    @commands.command(name="stop")
    async def stop(self, ctx):
        """Stop playing and clear the queue."""
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.send("❌ Nothing is playing right now.")
        
        queue = self.get_queue(ctx.guild.id)
        queue.clear()
        ctx.voice_client.stop()
        await ctx.send("⏹️ Playback stopped and queue cleared.")

    @commands.command(name="queue", aliases=["q"])
    async def queue_info(self, ctx):
        """Display the current queue."""
        queue = self.get_queue(ctx.guild.id)
        
        if not queue:
            return await ctx.send("📭 The queue is empty.")
        
        current = self.current_players.get(ctx.guild.id)
        
        embed = nextcord.Embed(title="Music Queue", color=nextcord.Color.blue())
        if current:
            embed.add_field(name="Now Playing", value=current.title, inline=False)
        
        # Get titles for queued songs
        queue_list = []
        for i, url in enumerate(queue):
            try:
                data = await self._loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
                title = data.get('title', url) if 'entries' not in data else data['entries'][0].get('title', url)
                queue_list.append(f"{i+1}. {title}")
            except:
                queue_list.append(f"{i+1}. {url}")
        
        if queue_list:
            embed.add_field(name="Queue", value="\n".join(queue_list), inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="disconnect", aliases=["leave"])
    async def disconnect(self, ctx):
        """Disconnect the bot from voice channel."""
        if not ctx.voice_client:
            return await ctx.send("❌ I'm not connected to any voice channel.")
        
        await ctx.voice_client.disconnect()
        if ctx.guild.id in self.queues:
            self.queues[ctx.guild.id].clear()
        await ctx.send("👋 Disconnected from voice channel.")

def setup(bot):
    bot.add_cog(MusicPlayer(bot))