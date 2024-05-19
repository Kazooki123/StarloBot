import discord
from discord import Color
from dotenv import load_dotenv
from discord.ext import commands, tasks
import requests
import random
import os
import asyncio
from pytube import YouTube
import json

from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
# from googleapiclient.discovery import build
from sympy import symbols, solve, Eq
import asyncpg
import yt_dlp as youtube_dl


load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
DATABASE_URL = os.getenv('POSTGRES_URL')
HUGGING_FACE_API_TOKEN = os.getenv('HUGGING_FACE_API')

intents = discord.Intents.all()
intents.members = True
intents.message_content = True
intents.messages = True  # Enable message related events
intents.guilds = True    # Enable server-related events
intents.typing = True   # Enabled typing-related events for simplicity (optional)

bot = commands.Bot(command_prefix='!', intents=intents)

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'emoji-quiz.json')

# Load emoji quiz questions from the JSON file
with open(file_path, 'r', encoding='utf-8') as file:
    emoji_quiz_data = json.load(file)

# Load/Initialize the birthday data through json format
#try:
    #with open("birthdays.json", "r") as f:
        #birthdays = json.load(f)
#except FileNotFoundError:
    #birthdays = {}

# Connect to PostgreSQL
async def create_pool():
    return await asyncpg.create_pool(DATABASE_URL)

