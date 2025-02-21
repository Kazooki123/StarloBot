import asyncio
import json
import os
import random
from typing import Optional

import nextcord
from nextcord.ext import commands


class EmojiQuiz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emoji_quiz_data = self.load_quiz_data()
        self.active_games = {}

    def load_quiz_data(self) -> dict:
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(script_dir)
            file_path = os.path.join(parent_dir, 'json', 'emoji-quiz.json')

            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Error: Could not find emoji-quiz.json at {file_path}")
            return {"questions": []}
        except json.JSONDecodeError:
            print("Error: Invalid JSON format in emoji-quiz.json")
            return {"questions": []}
        except Exception as e:
            print(f"Error loading quiz data: {e}")
            return {"questions": []}

    def get_random_question(self) -> Optional[dict]:
        if not self.emoji_quiz_data.get("questions"):
            return None
        return random.choice(self.emoji_quiz_data["questions"])

    @commands.command(name="emojiquiz", help="Start an emoji quiz!")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def emojiquiz(self, ctx: commands.Context):
        # Check if user is already in a game
        if ctx.author.id in self.active_games:
            await ctx.send("You already have an active quiz! Finish that one first.")
            return

        # Get a random question
        question = self.get_random_question()
        if not question:
            await ctx.send("Sorry, no quiz questions are available right now!")
            return

        self.active_games[ctx.author.id] = True

        try:
            # Create and send the quiz embed
            embed = nextcord.Embed(
                title="🎮 Emoji Quiz",
                description=f"Guess the word represented by these emojis:\n\n{' '.join(question['emojis'])}",
                color=nextcord.Color.blue()
            )
            embed.add_field(name="Instructions", value="Type your answer in lowercase!", inline=False)
            embed.set_footer(text="You have 30 seconds to answer!")

            await ctx.send(embed=embed)

            def check(message):
                return (
                        message.author == ctx.author
                        and message.channel == ctx.channel
                        and len(message.content) > 0
                )

            try:
                # Wait for the user's answer
                guess = await ctx.bot.wait_for(
                    'message',
                    timeout=30.0,
                    check=check
                )

                # Check if the answer is correct
                if guess.content.lower() == question['answer'].lower():
                    result_embed = nextcord.Embed(
                        title="🎉 Correct!",
                        description=f"Congratulations {ctx.author.mention}! You got it right!",
                        color=nextcord.Color.green()
                    )
                else:
                    result_embed = nextcord.Embed(
                        title="❌ Incorrect",
                        description=f"Sorry, the correct answer was: **{question['answer']}**",
                        color=nextcord.Color.red()
                    )

                await ctx.send(embed=result_embed)

            except asyncio.TimeoutError:
                timeout_embed = nextcord.Embed(
                    title="⏰ Time's Up!",
                    description=f"The correct answer was: **{question['answer']}**",
                    color=nextcord.Color.orange()
                )
                await ctx.send(embed=timeout_embed)

        except Exception as e:
            error_embed = nextcord.Embed(
                title="❌ Error",
                description="Sorry, something went wrong with the quiz.",
                color=nextcord.Color.red()
            )
            await ctx.send(embed=error_embed)
            print(f"Error in emoji quiz: {e}")

        finally:
            self.active_games.pop(ctx.author.id, None)

    @emojiquiz.error
    async def emojiquiz_error(self, ctx: commands.Context, error):
        """Handle errors for the emojiquiz command."""
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Please wait {error.retry_after:.1f} seconds before using this command again!")
        else:
            await ctx.send(f"An error occurred: {str(error)}")


def setup(bot):
    bot.add_cog(EmojiQuiz(bot))
