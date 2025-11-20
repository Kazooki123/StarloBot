import nextcord
from nextcord.ext import commands
import aiohttp
import asyncio

class Dictionary(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="dictionary", description="Get the meaning of a word.")
    async def dictionary(self, interaction: nextcord.Interaction, word: str):
        await interaction.response.defer()

        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    await interaction.followup.send(
                        embed=nextcord.Embed(
                            title="❌ Word Not Found",
                            description=f"No results found for **{word}**.",
                            color=0xFF0000,
                        )
                    )
                    return

                data = await response.json()

        # Extract meaning
        try:
            entry = data[0]
            meanings = entry.get("meanings", [])
            definitions_list = []

            for meaning in meanings:
                part_of_speech = meaning.get("partOfSpeech", "unknown")
                definitions = meaning.get("definitions", [])

                for d in definitions:
                    definition_text = d.get("definition", "No definition available.")
                    definitions_list.append(f"**{part_of_speech}** — {definition_text}")

            # Combine definitions
            description_text = "\n\n".join(definitions_list[:5])  # limit to 5

            embed = nextcord.Embed(
                title=f"📘 Definition of: {word}",
                description=description_text,
                color=0xFFD700
            )

            embed.set_footer(text="Source: dictionaryapi.dev")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="⚠️ Error Reading Definition",
                    description="The dictionary returned unexpected data.",
                    color=0xFFA500,
                )
            )
  

def setup(bot):
    bot.add_cog(Dictionary(bot))
