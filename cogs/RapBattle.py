import nextcord
from nextcord.ext import commands
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

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

    @nextcord.slash_command(
        name="rapbattle",
        description="Starts a rap battle between two characters!",
        guild_ids=[1237746712291049483]
    )
    async def rapbattle(self, interaction: nextcord.Interaction, character1: str, vs: str, character2: str):
        if vs.lower() != "vs":
            await interaction.response.send_message("Usage: /rapbattle {character1} vs {character2}")
            return

        try:
            character1_lines = []
            character2_lines = []
            rounds = 3

            await interaction.response.defer()

            for _ in range(rounds):
                character1_lines.append(self.generate_rap_line(character1, character1_lines + character2_lines))
                character2_lines.append(self.generate_rap_line(character2, character1_lines + character2_lines))

            embed = nextcord.Embed(title="Rap Battle", color=nextcord.Color.gold())
            embed.add_field(name=character1, value="\n".join(character1_lines), inline=False)
            embed.add_field(name=character2, value="\n".join(character2_lines), inline=False)

            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send("An error occurred during the rap battle.")

def setup(bot):
    bot.add_cog(RapBattle(bot))
