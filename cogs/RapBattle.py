import os

import google.generativeai as genai
import nextcord
from dotenv import load_dotenv
from nextcord.ext import commands

from utils.PremiumCheck import premium_check

load_dotenv('../.env')

genai.configure(api_key=os.getenv('GEMINI_TOKEN'))


class RapBattle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 400,
            }
        )

    def generate_rap_line(self, character: str, opponent: str, previous_lines: list) -> str:
        prompt = (
            f"Write a short, awesome and entertaining rap verse (2-4 lines) for {character} dissing {opponent} "
            f"based on their known characteristics. Keep it playful and fun, make it like they're roasting\n\n"
            "Previous lines:\n" + "\n".join(previous_lines) if previous_lines else ""
        )

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Error generating line: {str(e)}"

    @commands.command(
        name="rapbattle",
        help="Start a rap battle between two characters! Usage: !rapbattle character1 vs character2"
    )
    @premium_check()
    async def rapbattle(self, ctx, character1: str, vs: str, character2: str):
        if vs.lower() != "vs":
            await ctx.send("Usage: !rapbattle {character1} vs {character2}")
            return

        try:
            status_message = await ctx.send("🎤 Starting rap battle...")
            
            character1_lines = []
            character2_lines = []
            rounds = 2
            
            for round_num in range(1, rounds + 1):
                await status_message.edit(content=f"🎤 Round {round_num}/{rounds} in progress...")

                c1_verse = self.generate_rap_line(character1, character2, character1_lines + character2_lines)
                character1_lines.append(c1_verse)
                
                c2_verse = self.generate_rap_line(character2, character1, character1_lines + character2_lines)
                character2_lines.append(c2_verse)

            battle_embed = nextcord.Embed(
                title="🎤 Epic Rap Battle! 🎵",
                description=f"**{character1}** VS **{character2}**",
                color=nextcord.Color.gold()
            )

            for round_num in range(rounds):
                battle_embed.add_field(
                    name=f"Round {round_num + 1}",
                    value=f"**{character1}**:\n{character1_lines[round_num]}\n\n"
                          f"**{character2}**:\n{character2_lines[round_num]}",
                    inline=False
                )

            battle_embed.set_footer(text="Who won? React to vote! 🎯")
     
            await status_message.delete()
            await ctx.send(embed=battle_embed)

        except Exception as e:
            error_embed = nextcord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=nextcord.Color.red()
            )
            await ctx.send(embed=error_embed)

def setup(bot):
    bot.add_cog(RapBattle(bot))