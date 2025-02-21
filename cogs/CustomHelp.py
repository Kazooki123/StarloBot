import math

import nextcord
from nextcord.ext import commands
from nextcord.ui import View, Button


class CustomHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.commands_per_page = 5

    @commands.command(name="customhelp")
    async def customhelp(self, ctx):
        commands_list = [
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
            ("!urban", "**Get a meaning of a word using Urban Dictionary!**"),
            ("!steam", "**Search for any Games in the Steam Library!**"),
            ("!epicgames", "**Search for any Games in the Epic Store Library!**"),
            ("!wikipedia", "**Search for Information in Wikipedia!**"),
            ("!animal", "**Shows a random image & fact of an animal!**"),
            ("!searchimage", "**Search and display an image using Google!**"),
            ("!link_to_video", "**Converts a YOUTUBE video link to an actual video**"),
            ("!link_to_image", "**Convert an image link to an actual image**"),
            ("!apply", "**Apply for a job to gain game currencies.**"),
            ("!work", "**To gain more money as a salary.**"),
            ("!wallet", "**To see what you have from your game wallet.**"),
            ("!play", "**Plays a music of your choice!**"),
            ("!stop", "**Stops the music.**"),
            ("!disconnect", "**Disconnects the bot from the voice channel.**"),
            ("!call", "**Call a user across discord servers.**"),
            ("!answer", "**Answer a call from a stranger!**"),
            ("!reportcall", "**Report a user or caller so we can remove its previleges**"),
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
            ("!timezone", "**Show your TimeZone!**")
        ]
        total_pages = math.ceil(len(commands_list) / self.commands_per_page)

        async def generate_embed(page):
            embed = nextcord.Embed(
                title="🤖Bot Commands",
                description=f"**List of available commands! (Page {page + 1}/{total_pages})**",
                color=nextcord.Color.green()
            )
            start_idx = page * self.commands_per_page
            for name, desc in commands_list[start_idx:start_idx + self.commands_per_page]:
                embed.add_field(name=name, value=desc, inline=False)
            embed.set_footer(text=f"Requested by {ctx.author.name}")
            return embed

        class HelpView(View):
            def __init__(self):
                super().__init__()
                self.page = 0

            async def update_message(self, interaction):
                embed = await generate_embed(self.page)
                await interaction.response.edit_message(embed=embed, view=self)

            @nextcord.ui.button(label="< Previous", style=nextcord.ButtonStyle.gray)
            async def previous_button(self, button: Button, interaction: nextcord.Interaction):
                if self.page > 0:
                    self.page -= 1
                    await self.update_message(interaction)

            @nextcord.ui.button(label="Next >", style=nextcord.ButtonStyle.gray)
            async def next_button(self, button: Button, interaction: nextcord.Interaction):
                if self.page < total_pages - 1:
                    self.page += 1
                    await self.update_message(interaction)

        embed = await generate_embed(0)
        view = HelpView()
        await ctx.send(embed=embed, view=view)


def setup(bot):
    bot.add_cog(CustomHelp(bot))
