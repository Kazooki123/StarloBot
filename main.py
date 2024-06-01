import discord
from discord import Color
from dotenv import load_dotenv
from discord.ext import commands, tasks
from discord.ext.commands import BucketType
from discord.ui import Button, View
import requests
from requests import get
import random
import aiohttp
import os
import asyncio
from pytube import YouTube
import json
import io
import wikipediaapi 
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
# from googleapiclient.discovery import build
import google.generativeai as genai
from sympy import symbols, solve, Eq
import asyncpg
import yt_dlp as youtube_dl
import ffmpeg
from upstash_redis import Redis
import redis
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from groq import Groq

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
DATABASE_URL = os.getenv('POSTGRES_URL')
HUGGING_FACE_API_TOKEN = os.getenv('HUGGING_FACE_API')
NINJA_API = os.getenv('NINJA_API_KEY')
MONGO_DB_URL = os.getenv('MONGO_DB_URL')
GEMINI_API = os.getenv('GEMINI_TOKEN')

intents = discord.Intents.all()
intents.members = True
intents.message_content = True
intents.messages = True  # Enable message related events
intents.guilds = True    # Enable server-related events
intents.typing = True   # Enabled typing-related events for simplicity (optional)

bot = commands.Bot(command_prefix='!', case_insensitive=True, intents=intents)

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'emoji-quiz.json')

