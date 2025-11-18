import nextcord
from nextcord import Embed, Color
from nextcord.ext import commands
import subprocess
import asyncio

class Browser(commands.Cog):
    def __self__(self, bot):
        self.bot = bot

    @nextcord.slash_commands(name="browse", description="Browse through the internet in a terminal-style browser!")
    async def browse(self, interaction: nextcord.Interaction, url: str = None):
        if url is None:
            return await interaction.response.send_message("❌ Please provide a URL! Example: `!browse https://archive.org/`")

        embed = Embed(
            title="☕ Mocha-Caffe TUI Browser",
            description=f"Fetching `{url}`...",
            color=Color.yellow()
        )
        msg = await interaction.response.send_message(embed=embed)

        try:
            proc = await asyncio.create_subprocess_exec(
                ".././browsertui.exe", url,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout, stderr = await proc.communicate()
            stdout = stdout.decode(errors="ignore")
            stderr = stderr.decode(errors="ignore")

            if stderr:
                embed = Embed(
                    title="❌ Error Running TUI",
                    description=f"```{stderr}```",
                    color=Color.red()
                )
                return await msg.edit(embed=embed)

            if len(stdout) > 1900:
                stdout = stdout[:1900] + "... (**truncated**)"

            embed = Embed(
                title="️☁️ TUI Browser Output",
                description=f"```{stdout}```",
                color=Color.green()
            )
            await msg.edit(embed=embed)

        except Exception as e:
            embed = Embed(
                title="⚠️ Unexpected Error...",
                description=f"```{e}```",
                color=Color.red()
            )
            await msg.edit(embed=embed)
        

def setup(bot):
    bot.add_cog(Browser(bot))

