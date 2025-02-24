import nextcord
from nextcord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="customhelp")
    async def customhelp(self, ctx):
        url = "https://pbs.twimg.com/media/EhFNVcSXkAEhlPP?format=jpg&name=large"
        embed = nextcord.Embed(title="🤖Bot Commands", description="**List of available commands!🤩**", color=nextcord.Color.green())

        embed.add_field(name="!ban", value="**Get a list of banned members**", inline=False)
        embed.add_field(name="!kick", value="**Kick a member from the server**", inline=False)
        embed.add_field(name="!bibleverse", value="**Returns a bible verse**", inline=False)
        embed.add_field(name="!afk", value="**Set your status to AFK.**", inline=False)
        embed.add_field(name="!appeal", value="**Appeal for a unban.**", inline=False)
        embed.add_field(name="!playcards", value="**Play cards with your friends or opponent!**", inline=False)
        embed.add_field(name="!timeout", value="**Timeout a member for a specified duration**", inline=False)
        embed.add_field(name="!jokes", value="**Tells a random, cringe, edgy, funny joke**", inline=False)
        embed.add_field(name="!quote", value="**Get random quotes**", inline=False)
        embed.add_field(name="!steam", value="**Search for any Games in the Steam Library!**", inline=False)
        embed.add_field(name="!epicgames", value="**Search for any Games in the Epic Store Library!**", inline=False)
        embed.add_field(name="!wikipedia", value="**Search for Information in Wikipedia!**", inline=False)
        embed.add_field(name="!animal", value="**Shows a random image & fact of an animal!**", inline=False)
        embed.add_field(name="!searchimage", value="**Search and display an image using Google!**", inline=False)
        embed.add_field(name="!link_to_video", value="**Converts a YOUTUBE video link to an actual video**", inline=False)
        embed.add_field(name="!link_to_image", value="**Convert an image link to an actual image**", inline=False)
        embed.add_field(name="!apply", value="**Apply for a job to gain game currencies.**", inline=False)
        embed.add_field(name="!work", value="**To gain more money as a salary.**", inline=False)
        embed.add_field(name="!wallet", value="**To see what you have from your game wallet.**", inline=False)
        embed.add_field(name="!play", value="**Plays a music of your choice!**", inline=False)
        embed.add_field(name="!stop", value="**Stops the music.**", inline=False)
        embed.add_field(name="!disconnect", value="**Disconnects the bot from the voice channel.**", inline=False)
        embed.add_field(name="!call", value="**Call a user a cross discord servers.**", inline=False)
        embed.add_field(name="!bored", value="**Get a random activity when bored.**", inline=False)
        embed.add_field(name="!setempire", value="**Create your own empire and expand it!**", inline=False)
        embed.set_image(url=url)
        embed.set_footer(text="More commands to come!")

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))