# Load existing data when the bot starts
async def create_table():
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_data (
                user_id bigint PRIMARY KEY,
                job text,
                wallet integer,
                experience integer,
                level integer
            )
            """
        )


# youtube_dl options:
ytdl_format_options = {
    'default-search': 'ytsearch',
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

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        
    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]
        
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

#@tasks.loop(hours=24)
#async def check_birthdays():
    #today = datetime.today().strftime("%m/%d")
    #for user_id, bday in birthdays.items():
        #if bday.startswith(today):
            #user = await bot.fetch_user(user_id)
            #if user:
                #await user.send(f"It's {user.mention}'s birthday! Have a wonderful day!🥳🍰")

        
@bot.event
async def on_ready():
    #check_birthdays.start()
    print(f'We have logged in as {bot.user.name}')
    bot.pg_pool = await create_pool()  # Move the pool creation inside the on_ready event
    await create_table()
    print("The bot is ready and the pg_pool attribute is created.")
    

@bot.command()
@commands. has_permissions(administrator=True)
async def ban(ctx, member: discord.Member):
    await member.ban()
    await ctx.send(f"{member.mention} has been banned. You naughty bastard.")

@bot.command()
@commands. has_permissions(administrator=True)
async def kick(ctx, member: discord.Member):
    await member.kick()
    await ctx.send(f"{member.mention} has been kicked.")


#@bot.command()
#async def birthday(ctx, date: str):
    #try:
        #birthday_date = datetime.strptime(date, "%m/%d/%Y")
        #birthdays[str(ctx.author.id)] = date
        #with open("birthdays.json", "w") as f:
            #json.dump(birthdays, f)
            #await ctx.send(f"{ctx.author.mention}, your birthday has been set to {date}!")
    #except ValueError:
        #await ctx.send("Please use the correct format: !birthday MM/DD/YYYY")


@bot.command()
async def bibleverse(ctx, verse):
    verse = verse.strip()
    url = f"https://bible-api.com/{verse}"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        verse_data = response.json()
        text = verse_data["text"]
        
        await ctx.send(f"Bible Verse: {text}")
    else:
        await ctx.send("Failed to retrieve the Bible verse.")
        
@bot.command()
async def quote(ctx):
    response = requests.get("https://type.fit/api/quotes")
    
    quotes = response.json()
    random_quote = random.choice(quotes)
    
    quote_text = random_quote['text']
    quote_author = random_quote['author']
    
    await ctx.send(f"{quote_text} - {quote_author}")
    
    
@bot.command(name='jokes')
async def jokes(ctx):
    try:
        # Fetch a random joke from JokeAPI
        response = requests.get('https://v2.jokeapi.dev/joke/Programming,Miscellaneous,Pun,Spooky,Christmas?blacklistFlags=nsfw,religious,political,racist,sexist')
        response.raise_for_status()  # Raise an HTTPError for bad responses
        data = response.json()

        # Check if it's a two-part joke or a single-part joke
        if 'delivery' in data:
            await ctx.send(f"{ctx.author.mention}, here's a joke for you:\n{data['setup']}\n{data['delivery']}")
        else:
            await ctx.send(f"{ctx.author.mention}, here's a joke for you:\n{data['joke']}")
    except Exception as e:
        print(f"Error in !jokes command: {e}")
        await ctx.send("An error occurred while processing the command.")

@bot.command()
async def link_to_video(ctx, link):
    try:
        youtube = YouTube(link)
        video = youtube.streams.get_highest_resolution()
        video.download()
        
        file = discord.File(video.default_filename)
        await ctx.send(file=file)
    except Exception as e:
        await ctx.send("An error occurred while processing the video. Please try again later.")


@bot.command()
async def link_to_image(ctx, link):
    embed = discord.Embed(title="Image", description="Here is the image from the provided link:")
    embed.set_image(url=link)
    await ctx.send(embed=embed)


@bot.command(name='hangman')
async def hangman(ctx):
    word_to_guess = "discord"  # Replace with your word selection logic
    guessed_word = ['_'] * len(word_to_guess)
    attempts_left = 6

    while attempts_left > 0 and '_' in guessed_word:
        await ctx.send(f"{' '.join(guessed_word)}\nAttempts left: {attempts_left}")
        guess = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
        guess = guess.content.lower()

        if guess in word_to_guess:
            for i, letter in enumerate(word_to_guess):
                if letter == guess:
                    guessed_word[i] = guess
        else:
            attempts_left -= 1

    if '_' not in guessed_word:
        await ctx.send(f"Congratulations! You guessed the word: {''.join(guessed_word)}")
    else:
        await ctx.send(f"Sorry, you ran out of attempts. The word was: {word_to_guess}")


@bot.command()
async def searchimage(ctx, *, query):
    url = f"https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "searchType": "image",
        "q": query
    }
    
    response = requests.get(url, params=params).json()
    items = response.get("items", [])
    if not items:
        await ctx.send("No image found.")
        return
    
    image_url = random.choice(items)["link"]
    await ctx.send(image_url)


@bot.command()
async def meme(ctx):
    response = requests.get("https://api.imgflip.com/get_memes")
    if response.status_code == 200:
        meme_data = response.json()
        meme = random.choice(meme_data)
        meme_url = meme['url']
        await ctx.send(meme_url)
    else:
        await ctx.send("Failed to fetch a meme. Please try again later.")

@bot.command()
async def urban(ctx, *, term):
    url = f"https://api.urbandictionary.com/v0/define?term={term}"
    
    response = requests.get(url)
    data = response.json()
    
    if len(data["list"]) > 0:
        definition = data["list"][0]["definition"]
        example = data["list"][0]["example"]
        output = f"Definition of **{term}**:\n\n{definition}\n\nExample:\n{example}"
    else:
        output = f"No definition found for **{term}**."
        
    await ctx.send(output)


@bot.command()
async def timezone(ctx, country_or_city):
    try:
        response = requests.get(f"https://worldtimeapi.org/api/timezon/{country_or_city}")
        data = response.json()
        
        if response.status_code == 400 or "error" in data:
            await ctx.send("Cannot find. Please provide a valid country or city.")
        else:
            timezone = data["timezone"]
            current_time = datetime.strptime(data["datetime", "%Y-%m-%dT%H:%M:%S.%f%z"])
            formatted_time = current_time.strftime("%Y-%m-%d%H:%M:%S")
            await ctx.send(f"Timezone: {timezone}\nCurrent Time: {formatted_time}")
    except requests.exceptions.RequestException as e :
        await ctx.send(f"An error occurred: {str(e)}")
    
        
# Command to apply for a job
@bot.command(name='apply')
async def apply(ctx):
    jobs = ["Engineer", "Programmer", "Artist"]
    job_message = "\n".join([f"{i+1}. {job}" for i, job in enumerate(jobs)])

    await ctx.send(f"{ctx.author.mention}, choose a job by replying with the corresponding number:\n{job_message}")

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        reply = await bot.wait_for('message', check=check, timeout=30)
        job_number = int(reply.content)

        if 1 <= job_number <= len(jobs):
            job = jobs[job_number - 1]

            async with bot.pg_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO user_data (user_id, job, wallet)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (user_id) DO NOTHING
                    """,
                    ctx.author.id, job, 0
                )

            await ctx.send(f"{ctx.author.mention}, applied as {job}.")
        else:
            await ctx.send(f"{ctx.author.mention}, invalid job number.")
    except asyncio.TimeoutError:
        await ctx.send(f"{ctx.author.mention}, timeout. Please use !apply again.")


