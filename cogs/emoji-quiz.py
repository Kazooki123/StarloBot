import nextcord
from nextcord.ext import commands
import json
import os
import random
import asyncio

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'emoji-quiz.json')

# Load emoji quiz questions from the JSON file
with open(file_path, 'r', encoding='utf-8') as file:
    emoji_quiz_data = json.load(file)
    
intents = nextcord.Intents.all()
intents.members = True
intents.message_content = True
intents.messages = True  # Enable message related events

bot = commands.Bot(intents=intents) 
    
class EmojiQuiz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(name='emoji-quiz', description="Plays game of emoji quiz and guess the correct answer!")
    async def emoji_quiz(self, ctx: nextcord.Interaction):
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