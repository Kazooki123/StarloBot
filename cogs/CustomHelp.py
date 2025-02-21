import nextcord
from nextcord.ext import commands


class HelpPaginator(nextcord.ui.View):
    def __init__(self, bot, ctx):
        super().__init__(timeout=180)
        self.bot = bot
        self.ctx = ctx
        self.current_page = 0
        self.commands_per_page = 5

        self.command_list = [
            ("!ping", "**Ping the Bot if it's alive!**"),
            ("!ban", "**Get a list of banned members**"),
            ("!kick", "**Kick a member from the server**"),
            ("!bibleverse", "**Returns a bible verse**"),
            ("!afk", "**Set your status to AFK.**"),
            ("!appeal", "**Appeal for a unban.**"),
            ("!playcards", "**Play cards with your friends or opponent!**"),
            ("!timeout", "**Timeout a member for a specified duration**"),
            ("!jokes", "**Tells a random, cringe, edgy, funny joke**"),
            ("!quote", "**Get random quotes**"),
            ("!birthday", "**Set your Birthday, format is: DD/MM/YYYY**"),
            ("!urban", "**Get a meaning of a word using Urban Dictionary!**"),
            ("!steam", "**Search for any Games in the Steam Library!**"),
            ("!epicgames", "**Search for any Games in the Epic Store Library!**"),
            ("!wikipedia", "**Search for Information in Wikipedia!**"),
            ("!animal", "**Shows a random image & fact of an animal!**"),
            ("!searchimage", "**Search and display an image using Google!**"),
            ("!link2video", "**Converts a YOUTUBE video link to an actual video**"),
            ("!link2image", "**Convert an image link to an actual image**"),
            ("!apply", "**Apply for a job to gain game currencies.**"),
            ("!work", "**To gain more money as a salary.**"),
            ("!wallet", "**To see what you have from your game wallet.**"),
            ("!play", "**Plays a music of your choice!**"),
            ("!stop", "**Stops the music.**"),
            ("!call", "**Call a user across discord servers.**"),
            ("!answer", "**Answer a call from a stranger!**"),
            ("!reportcall", "**Report a user or caller so we can remove its privileges**"),
            ("!bored", "**Get a random activity when bored.**"),
            ("!setempire", "**Create your own empire and expand it!**"),
            ("!aesthetic", "**Returns a image of a aesthetic type**"),
            ("!choose_pokemon", "**Choose your Pokemon!**"),
            ("!pokebattle", "**Battle with a Pokemon user!**"),
            ("!blackjack", "**Play Blackjack with your friends against the Dealer!**"),
            ("!hangman", "**Play and guess a word!**"),
            ("!ai_art", "**Generate a A.I Image!**"),
            ("!guess-flag", "**Guess the flag game!**"),
            ("!leaderboard", "**Shows the Leaderboard, specify a type first.**"),
            ("!timezone", "**Show your TimeZone!**"),
            ("!movies", "**Search for Movies!**"),
            ("!anime", "**Search and display your favorite anime!**"),
            ("!lyrics", "**Displays a Lyric from a song using Genius.**")
        ]

        self.total_pages = (len(self.command_list) - 1) // self.commands_per_page + 1

        # Disable "< Previous" button initially
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == self.total_pages - 1

    def get_embed(self):
        """Generates an embed for the current page."""
        embed = nextcord.Embed(
            title="🤖 Bot Commands",
            description="**List of available commands! 🤩**",
            color=nextcord.Color.green(),
            timestamp=datetime.utcnow(),
        )

        # Add commands for the current page
        start = self.current_page * self.commands_per_page
        end = start + self.commands_per_page
        for cmd, desc in self.command_list[start:end]:
            embed.add_field(name=cmd, value=desc, inline=False)

        embed.set_footer(
            text=f"Requested by {self.ctx.author} | Page {self.current_page + 1} of {self.total_pages}",
            icon_url=self.ctx.author.avatar.url if self.ctx.author.avatar else None
        )
        embed.set_image(url="https://pbs.twimg.com/media/EhFNVcSXkAEhlPP?format=jpg&name=large")

        return embed

    @nextcord.ui.button(label="< Previous", style=nextcord.ButtonStyle.gray, disabled=True, custom_id="previous_button")
    async def previous_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        """Handles the previous button click."""
        await interaction.response.defer()  # Acknowledge the button press
        if self.current_page > 0:
            self.current_page -= 1

        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = False
        await interaction.edit(embed=self.get_embed(), view=self)

    @nextcord.ui.button(label="Next >", style=nextcord.ButtonStyle.gray, custom_id="next_button")
    async def next_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        """Handles the next button click."""
        await interaction.response.defer()
        if self.current_page < self.total_pages - 1:
            self.current_page += 1

        self.previous_button.disabled = False
        self.next_button.disabled = self.current_page == self.total_pages - 1
        await interaction.edit(embed=self.get_embed(), view=self)


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="customhelp")
    async def customhelp(self, ctx):
        """Sends the paginated help embed."""
        view = HelpPaginator(self.bot, ctx)
        await ctx.send(embed=view.get_embed(), view=view)


def setup(bot):
    bot.add_cog(Help(bot))
