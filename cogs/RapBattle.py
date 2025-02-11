import nextcord
from nextcord.ext import commands
import google.generativeai as genai
import os
from dotenv import load_dotenv

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

    def generate_rap_line(self, character: str, previous_lines: list) -> str:
        prompt = f"{character} is a rapper in a rap battle. "
        prompt += "\n".join(previous_lines)
        prompt += f"\n{character} responds:"

        response = self.model.generate_content(prompt)
        return response.text.strip()

    @commands.command(
        name="rapbattle"
    )
    async def rapbattle(self, ctx, character1: str, vs: str, character2: str):
        if vs.lower() != "vs":
            await ctx.send("Usage: /rapbattle {character1} vs {character2}")
            return

        try:
            character1_lines = []
            character2_lines = []
            rounds = 3

            await ctx.response.defer()

            for _ in range(rounds):
                character1_lines.append(self.generate_rap_line(character1, character1_lines + character2_lines))
                character2_lines.append(self.generate_rap_line(character2, character1_lines + character2_lines))

            embed = nextcord.Embed(title="Rap Battle", color=nextcord.Color.gold())
            embed.add_field(name=character1, value="\n".join(character1_lines), inline=False)
            embed.add_field(name=character2, value="\n".join(character2_lines), inline=False)

            await ctx.followup.send(embed=embed)
        except Exception as e:
            await ctx.followup.send(f"An error occurred during the rap battle: {e}")

def setup(bot):
    bot.add_cog(RapBattle(bot))
