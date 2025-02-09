import nextcord
from nextcord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(
        name="customhelp",
        description="List of helpful, fun, enjoying commands!",
        guild_ids=[1237746712291049483]
    )
    async def customhelp(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(title="Bot Commands", description="List of available commands:")

        # Add command descriptions

        embed.add_field(name="!ban", value="Get a list of banned members", inline=False)
        embed.add_field(name="!kick", value="Kick a member from the server", inline=False)
        embed.add_field(name="!timeout", value="Timeout a member for a specified duration", inline=False)
        embed.add_field(name="!jokes", value="Tells a random,cringe,edgy,funny joke", inline=False)
        embed.add_field(name="!quote", value="Get random quotes", inline=False)
        embed.add_field(name="!searchimage", value="Search and display an image using Google search engine though "
                                                   "remember that it has limitations", inline=False)
        embed.add_field(name="!link_to_video", value="Convert a YOUTUBE video link to an actual video", inline=False)
        embed.add_field(name="!link_to_image", value="Convert an image link to an actual image", inline=False)
        embed.add_field(name="!apply", value="Apply for a job to gain game currencies.", inline=False)
        embed.add_field(name="!work", value="To gain more money as a salary(Prices will sometimes drop).", inline=False)
        embed.add_field(name="!wallet", value="To see what you have from your game wallet.", inline=False)
        embed.add_field(name="!play", value="Plays music(Note: Due to errors the music wont play).", inline=False)
        embed.add_field(name="!stop", value="Stops the music.", inline=False)
        embed.add_field(name="!disconnect", value="Disconnects the bot from the voice channel.", inline=False)

        await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))