# Command to work
@bot.command(name='work')
async def work(ctx):
    async with bot.pg_pool.acquire() as conn:
        user_data = await conn.fetchrow(
            "SELECT job, wallet FROM user_data WHERE user_id = $1",
            ctx.author.id
        )

    if user_data:
        job, _ = user_data
        earnings = random.randint(1, 500)  # Simulate random earnings

        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE user_data
                SET wallet = wallet + $1
                WHERE user_id = $2
                """,
                earnings, ctx.author.id
            )

        await ctx.send(f"{ctx.author.mention}, you worked as a {job} and earned {earnings} coins.")
    else:
        await ctx.send(f"{ctx.author.mention}, you need to !apply for a job first.")


# Command to check wallet
@bot.command(name='wallet')
async def wallet(ctx):
    async with bot.pg_pool.acquire() as conn:
        wallet_amount = await conn.fetchval(
            "SELECT wallet FROM user_data WHERE user_id = $1",
            ctx.author.id
        )

    if wallet_amount is not None:
        await ctx.send(f"{ctx.author.mention}, your wallet balance is {wallet_amount} coins 🪙🪙.")
    else:
        await ctx.send(f"{ctx.author.mention}, you need to !apply for a job first.")


# Wikipedia Search command



@bot.command(name='emoji-quiz')
async def emoji_quiz(ctx):
    # Select a random emoji quiz question
    quiz_question = random.choice(emoji_quiz_data['questions'])
    emojis = quiz_question['emojis']
    correct_answer = quiz_question['answer'].lower()

    await ctx.send(f"Guess the word represented by these emojis: {' '.join(emojis)}")

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        guess = await bot.wait_for('message', check=check, timeout=30.0)
    except asyncio.TimeoutError:
        await ctx.send("Time's up! The correct answer was: {correct_answer}")
        return

    guess = guess.content.lower()

    if guess == correct_answer:
        await ctx.send("Congratulations! You guessed correctly.")
    else:
        await ctx.send(f"Sorry, the correct answer was: {correct_answer}")


# PLAY command for music bot feature
@bot.command(name='play', help='Plays a song')
async def play(ctx, *, search):
    """Plays from a url (almost anything youtube_dl supports)
    """
    if not ctx.message.author.voice:
        await ctx.send('You must be in a voice channel to play music.')
        return
    
    channel = ctx.message.author.voice.channel
    if not channel:
        await ctx.send('You are not in a voice channel.')
        return
    
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
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


@bot.command(name='stop', help='Stops the music')
async def stop(ctx):
    """
    Stops the music and clears queue
    """
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        voice_client.stop()
        await ctx.send('Music stopped')
    else:
        await ctx.send('No music is playing at the moment.')
        
@bot.command(name='disconnect', help='Disconnects the bot from the voice channel')
async def disconnect(ctx):
    """
    Disconnects the bot from the voice channel
    """
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
        await ctx.send('Disconnected from the voice channel.')
    else:
        await ctx.send('The bot is not connected to any voice channels.') 

@bot.command()
async def customhelp(ctx):
    embed = discord.Embed(title="Bot Commands", description="List of available commands:")

    # Add command descriptions
    
    embed.add_field(name="!ban", value="Get a list of banned members", inline=False)
    embed.add_field(name="!kick", value="Kick a member from the server", inline=False)
    embed.add_field(name="!timeout", value="Timeout a member for a specified duration", inline=False)
    embed.add_field(name="!jokes", value="Tells a random,cringe,edgy,funny joke", inline=False)
    embed.add_field(name="!quote", value="Get random quotes", inline=False)
    embed.add_field(name="!searchimage", value="Search and display an image using Google search engine though remember that it has limitations", inline=False)
    embed.add_field(name="!link_to_video", value="Convert a YOUTUBE video link to an actual video", inline=False)
    embed.add_field(name="!link_to_image", value="Convert an image link to an actual image", inline=False)
    embed.add_field(name="!apply", value="Apply for a job to gain game currencies.", inline=False)
    embed.add_field(name="!work", value="To gain more money as a salary(Prices will sometimes drop).", inline=False)
    embed.add_field(name="!wallet", value="To see what you have from your game wallet.", inline=False)
    embed.add_field(name="!play", value="Plays music(Note: Due to errors the music wont play).", inline=False)
    embed.add_field(name="!stop", value="Stops the music.", inline=False)
    embed.add_field(name="!disconnect", value="Disconnects the bot from the voice channel.", inline=False)    
    
    
    await ctx.send(embed=embed)


@bot.command(name='ai_art')
async def generate_image(ctx, *, prompt):
    api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {HUGGING_FACE_API_TOKEN}"}
    # payload = {
    #     "inputs": prompt,
    #     "options": {
    #         "wait_for_model": True
    #     }
    # }
    def query(payload):
        response = requests.post(api_url, headers=headers, json=payload)
	                             
        return response.content
    
    try:
        
        bytes = query(
            {
                "inputs": prompt
            }
        )
        import io
        from PIL import Image
        image = Image.open(io.BytesIO(bytes))
        with io.BytesIO() as image_binary:
            image.save(image_binary, 'JPEG')
            image_binary.seek(0)
            await ctx.send(file=discord.File(fp=image_binary, filename='generated_image.jpg'))

       
       

    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
        await ctx.send("Error occurred while making the API request.")

    except json.JSONDecodeError as e:
        print(f"JSON Decoding Error: {e}")
        await ctx.send("Error occurred while decoding the API response.")


# Question and answer with Huggingface Mistral-7B-Instruct-v0.2 API
@bot.command(name='question')
async def answer(ctx, *, prompt):
    # passing the hugging face API
    return

# Start the bot
bot.run(TOKEN)