# Load emoji quiz questions from the JSON file
with open(file_path, 'r', encoding='utf-8') as file:
    emoji_quiz_data = json.load(file)


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
                level integer,
                birthday date,
                premium_user boolean DEFAULT FALSE
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS fact_channels (
                channel_id bigint UNIQUE
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
              guild_id BIGINT PRIMARY KEY,
              level_channel_id BIGINT
            );
            """
        )
        
# Redis connection
try:
  redis = Redis.from_env()
  # Explicitly check connection using ping
  if redis.ping():
    print("Connection to Redis successful!")
  else:
    print("Connection to Redis failed. Please check credentials and network connectivity.")

except redis.exceptions.ConnectionError as e:
     print(f"Error connecting to Redis: {e}")
     

# MongoDB Connection
uri = MONGO_DB_URL

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
   
      
client = Groq(
    api_key = os.getenv('GROQ_API_KEY'),
)
 
 
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

genai.configure(api_key=GEMINI_API)

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 400,
}

model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user.name}')
    bot.pg_pool = await create_pool()  # Move the pool creation inside the on_ready event
    await create_table()
    check_birthdays.start()
    #send_daily_fact.start()
    print("The bot is ready and the pg_pool attribute is created.")
    
    
@bot.command()
async def load(ctx, extension):
    bot.load_extension(f'cogs.{extension}')

@bot.command()
async def unload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')    
    
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')
    

async def get_user_balance(user_id):
    async with bot.pg_pool.acquire() as connection:
        result = await connection.fetchrow(
            """
            SELECT wallet FROM user_data WHERE user_id = $1;
            """, user_id
        )
        return result['wallet'] if result else 0
    
async def update_user_balance(user_id, amount):
    async with bot.pg_pool.acquire() as connection:
        await connection.execute(
            """
            UPDATE user_data 
            SET wallet = wallet + $1
            WHERE user_id = $2
            """, amount, user_id
        )
        
class MoneyRequestView(View):
    def __init__(self, sender_id, recipient_id, amount):
        super().__init__(timeout=None)
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.amount = amount
        
    @discord.ui.button(label="Accept✅", style=discord.ButtonStyle.success)
    async def accept_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.recipient_id:
            await interaction.response.send_message("You are not the intended recipient of this request.", ephemeral=True)
            return
        
        # Update database
        await update_user_balance(self.recipient_id, -self.amount)
        await update_user_balance(self.sender_id, self.amount)

        await interaction.response.send_message(f"Request accepted. {self.amount}🪙 has been transferred to {interaction.guild.get_member(self.sender_id).mention}.", ephemeral=True)
        await interaction.message.delete()

    @discord.ui.button(label="Deny❌", style=discord.ButtonStyle.danger)
    async def deny_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.recipient_id:
            await interaction.response.send_message("You are not the intended recipient of this request.", ephemeral=True)
            return

        await interaction.response.send_message(f"Request denied. {self.amount}🪙 was not transferred.", ephemeral=True)
        await interaction.message.delete()

@bot.command()
async def request(ctx, recipient: discord.User, amount: int):
    sender_id = ctx.author.id
    recipient_id = recipient.id

    # Check if the sender has enough balance
    sender_balance = await get_user_balance(sender_id)
    if sender_balance < amount:
        await ctx.send("You do not have enough balance to make this request.")
        return

    embed = discord.Embed(
        title="Money Request",
        description=f"{ctx.author.mention} wants to send a request of {amount}🪙 to {recipient.mention}",
        color=discord.Color.green()
    )

    view = MoneyRequestView(sender_id, recipient_id, amount)
    
    try:
        await recipient.send(embed=embed, view=view)
        await ctx.send(f"Request sent to {recipient.mention} successfully.")
    except discord.Forbidden:
        await ctx.send(f"Failed to send a request. {recipient.mention} has DMs disabled.")


@bot.command(name='chat')
async def generate_chat(ctx):
    # Pass the user's message content to the chatbot
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": ctx.message.content,
            }
        ],
        model="gemma-7b-it",
        temperature=0.5,
        max_tokens=1024,
        top_p=1,
        stop=None
    )

    # Send the chatbot's response back to the Discord channel
    await ctx.send(chat_completion.choices[0].message.content)


# RAP BATTLE COMMAND (For fun using A.I)
def generate_rap_line(character, previous_lines):
    prompt = f"{character} is a rapper in a rap battle. "
    for line in previous_lines:
        prompt += f"{line}\n"
    prompt += f"{character} responds:" 
    
    response = model.generate_content(prompt)
    
    text = response.candidates[0].content.parts[0].content
    
    return text.strip()

@bot.command()
async def rapbattle(ctx, character1: str, vs: str, character2: str):
    if vs.lower() != "vs".lower():
        await ctx.send("Usage: !rapbattle {character} V.S {character}")
        return
    
    character1_lines = []
    character2_lines = []
    
    rounds = 3
    
    for i in range(rounds):
        line1 = generate_rap_line(character1, character1_lines + character2_lines)
        character1_lines.append(line1)
        
        line2 = generate_rap_line(character2, character1_lines + character2_lines)
        character2_lines.append(line2)
        
    embed = discord.Embed(title="Rap Battle", color=discord.Color.gold())
    embed.add_field(name=f"{character1}:", value="\n".join(character1_lines), inline=False)
    embed.add_field(name=f"{character2}:", value="\n".join(character2_lines), inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def channellevel(ctx):
    channel_id = ctx.channel.id
    guild_id = ctx.guild.id
    
    async with bot.pg_pool.acquire() as connection:
        await connection.execute(
            'INSERT INTO settings (guild_id, level_channel_id) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET level_channel_id = $2',
            guild_id, channel_id
        )
    
    await ctx.send(f"Level-up announcements will now be sent in this channel: {ctx.channel.mention}")

async def get_level_channel(guild_id):
    async with bot.pg_pool.acquire() as connection:
        record = await connection.fetchrow('SELECT level_channel_id FROM settings WHERE guild_id = $1', guild_id)
        return record['level_channel_id'] if record else None

async def update_experience(user_id, guild_id):
    async with bot.pg_pool.acquire() as connection:
        user_data = await connection.fetchrow('SELECT experience, level FROM user_data WHERE user_id = $1', user_id)
        
        if user_data is None:
            await connection.execute(
                'INSERT INTO user_data (user_id, experience, level) VALUES ($1, $2, $3)',
                user_id, 0, 1
            )
            experience = 0
            level = 1
        else:
            experience = user_data['experience'] if user_data['experience'] is not None else 0
            level = user_data['level'] if user_data['level'] is not None else 1
        
        experience += 20  # Increment experience by 20, adjust as needed
        new_level = level
        
        while experience >= 50 * (new_level ** 2):
            experience -= 50 * (new_level ** 2)
            new_level += 1
        
        await connection.execute(
            'UPDATE user_data SET experience = $1, level = $2 WHERE user_id = $3',
            experience, new_level, user_id
        )
    
    if new_level > level:
        user = await bot.fetch_user(user_id)
        level_channel_id = await get_level_channel(guild_id)
        if level_channel_id:
            level_channel = bot.get_channel(level_channel_id)
            if level_channel:
                await level_channel.send(f"{user.mention} is now level {new_level}!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    public_channels = [channel.id for channel in message.guild.text_channels if not channel.is_nsfw()]
    if message.channel.id in public_channels:
        await update_experience(message.author.id, message.guild.id)
    
    await bot.process_commands(message)


@bot.command(name='premium')
async def premium(ctx):
    message = (
        'Commands like "!ai_art" and "!question" are officially locked.'
        'You\'ll have to pay premium, contact or DM Starlo for payments.'
    )
    await ctx.send(message)

async def is_premium(user_id):
    async with bot.pg_pool.acquire() as connection:
        record = await connection.fetchrow(
            """
            SELECT premium_user FROM user_data
            WHERE user_id = $1;
            """, user_id
        )
        return record and record['premium_user']

def premium_check():
    async def predicate(ctx):
        if await is_premium(ctx.author.id):
            return True
        else:
            await ctx.send('Looks like you haven\'t been premium yet, please type !premium, Thank you.')
            return False
    
    return commands.check(predicate)


@bot.command()
@commands.has_permissions(administrator=True)
async def add_premium(ctx, user: discord.User):
    async with bot.pg_pool.acquire() as connection:
        await connection.execute('UPDATE user_data SET premium_user = $1 WHERE user_id = $2', True, user.id)
    await ctx.send(f"{user.mention} has been added to the premium users list.")


@bot.command()
@commands.has_permissions(administrator=True)
async def remove_premium(ctx, user: discord.User):
    async with bot.pg_pool.acquire() as connection:
        await connection.execute('UPDATE user_data SET premium_user = $1 WHERE user_id = $2', False, user.id)
    await ctx.send(f"{user.mention} has been removed from the premium users list.")


@bot.command()
@commands.has_permissions(administrator=True)
async def ban(ctx, member: discord.Member):
    await member.ban()
    await ctx.send(f"{member.mention} has been banned. You naughty bastard.")

@bot.command()
@commands.has_permissions(administrator=True)
async def kick(ctx, member: discord.Member):
    await member.kick()
    await ctx.send(f"{member.mention} has been kicked.")

@bot.command()
async def button(ctx):
    button = Button(label="Click Me!", style=discord.ButtonStyle.primary)
    
    async def button_callback(interaction):
        await interaction.response.send_message("Button Clicked!")
        
    button.callback = button_callback
    
    view = View()
    view.add_item(button)
    
    await ctx.send("Here's a button:", view=view)


@bot.command()
@commands.cooldown(1, 10, BucketType.user)
async def rank(ctx):
    user_id = ctx.author.id
    async with bot.pg_pool.acquire() as connection:
        record = await connection.fetchrow(
            """
            SELECT level FROM user_data
            WHERE user_id = $1;
            """, user_id
        )
        
        if record:
            level = record['level']
            
            embed = discord.Embed(title=f"{ctx.author} Level!", color=discord.Color.red())
            embed.add_field(name="Your level", value=f"{ctx.author.mention}, You're level {level}!", inline=False)
            await ctx.send(embed=embed)
        else:
            embed.add_field(name="Failed!", value="You don't have a level yet.", inline=False)
            await ctx.send(embed=embed)


@bot.command(name='leaderboard')
@commands.cooldown(1, 10, BucketType.user)
async def leaderboard(ctx, types: str):
    if types.lower() not in ["money", "level"]:
        await ctx.send("Invalid type! Please use '!leaderboard money' or '!leaderboard level'.")
        return
    
    async with bot.pg_pool.acquire() as connection:
        if types.lower() == "money":
            query = 'SELECT user_id, wallet FROM user_data ORDER BY wallet DESC LIMIT 10'
        else:
            query = 'SELECT user_id, level FROM user_data ORDER BY level DESC LIMIT 10'
            
        records = await connection.fetch(query)  
        
    if not records:
        await ctx.send("No data available for the leaderboard.")
        return
    
    embed = discord.Embed(title=f"Top 10 Users by {types.capitalize()}", color=discord.Color.red())
    
    for i, record in enumerate(records):
        user_id = record['user_id']
        value = record['wallet'] if types.lower() == "money" else record['level']
        user = await bot.fetch_user(user_id)
        medal = "" 
        if i == 0:
            medal = " 🥇 "
        elif i == 1:
            medal = " 🥈 "
        elif i == 2:
            medal = " 🥉 "
        embed.add_field(name=f"{medal}{user}", value=f"{types.capitalize()}: {value}", inline=False)
        
        
    await ctx.send(embed=embed)
        

@bot.command()
async def birthday(ctx, date: str, member: discord.Member = None):
    if member is None:
        member = ctx.author
    
    try:
        birthday_date = datetime.strptime(date, "%m/%d/%Y")
        
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO user_data (user_id, birthday)
                VALUES ($1, $2)
                ON CONFLICT (user_id) DO UPDATE
                SET birthday = EXCLUDED.birthday;
                """, ctx.author.id, birthday_date
            )
            embed = discord.Embed(title="Birthday Set", description=f"{ctx.author.mention}, Your birthday has been set to {date}!", color=discord.Color.green())
            
            embed.set_thumbnail(url=member.avatar.url)
            await ctx.send(embed=embed)
            
    except ValueError:
        await ctx.send("Please use the correct format: !birthday MM/DD/YYYY")

