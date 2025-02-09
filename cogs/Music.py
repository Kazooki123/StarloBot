import nextcord
from nextcord.ext import commands
import yt_dlp as youtube_dl
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import bot_intents

bot = commands.Bot(intents=bot_intents())

# youtube_dl options:
ytdl_format_options = {
    'default-search': 'ytsearch',
    'quiet': True,
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(nextcord.PCMVolumeTransformer, commands.Cog):
    def __init__(self, source: object, *, data: object, volume: object = 0.5, bot: object) -> object:
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.bot = bot

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(nextcord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

    # PLAY command for music bot feature
    @nextcord.slash_command()
    async def play(self, ctx: nextcord.Interaction, *, search):
        """Plays from a url (almost anything youtube_dl supports)
        """
        if not ctx.message.author.voice:
            await ctx.send('You must be in a voice channel to play music.')
            return

        channel = ctx.message.author.voice.channel
        if not channel:
            await ctx.send('You are not in a voice channel.')
            return

        voice_client = nextcord.utils.get(bot.voice_clients, guild=ctx.guild)
        if voice_client is None:
            voice_client = await channel.connect()
        elif voice_client.channel != channel:
            await voice_client.move_to(channel)

        async with ctx.typing():
            ytdl_opts = {
                'default_search': 'ytsearch',
                'format': 'bestaudio/best',
                'quiet': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'ffmpeg-location': 'E:/Programming Files/ffmpeg/ffmpeg-2024-05-15-git-7b47099bc0-full_build/ffmpeg-2024-05-15-git-7b47099bc0-full_build/bin/',
            }
            ffmpeg_opts = {

                'options': '-vn'
            }

            ytdl = youtube_dl.YoutubeDL(ytdl_opts)

            loop = bot.loop

            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=False))
            song = data['entries'][0] if 'entries' in data else data

            player = await YTDLSource.from_url(song['webpage_url'], loop=bot.loop)
            ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(player.title))


def setup(bot):
    source = source
    data = data
    volume = 0.5
    bot.add_cog(YTDLSource(source))
