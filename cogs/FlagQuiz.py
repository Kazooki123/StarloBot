import json
import os
import random

import asyncpg
import nextcord
from dotenv import load_dotenv
from nextcord import Embed
from nextcord.ext import commands

load_dotenv('../.env')

DATABASE_URL = os.getenv("POSTGRES_URL")

script_dir = os.path.dirname(os.path.abspath(__file__))  # Gets cogs directory
parent_dir = os.path.dirname(script_dir)  # Gets parent directory
file_path = os.path.join(parent_dir, 'json', 'flagquiz.json')

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        FLAG_DATA = json.load(f)
except FileNotFoundError:
    print(f"Error: Could not find emoji-quiz.json at {file_path}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script directory: {script_dir}")
    print(f"Parent directory: {parent_dir}")
    raise FileNotFoundError(f"Emoji quiz file not found at path: {file_path}")


class FlagQuiz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}

    async def get_db_connection(self):
        return await asyncpg.connect(DATABASE_URL)

    async def update_score(self, user):
        conn = await self.get_db_connection()
        await conn.execute(
            """
            INSERT INTO flagquiz_leaderboard (user_id, username, score)
            VALUES ($1, $2, 1)
            ON CONFLICT (user_id) DO UPDATE
            SET score = flagquiz_leaderboard.score + 1
            """, user.id, user.name
        )
        await conn.close()

    async def show_leaderboard(self, ctx):
        conn = await self.get_db_connection()
        rows = await conn.fetch("SELECT username, score FROM flagquiz_leaderboard ORDER BY score DESC LIMIT 5")
        await conn.close()

        if rows:
            leaderboard = "\n".join([f"**{i + 1}.{r['username']}** - {r['score']} flags" for i, r in enumerate(rows)])
        else:
            leaderboard = "No scores yet!"

        embed = Embed(
            title="🏆 Flag Quiz Leaderboard",
            description=leaderboard,
            color=nextcord.Color.gold()
        )
        await ctx.send(embed=embed)

    async def end_game(self, message):
        user_id = message.author.id
        guesses = await self.get_score(message.author)

        await message.channel.send(f"{message.author.mention} **has guessed {guesses} flags!**")
        del self.active_games[user_id]

    async def get_score(self, user):
        conn = await self.get_db_connection()
        row = await conn.fetchrow("SELECT score FROM flagquiz_leaderboard WHERE user_id = $1", user.id)
        await conn.close()
        return row["score"] if row else 0

    @commands.command(name="flagquiz", help="Start a flag quiz guessing!")
    async def flagquiz(self, ctx, action: str = None):
        user_id = ctx.author.id

        if action == "start":
            if user_id in self.active_games:
                await ctx.send(f"❌ {ctx.author.mention} **You're already playing a flag quiz!")
                return

            country, flag = random.choice(list(FLAG_DATA.items()))
            self.active_games[user_id] = (country, flag)

            await ctx.send(f"**Flag Quiz has started!** Let's go.\n{flag}")
        elif action == "leaderboard":
            await self.show_leaderboard(ctx)
        else:
            await ctx.send("Usage: `!flagquiz start` or `!flagquiz leaderboard`")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user_id = message.author.id
        if user_id in self.active_games:
            country, flag = self.active_games[user_id]

            if message.content.lower() == "skip":
                await message.channel.send(f"Yikes! **That was {country}**!")
                self.active_games[user_id] = random.choice(list(FLAG_DATA.items()))
                await message.channel.send(self.active_games[user_id][1])
            elif message.content.lower() == "give up":
                await message.channel.send("**Are you sure? You can play anytime!** Type `yes` to confirm.")
            elif message.content.lower() == "yes":
                await self.end_game(message)
            elif message.content.lower() == country.lower():
                await self.update_score(message.author)
                self.active_games[user_id] = random.choice(list(FLAG_DATA.items()))
                await message.channel.send(f"**Correct! 🎉** Next Flag:\n{self.active_games[user_id][1]}")


def setup(bot):
    bot.add_cog(FlagQuiz(bot))