@tasks.loop(hours=12)
async def check_birthdays(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
        
    today = datetime.today().strftime("%m/%d")
    
    async with bot.pg_pool.acquire() as conn:
        results = await conn.fetch(
            """
            SELECT user_id FROM user_data WHERE TO_CHAR(birthday, 'MM-DD') = $1;
            """, today
        )
        
    for record in results:
        user = await bot.fetch_user(record['user_id'])
        if user:
            embed = discord.Embed(title="Happy Birthday!", description=f"It's {user.mention}'s birthday! Have a great day!🥳🍰", color=discord.Color.green())
            
            embed.set_thumbnail(url=member.avatar.url)
            await user.send(embed=embed)


# Command to start sending daily facts
@bot.command()
async def factstart(ctx):
    channel_id = ctx.channel.id
    guild = ctx.guild

    async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO fact_channels (channel_id)
                VALUES ($1)
                ON CONFLICT (channel_id) DO NOTHING;
                """, channel_id
            )
    embed = discord.Embed(title="Facts Channel Set Up", description="Daily facts will now be posted in this channel!")
    
    embed.set_thumbnail(url=guild.icon.url)
    await ctx.send(embed=embed)


async def get_random_fact():
   # Path to JSON file containing facts
  facts_file_path = "facts.json"

  # Read the JSON file
  try:
    with open(facts_file_path, "r") as file:
      data = json.load(file)
  except FileNotFoundError:
    # Handle case where "facts.json" is not found
    return "Error: Facts file 'facts.json' not found."
  except json.JSONDecodeError:
    # Handle case where "facts.json" is invalid JSON
    return "Error: 'facts.json' is not valid JSON."

  # Pick a random fact from the list
  random_fact_index = random.randint(0, len(data) - 1)
  return data[random_fact_index]


# Background task to send daily facts
@tasks.loop(hours=24)
async def send_daily_fact():
    fact = await get_random_fact()
    
    async with bot.pg_pool.acquire() as conn:
            channels = await conn.fetch(
                """
                SELECT channel_id FROM fact_channels;
                """
            )
            for record in channels:
                channel = bot.get_channel(record['channel_id'])
                if channel:
                    await channel.send(f"Facts Of the Day: {fact}")

@send_daily_fact.before_loop
async def before_send_daily_fact():
    await bot.wait_until_ready()

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
            embed = discord.Embed(title="JOKE!", color=discord.Color.red())
            embed.add_field(name="Joke for you", value=f"{ctx.author.mention}, here's a joke for you:\n{data['setup']}\n{data['delivery']}", inline=False)
            await ctx.send(embed=embed)
        else:
            embed.add_field(name="Joke for you", value=f"{ctx.author.mention}, here's a joke for you:\n{data['joke']}", inline=False)
            await ctx.send(embed=embed)
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

WEATHER_KEY = os.getenv('WEATHER_KEY')
WEATHER_API_URL = 'http://api.weatherapi.com/v1/current.json?key={WEATHER_KEY}&q={}&aqi=no'

@bot.command(name='weather')
async def get_weather(ctx, location):
  url = WEATHER_API_URL.format(location)
  guild = ctx.guild

  response = get(url)

  if response.status_code == 200:
      data = response.json()
      embed = discord.Embed(title=f"Weather in {location.title()}", color=0x00ffff)
      embed.set_thumbnail(url=guild.icon.url)
      embed.add_field(name="Temperature:", value=f"{data['current']['temp_c']}°C", inline=False)  
      embed.add_field(name="Condition:", value=f"{data['current']['condition']['text']}", inline=False)
      embed.set_footer(text=f"More info: https://www.weatherapi.com/weather/{location}")      

      await ctx.send(embed=embed)
  else:
      await ctx.send(f"Error: Could not retrieve weather data for {location}.")


## -- DECK CARDS GAME (HIGH CARD) -- ##

suits = ['♠️', '♥️', '♦️', '♣️']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
initial_deck = [f'{rank}{suit}' for suit in suits for rank in ranks]

rank_values = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
    '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
}
rank_values['A'] = 11

deck = initial_deck.copy()

# --For blackjack -- 
games = {}

def calculate_hand_value(hand):
    value = sum(rank_values[card[:-2]] for card in hand)
    num_aces = sum(1 for card in hand if card.startswith('A'))
    while value > 21 and num_aces:
        value -= 10
        num_aces -= 1
    return value

# COMMAND to start the card game --
@bot.command(name='card')
async def startgame(ctx, player1: discord.Member = None, player2: discord.Member = None):
    embed = discord.Embed(title="High Card Game", color=discord.Color.yellow())
    if player1 is None or player2 is None:
        embed.add_field(name="Warning", value="Please mention two players to start the game.", inline=False)
        await ctx.send(embed=embed)
        return
    
    global deck
    
    if len(deck) < 2:
        embed.add_field(name="Warning", value="Not enough cards in the deck to continue. Please reset the game.", inline=False)
        await ctx.send(embed=embed)
        return
    
    # Shuffle the deck
    random.shuffle(deck)
    
    # Draw cards for two players
    player1_card = deck.pop()
    player2_card  = deck.pop()
    
    # Getting the rank values for comparison
    player1_value = rank_values[player1_card[:-2]] 
    player2_value = rank_values[player2_card[:-2]]

    
    if player1_value > player2_value:
        result = embed.add_field(name="Player 1 Wins", value=f"Player 1 wins with {player1_card} against {player2_card}!")
    elif player1_value < player2_value:
        result = embed.add_field(name="Player 2 Wins", value=f"Player 2 wins with {player2_card} against {player1_card}!")
    else:
        result = embed.add_field(name="Ties", value=f"It's a tie with {player1_card} and {player2_card}!")
        
    await ctx.send(embed=result)
    
# Resets the deck
@bot.command(name='resetdeck')
async def resetdeck(ctx):
    embed = discord.Embed(title="Reset", color=discord.Color.red())
    
    global deck
    deck = initial_deck.copy()
    embed.add_field(name="Deck Reset!", value="The deck has been reset!")
    await ctx.send(embed=embed)

## BLACKJACK GAME ##
@bot.command(name='blackjack')
async def startblackjack(ctx, *players: discord.Member):
    embed = discord.Embed(title="Blackjack", color=discord.Color.red())
    
    global deck
    if not players:
        
        embed.add_field(name="Warning!", value="Please mention at least one player to start Blackjack.", inline=False)
        await ctx.send(embed=embed)
        return

    if len(deck) < 2 * (len(players) + 1):
        
        embed.add_field(name="Warning!", value="Not enough cards in the deck to continue. Please reset the game.", inline=False)
        await ctx.send(embed=embed)
        return
    
    # Shuffles the deck
    random.shuffle(deck)
    
    game_id = ctx.channel.id
    games[game_id] = {
        "players": {player: {"hand": [], "stand": False} for player in players},
        "dealer": {"hand": []},
        "deck": deck.copy()
    }
    
    for _ in range(2):
        for player in players:
            games[game_id]["players"][player]["hand"].append(games[game_id]["deck"].pop())
            games[game_id]["dealer"]["hand"].append(games[game_id]["deck"].pop())
    
    # Show initial hands
    dealer_hand = games[game_id]["dealer"]["hand"]
    dealer_hand_str = f"{dealer_hand[0]} ??"
    embed.add_field(name="Dealer", value=f"Dealer's hand: {dealer_hand_str}", inline=False)
    await ctx.send(embed=embed)
    
    for player in players:
        hand = games[game_id]["players"][player]["hand"]
        hand_str = ' '.join(hand)
        embed.add_field(name=f"{ctx.author} hand:", value=f"{player.display_name}'s hand: {hand_str} (Value: {calculate_hand_value(hand)})", inline=False)
        await ctx.send(embed=embed)
    
    embed.add_field(name="Hit or Stay?", value="Use !hit or !stand to play.", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def hit(ctx):
    embed = discord.Embed(title="Hit", color=discord.Color.red())
    
    game_id = ctx.channel.id
    if game_id not in games:
        embed.add_field(name="Warning!", value="No active Blackjack game in this channel. Start one with !startblackjack.", inline=False)
        await ctx.send(embed=embed)
        return
    
    player = ctx.author
    if player not in games[game_id]["players"]:
        embed.add_field(name="Warning!", value="You are not a part of this Blackjack game.", inline=False)
        await ctx.send(embed=embed)
        return
    
    if games[game_id]["players"][player]["stand"]:
        embed.add_field(name="Warning!", value="You have already chosen to stand.", inline=False)
        await ctx.send(embed=embed)
        return
    
    games[game_id]["players"][player]["hand"].append(games[game_id]["deck"].pop())
    hand = games[game_id]["players"][player]["hand"]
    hand_value = calculate_hand_value(hand)
    
    hand_str = ' '.join(hand)
    embed.add_field(name=f"{ctx.author} hand:", value=f"{player.display_name}'s hand: {hand_str} (Value: {hand_value})", inline=False)
    await ctx.send(embed=embed)
    
    if hand_value > 21:
        embed.add_field(name="Busts! 🚫", value=f"{player.display_name} busts! You are out of the game.", inline=False)
        await ctx.send(embed=embed)
        games[game_id]["players"][player]["stand"] = True
    
    await check_game_status(ctx)

@bot.command()
async def stand(ctx):
    embed = discord.Embed(title="Stand", color=discord.Color.blue())
    
    game_id = ctx.channel.id
    if game_id not in games:
        embed.add_field(name="Warning!", value="No active Blackjack game in this channel. Start one with !startblackjack.", inline=False)
        await ctx.send(embed=embed)
        return
    
    player = ctx.author
    if player not in games[game_id]["players"]:
        embed.add_field(name="Warning!", value="You are not a part of this Blackjack game.", inline=False)
        await ctx.send(embed=embed)
        return
    
    games[game_id]["players"][player]["stand"] = True
    embed.add_field(name=f"{ctx.author}", value=f"{player.display_name} stands.", inline=False)
    await ctx.send(embed=embed)
    
    await check_game_status(ctx)

async def check_game_status(ctx):
    game_id = ctx.channel.id
    if game_id not in games:
        return
    
    all_stand = all(player["stand"] for player in games[game_id]["players"].values())
    if all_stand:
        await dealer_turn(ctx)

async def dealer_turn(ctx):
    embed = discord.Embed(title="Dealers Turn!", color=discord.Color.yellow())
    
    game_id = ctx.channel.id
    dealer = games[game_id]["dealer"]
    deck = games[game_id]["deck"]
    
    while calculate_hand_value(dealer["hand"]) < 17:
        dealer["hand"].append(deck.pop())
    
    dealer_value = calculate_hand_value(dealer["hand"])
    dealer_hand_str = ' '.join(dealer["hand"])
    embed.add_field(name="Dealer", value=f"Dealer's hand: {dealer_hand_str} (Value: {dealer_value})", inline=False)
    await ctx.send(embed=embed)
    
    await determine_winners(ctx)

async def determine_winners(ctx):
    embed = discord.Embed(title="🏆Winner!", color=discord.Color.green())
    
    game_id = ctx.channel.id
    dealer_value = calculate_hand_value(games[game_id]["dealer"]["hand"])
    
    for player, data in games[game_id]["players"].items():
        player_value = calculate_hand_value(data["hand"])
        if player_value > 21:
            result = embed.add_field(name="Busts!❌", value=f"{player.display_name} busts and loses!", inline=False)
        elif dealer_value > 21 or player_value > dealer_value:
            result = embed.add_field(name=f"{ctx.author} Wins!", value=f"{player.display_name} wins with {player_value} against dealer's {dealer_value}!", inline=False)
        elif player_value < dealer_value:
            result = embed.add_field(name="Dealer Wins", value=f"{player.display_name} loses with {player_value} against dealer's {dealer_value}.", inline=False)
        else:
            result = embed.add_field(name="Ties!", value=f"{player.display_name} ties with dealer at {player_value}.", inline=False)
        
        await ctx.send(embed=result)
    
    del games[game_id]

## -- ENDS HERE -- ##

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
    

# Translate languages command
@bot.command(name='translate')
async def translate_language(ctx, *, language):
    return

        
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
        embed = discord.Embed(title="Your Wallet", color=discord.Color.yellow())
        embed.add_field(name="Wallet:", value=f"{ctx.author.mention}, your wallet balance is {wallet_amount} coins 🪙🪙.")
        await ctx.send(embed=embed)
    else:
        embed.add_field(name="Failed!", value=f"{ctx.author.mention}, you need to !apply for a job first.")
        await ctx.send(embed=embed)


# Wikipedia Search command
@bot.command()
async def askwiki(ctx, *, query):
    try:
        headers = {'User-Agent': 'StarloExo Bot/1.0 (Discord Bot)'}
        wiki_wiki = wikipediaapi.Wikipedia('en', headers=headers)
        page = wiki_wiki.page(query)
        page_summary = page.summary

        if page_summary:
            image_url = f"https://en.wikipedia.org/wiki/File:{page.title.replace(' ', '_')}.png"
            
            embed = discord.Embed(title=query, description=page_summary)
            embed.set_image(url=image_url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("No Wikipedia page found for the given query.")
    except json.JSONDecodeError:
        await ctx.send("Error: Invalid JSON response from the Wikipedia API.")
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")


@bot.command()
async def serverstats(ctx):
    guild = ctx.guild
    
    embed = discord.Embed(title="Server Statistics:", color=discord.Color.green())
    
    embed.set_thumbnail(url=guild.icon.url)
    
    embed.add_field(name="Server Name:", value=guild.name, inline=True)
    embed.add_field(name="Server ID:", value=guild.id, inline=True)
    embed.add_field(name="Owner:", value=guild.owner.name if guild.owner else "Unknown", inline=True)
    embed.add_field(name="Member Count:", value=guild.member_count, inline=True)
    embed.add_field(name="Creation Date:", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
    
    await ctx.send(embed=embed)

async def should_store_member_info(member):
  # Send a confirmation DM with a yes/no option (replace with actual DM content)
  await member.send("Do you want your member information stored for bot features? (yes/no)")
  try:
    response = await bot.wait_for('message', check=lambda m: m.author == member and m.channel.is_private, timeout=60)
    if response.content.lower() == 'yes':
      return True
    else:
      return False
  except asyncio.TimeoutError:
    await member.send("Timed out waiting for your response.")
    return False

@bot.command()
async def memberinfo(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
        
    if not should_store_member_info(ctx):
        await ctx.send("Sorry, member information storage is not available.")
        return
        
    embed = discord.Embed(title="Member Information", color=discord.Color.blue())
    embed.set_thumbnail(url=member.avatar.url)
    embed.add_field(name="Username:", value=member.name, inline=True)
    embed.add_field(name="Discriminator:", value=member.discriminator, inline=True)
    embed.add_field(name="ID:", value=member.id, inline=True)
    embed.add_field(name="Joined Server:", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
    embed.add_field(name="Joined Discord:", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
    
    db = client.user_data
    collection = db.member_info
    data = {
        "user_id": member.id,
        "username": member.name,
        "discriminator": member.discriminator,
        "joined_server": member.joined_at.strftime("%Y-%m-%d %H:%M:%S"),
        "joined_discord": member.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    collection.insert_one(data)

    await ctx.send(embed=embed)


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
@premium_check()
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
@premium_check()
async def answer_question(ctx, *, question):
    api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": f"Bearer {HUGGING_FACE_API_TOKEN}"}

    def query(payload):
        response = requests.post(api_url, headers=headers, json=payload)
        
        return response.content

    try:
        response = query(
            {
                "inputs": question
            }
        )
        response = response.decode('utf-8')
        answer = json.loads(response)
        answer = answer[0]['generated_text']

        

        answer_embed = discord.Embed(title="AI Answer",color=discord.Color.blue())
        answer_embed.add_field(name="Question",value=question,inline=False)
        answer_embed.add_field(name="Answer By AI",value=answer)
        await ctx.send(embed=answer_embed)

        
        response_json = json.loads(response)

        if response_json.get("error"):
            await ctx.send(f"Error generating answer: {response_json['error']}")
        else:
            answer = response_json[0]['generated_text']
            await ctx.send(answer)

    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
        await ctx.send("Error occurred while making the API request.")
        
    except ValueError as e:
        print(f"JSON Decoding Error: {e}")
        await ctx.send("Error occurred while decoding the API response.")


# Start the bot
bot.run(TOKEN)
