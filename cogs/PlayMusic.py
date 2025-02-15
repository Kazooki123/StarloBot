import nextcord
from nextcord.ext import commands
import yt_dlp as youtube_dl
import asyncio

intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

class YTDLSource(nextcord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
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
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(nextcord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class PlayMusic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="play")
    async def play(self, ctx, *, search):
        """Plays from a url (almost anything youtube_dl supports)"""
        if not ctx.message.author.voice:
            await ctx.send('You must be in a voice channel to play music.')
            return

        channel = ctx.message.author.voice.channel
        if not channel:
            await ctx.send('You are not in a voice channel.')
            return

        voice_client = nextcord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
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
            ytdl = youtube_dl.YoutubeDL(ytdl_opts)

            loop = ctx.bot.loop

            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=False))
            song = data['entries'][0] if 'entries' in data else data

            player = await YTDLSource.from_url(song['webpage_url'], loop=ctx.bot.loop)
            ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(player.title))

def setup(bot):
    bot.add_cog(PlayMusic(bot))