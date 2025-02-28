import nextcord
from nextcord.ext import commands
from utils.Paginator import Paginator


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.commands_per_page = 8
        self.bot_icon_url = "https://pbs.twimg.com/media/EhFNVcSXkAEhlPP?format=jpg&name=large"

    @commands.command(name="customhelp")
    async def customhelp(self, ctx):
        all_commands = [
            {"name": "!ban", "value": "**Get a list of banned members**"},
            {"name": "!kick", "value": "**Kick a member from the server**"},
            {"name": "!bibleverse", "value": "**Returns a bible verse**"},
            {"name": "!afk", "value": "**Set your status to AFK.**"},
            {"name": "!appeal", "value": "**Appeal for a unban.**"},
            {"name": "!playcards", "value": "**Play cards with your friends or opponent!**"},
            {"name": "!timeout", "value": "**Timeout a member for a specified duration**"},
            {"name": "!jokes", "value": "**Tells a random, cringe, edgy, funny joke**"},
            {"name": "!quote", "value": "**Get random quotes**"},
            {"name": "!steam", "value": "**Search for any Games in the Steam Library!**"},
            {"name": "!epicgames", "value": "**Search for any Games in the Epic Store Library!**"},
            {"name": "!wikipedia", "value": "**Search for Information in Wikipedia!**"},
            {"name": "!animal", "value": "**Shows a random image & fact of an animal!**"},
            {"name": "!searchimage", "value": "**Search and display an image using Google!**"},
            {"name": "!link_to_video", "value": "**Converts a YOUTUBE video link to an actual video**"},
            {"name": "!link_to_image", "value": "**Convert an image link to an actual image**"},
            {"name": "!apply", "value": "**Apply for a job to gain game currencies.**"},
            {"name": "!work", "value": "**To gain more money as a salary.**"},
            {"name": "!wallet", "value": "**To see what you have from your game wallet.**"},
            {"name": "!play", "value": "**Plays a music of your choice!**"},
            {"name": "!stop", "value": "**Stops the music.**"},
            {"name": "!disconnect", "value": "**Disconnects the bot from the voice channel.**"},
            {"name": "!call", "value": "**Call a user a cross discord servers.**"},
            {"name": "!bored", "value": "**Get a random activity when bored.**"},
            {"name": "!setempire", "value": "**Create your own empire and expand it!**"},
        ]

        total_pages = (len(all_commands) + self.commands_per_page - 1) // self.commands_per_page

        embeds = []
        for i in range(total_pages):
            start_index = i * self.commands_per_page
            end_index = min(start_index + self.commands_per_page, len(all_commands))
            page_commands = all_commands[start_index:end_index]

            embed = nextcord.Embed(
                title="🤖 Bot Commands | StarloBot",
                description="**List of available commands!🤩**",
                color=nextcord.Color.green()
            )

            for cmd in page_commands:
                embed.add_field(name=cmd["name"], value=cmd["value"], inline=False)

            embed.set_image(url=self.bot_icon_url)
            embed.set_footer(text=f"Page {i + 1}/{total_pages} • More commands to come!")

            embeds.append(embed)

        paginator = Paginator(ctx, embeds, timeout=120)
        await paginator.send()


def setup(bot):
    bot.add_cog(Help(bot))
