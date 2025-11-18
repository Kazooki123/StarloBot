import nextcord
from nextcord.ext import commands
import asyncio
import aiohttp
import json
import os
import yt_dlp
import datetime
from collections import deque
from dotenv import load_dotenv

load_dotenv('../.env')

SOUNDCLOUD_CLIENT_ID = os.getenv("SOUNDCLOUD_CLIENT_ID")


class SoundCloudPlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
        self.playlists = {}
        self.current_tracks = {}
        self.sc_client_id = SOUNDCLOUD_CLIENT_ID
        self.playlist_storage = {}
        self.is_playing = {}

        self.sc_orange = 0xFF7700
        self.success_green = 0x57F287
        self.error_red = 0xED4245

        if not self.sc_client_id:
            print("WARNING: SOUNDCLOUD_CLIENT_ID environment variable are not set. SoundCloud commands may not work.")

    async def get_sc_track_info(self, query):
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
                'default_search': 'scsearch',
                'source_address': '0.0.0.0',
                'verbose': True,
                'extract_flat': False
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"scsearch: {query}", download=False)
                if 'entries' in info:
                    track = info['entries'][0]
                    return {
                        'url': track['original_url'],
                        'title': track['title'],
                        'thumbnail': track.get('thumbnail'),
                        'uploader': track.get('uploader'),
                        'duration': track.get('duration'),
                        'stream_url': track['url']
                    }
                return None
        except Exception as e:
            print(f"Error getting SoundCloud track info: {e}")
            return None

    def get_voice_client(self, guild_id):
        return self.voice_clients.get(guild_id)

    async def play_next(self, guild_id):
        if not self.playlists.get(guild_id) or len(self.playlists[guild_id]) == 0:
            self.is_playing[guild_id] = False
            return

        track = self.playlists[guild_id].popleft()
        self.current_tracks[guild_id] = track

        voice_client = self.get_voice_client(guild_id)
        if voice_client and voice_client.is_connected():
            self.is_playing[guild_id] = True

            try:
                print(f"Attempting to play URL: {track['stream_url'][:50]}...")

                audio_source = nextcord.FFmpegPCMAudio(
                    track['stream_url'],
                    before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin',
                    options='-vn -threads 4'
                )

                audio = nextcord.PCMVolumeTransformer(audio_source, volume=0.5)

                def after_playing(error):
                    if error:
                        print(f"Error after playing: {error}")
                    asyncio.run_coroutine_threadsafe(self.play_next(guild_id), self.bot.loop)

                voice_client.play(audio, after=after_playing)

                channel = voice_client.channel
                embed = nextcord.Embed(
                    title="Now Playing from SoundCloud",
                    description=f"[{track['title']}]({track['url']})",
                    color=self.sc_orange
                )
                embed.set_thumbnail(
                    url=track['thumbnail'] if track['thumbnail'] else "https://soundcloud.com/favicon.ico")
                embed.add_field(name="Uploader", value=track['uploader'] or "Unknown", inline=True)

                # Format duration
                if track['duration']:
                    duration = str(datetime.timedelta(seconds=track['duration']))
                    embed.add_field(name="Duration", value=duration, inline=True)

                asyncio.run_coroutine_threadsafe(
                    channel.send(embed=embed), self.bot.loop)

            except Exception as e:
                print(f"FFmpeg error: {e}")
                self.is_playing[guild_id] = False

                channel = voice_client.channel
                error_msg = f"Error playing track: {e}"
                asyncio.run_coroutine_threadsafe(
                    channel.send(f"⚠️ {error_msg}"),
                    self.bot.loop
                )
                return

    @nextcord.slash_command(name="playsc", description="Plays Soundcloud from query.")
    async def playsc(self, interaction, *, query):
        if not query:
            embed = nextcord.Embed(
                title="Error",
                description="Please provide a song name to search for",
                color=self.error_red
            )
            return await interaction.response.send_message(embed=embed)

        if not interaction.author.voice:
            embed = nextcord.Embed(
                title="Error",
                description="You need to be in a voice channel to use this command",
                color=self.error_red
            )
            return await interaction.response.send_message(embed=embed)

        searching_embed = nextcord.Embed(
            title="Searching SoundCloud",
            description=f"Looking for: `{query}`",
            color=self.sc_orange
        )
        message = await interaction.response.send_message(embed=searching_embed)

        track = await self.get_sc_track_info(query)
        if not track:
            embed = nextcord.Embed(
                title="Error",
                description=f"Could not find any tracks matching: `{query}`",
                color=self.error_red
            )
            return await message.edit(embed=embed)

        guild_id = interaction.guild.id
        if guild_id not in self.playlists:
            self.playlists[guild_id] = deque()

        self.playlists[guild_id].append(track)
        voice_client = self.get_voice_client(guild_id)
        if not voice_client or not voice_client.is_connected():
            try:
                voice_client = await interaction.author.voice.channel.connect()
                self.voice_clients[guild_id] = voice_client
            except Exception as e:
                embed = nextcord.Embed(
                    title="Error",
                    description=f"Could not connect to voice channel: {str(e)}",
                    color=self.error_red
                )
                return await message.edit(embed=embed)

        if guild_id not in self.is_playing or not self.is_playing[guild_id]:
            await self.play_next(guild_id)
            success_embed = nextcord.Embed(
                title="Added to Queue",
                description=f"Now playing: [{track['title']}]({track['url']})",
                color=self.success_green
            )
        else:
            position = len(self.playlists[guild_id]) + 1
            success_embed = nextcord.Embed(
                title="Added to Queue",
                description=f"[{track['title']}]({track['url']}) (Position: {position})",
                color=self.success_green
            )

        if track['thumbnail']:
            success_embed.set_thumbnail(url=track['thumbnail'])

        await message.edit(embed=success_embed)

    @nextcord.slash_command(name="stopsc")
    async def stopsc(self, interaction):
        guild_id = interaction.guild.id
        voice_client = self.get_voice_client(guild_id)

        if voice_client and voice_client.is_connected():
            if guild_id in self.playlists:
                self.playlists[guild_id].clear()

            if voice_client.is_playing():
                voice_client.stop()

            # Disconnect
            await voice_client.disconnect()
            del self.voice_clients[guild_id]
            self.is_playing[guild_id] = False

            embed = nextcord.Embed(
                title="Disconnected",
                description="Stopped playing and disconnected from voice channel",
                color=self.success_green
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = nextcord.Embed(
                title="Error",
                description="Not currently connected to a voice channel",
                color=self.error_red
            )
            await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="skipsc")
    async def skipsc(self, interaction):
        guild_id = interaction.guild.id
        voice_client = self.get_voice_client(guild_id)

        if voice_client and voice_client.is_playing():
            voice_client.stop()
            embed = nextcord.Embed(
                title="Skipped",
                description="Skipped the current track",
                color=self.success_green
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = nextcord.Embed(
                title="Error",
                description="Nothing is currently playing",
                color=self.error_red
            )
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="pausesc")
    async def pausesc(self, interaction):
        guild_id = interaction.guild.id
        voice_client = self.get_voice_client(guild_id)

        if voice_client and voice_client.is_playing():
            voice_client.pause()
            embed = nextcord.Embed(
                title="Paused",
                description="Paused the current track",
                color=self.success_green
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = nextcord.Embed(
                title="Error",
                description="Nothing is currently playing",
                color=self.error_red
            )
            await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="resumesc")
    async def resumesc(self, interaction):
        guild_id = interaction.guild.id
        voice_client = self.get_voice_client(guild_id)

        if voice_client and voice_client.is_paused():
            voice_client.resume()
            embed = nextcord.Embed(
                title="Resumed",
                description="Resumed the current track",
                color=self.success_green
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = nextcord.Embed(
                title="Error",
                description="Nothing is currently paused",
                color=self.error_red
            )
            await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="queuesc")
    async def queuesc(self, interaction):
        guild_id = interaction.guild.id

        if guild_id not in self.playlists or len(self.playlists[guild_id]) == 0:
            if guild_id not in self.current_tracks:
                embed = nextcord.Embed(
                    title="Queue",
                    description="The queue is empty",
                    color=self.sc_orange
                )
                return await interaction.response.send_message(embed=embed)

        embed = nextcord.Embed(
            title="SoundCloud Queue",
            color=self.sc_orange
        )

        current = self.current_tracks.get(guild_id)
        if current:
            embed.add_field(
                name="Now Playing",
                value=f"[{current['title']}]({current['url']})",
                inline=False
            )

        # Add queued tracks
        if guild_id in self.playlists and len(self.playlists[guild_id]) > 0:
            queue_list = ""
            for i, track in enumerate(self.playlists[guild_id], 1):
                if i <= 10:
                    queue_list += f"{i}. [{track['title']}]({track['url']})\n"

            remaining = len(self.playlists[guild_id]) - 10
            if remaining > 0:
                queue_list += f"\n*And {remaining} more track(s)*"

            embed.add_field(
                name="Up Next",
                value=queue_list or "No tracks in queue",
                inline=False
            )
        else:
            embed.add_field(
                name="Up Next",
                value="No tracks in queue",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="addplaylist")
    async def addplaylist(self, interaction, name, *, query):
        user_id = interaction.author.id

        if user_id not in self.playlist_storage:
            self.playlist_storage[user_id] = {}

        # Initialize playlist if it doesn't exist
        if name not in self.playlist_storage[user_id]:
            self.playlist_storage[user_id][name] = []

        # Search for the track
        track = await self.get_sc_track_info(query)
        if not track:
            embed = nextcord.Embed(
                title="Error",
                description=f"Could not find any tracks matching: `{query}`",
                color=self.error_red
            )
            return await interaction.response.send_message(embed=embed)

        # Add to playlist
        self.playlist_storage[user_id][name].append(track)

        embed = nextcord.Embed(
            title="Added to Playlist",
            description=f"Added [{track['title']}]({track['url']}) to playlist `{name}`",
            color=self.success_green
        )
        if track['thumbnail']:
            embed.set_thumbnail(url=track['thumbnail'])

        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="playlist")
    async def playlist(self, interaction, name=None):
        user_id = interaction.author.id

        if user_id not in self.playlist_storage or not self.playlist_storage[user_id]:
            embed = nextcord.Embed(
                title="Playlists",
                description="You don't have any saved playlists",
                color=self.sc_orange
            )
            return await interaction.response.send_message(embed=embed)

        if not name:
            embed = nextcord.Embed(
                title="Your Playlists",
                color=self.sc_orange
            )

            playlist_list = ""
            for playlist_name, tracks in self.playlist_storage[user_id].items():
                playlist_list += f"**{playlist_name}** - {len(tracks)} track(s)\n"

            embed.description = playlist_list or "You don't have any saved playlists"
            embed.set_footer(text="Use !playlist [name] to view a specific playlist")

            return await interaction.response.send_message(embed=embed)

        # Check if playlist exists
        if name not in self.playlist_storage[user_id]:
            embed = nextcord.Embed(
                title="Error",
                description=f"Playlist `{name}` not found",
                color=self.error_red
            )
            return await interaction.response.send_message(embed=embed)

        # Show playlist
        embed = nextcord.Embed(
            title=f"Playlist: {name}",
            description=f"{len(self.playlist_storage[user_id][name])} track(s)",
            color=self.sc_orange
        )

        track_list = ""
        for i, track in enumerate(self.playlist_storage[user_id][name], 1):
            if i <= 15:  # Show only first 15 tracks to avoid embed limit
                track_list += f"{i}. [{track['title']}]({track['url']})\n"

        remaining = len(self.playlist_storage[user_id][name]) - 15
        if remaining > 0:
            track_list += f"\n*And {remaining} more track(s)*"

        embed.add_field(
            name="Tracks",
            value=track_list or "No tracks in playlist",
            inline=False
        )

        embed.set_footer(text="Use !playplaylist [name] to play this playlist")

        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="playplaylist")
    async def playplaylist(self, interaction, name):
        user_id = interaction.author.id

        if user_id not in self.playlist_storage or not self.playlist_storage[user_id]:
            embed = nextcord.Embed(
                title="Error",
                description="You don't have any saved playlists",
                color=self.error_red
            )
            return await interaction.response.send_message(embed=embed)

        if name not in self.playlist_storage[user_id]:
            embed = nextcord.Embed(
                title="Error",
                description=f"Playlist `{name}` not found",
                color=self.error_red
            )
            return await interaction.response.send_message(embed=embed)

        if not self.playlist_storage[user_id][name]:
            embed = nextcord.Embed(
                title="Error",
                description=f"Playlist `{name}` is empty",
                color=self.error_red
            )
            return await interaction.response.send_message(embed=embed)

        if not interaction.author.voice:
            embed = nextcord.Embed(
                title="Error",
                description="You need to be in a voice channel to use this command",
                color=self.error_red
            )
            return await interaction.response.send_message(embed=embed)

        guild_id = interaction.guild.id
        if guild_id not in self.playlists:
            self.playlists[guild_id] = deque()
        else:
            self.playlists[guild_id].clear()

        for track in self.playlist_storage[user_id][name]:
            self.playlists[guild_id].append(track)

        voice_client = self.get_voice_client(guild_id)
        if not voice_client or not voice_client.is_connected():
            try:
                voice_client = await interaction.author.voice.channel.connect()
                self.voice_clients[guild_id] = voice_client
            except Exception as e:
                embed = nextcord.Embed(
                    title="Error",
                    description=f"Could not connect to voice channel: {str(e)}",
                    color=self.error_red
                )
                return await interaction.response.send_message(embed=embed)

        if voice_client.is_playing():
            voice_client.stop()

        await self.play_next(guild_id)

        embed = nextcord.Embed(
            title="Playing Playlist",
            description=f"Now playing playlist `{name}` ({len(self.playlist_storage[user_id][name])} track(s))",
            color=self.success_green
        )
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="removeplaylist")
    async def removeplaylist(self, interaction, name):
        user_id = interaction.author.id

        if user_id not in self.playlist_storage or name not in self.playlist_storage[user_id]:
            embed = nextcord.Embed(
                title="Error",
                description=f"Playlist `{name}` not found",
                color=self.error_red
            )
            return await interaction.response.send_message(embed=embed)

        del self.playlist_storage[user_id][name]

        embed = nextcord.Embed(
            title="Playlist Removed",
            description=f"Removed playlist `{name}`",
            color=self.success_green
        )
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="clearqueue")
    async def clearqueue(self, interaction):
        guild_id = interaction.guild.id

        if guild_id in self.playlists:
            self.playlists[guild_id].clear()

        embed = nextcord.Embed(
            title="Queue Cleared",
            description="Cleared the queue, but current track will continue playing",
            color=self.success_green
        )
        await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(SoundCloudPlayer(bot))
