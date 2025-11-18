import nextcord
from nextcord.ext import commands


class Hangman(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(name="hangman", description="Play a word quiz with hangman!")
    async def hangman(self, interaction: nextcord.Interaction):
        word_to_guess = "discord"
        guessed_word = ['_'] * len(word_to_guess)
        attempts_left = 6
        guessed_letters = set()

        embed = nextcord.Embed(title="Hangman", color=nextcord.Color.blue())
        embed.add_field(name="Word", value=' '.join(guessed_word), inline=False)
        embed.add_field(name="Attempts Left", value=str(attempts_left), inline=False)
        embed.add_field(name="Guessed Letters", value=' '.join(guessed_letters) or "None", inline=False)
        
        await interaction.response.send_message(embed=embed)

        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id

        while attempts_left > 0 and '_' in guessed_word:
            try:
                guess_msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                guess = guess_msg.content.lower()

                if len(guess) != 1:
                    await interaction.channel.send("Please guess one letter at a time!")
                    continue

                if guess in guessed_letters:
                    await interaction.channel.send("You already guessed that letter!")
                    continue

                guessed_letters.add(guess)

                if guess in word_to_guess:
                    for i, letter in enumerate(word_to_guess):
                        if letter == guess:
                            guessed_word[i] = guess
                else:
                    attempts_left -= 1

                embed = nextcord.Embed(title="Hangman", color=nextcord.Color.blue())
                embed.add_field(name="Word", value=' '.join(guessed_word), inline=False)
                embed.add_field(name="Attempts Left", value=str(attempts_left), inline=False)
                embed.add_field(name="Guessed Letters", value=' '.join(sorted(guessed_letters)), inline=False)
                
                await interaction.channel.send(embed=embed)

            except TimeoutError:
                await interaction.channel.send("Game timed out!")
                return

        if '_' not in guessed_word:
            await interaction.channel.send("🎉 Congratulations! You won!")
        else:
            await interaction.channel.send(f"Game Over! The word was: {word_to_guess}")


def setup(bot):
    bot.add_cog(Hangman(bot))
