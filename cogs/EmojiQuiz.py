import asyncio
import json
import os
import random

import nextcord
from nextcord.ext import commands

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, '../json/emoji-quiz.json')

# Load emoji quiz questions from the JSON file
if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        emoji_quiz_data = json.load(file)
else:
    raise FileNotFoundError(f"Emoji quiz file not found at path: {file_path}")
    
intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


class EmojiQuiz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="emojiquiz", help="Answer a emoji quiz!")
    async def emojiquiz(self, ctx):
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


def setup(bot):
    bot.add_cog(EmojiQuiz(bot))
