import nextcord
from nextcord.ext import commands


class Hangman(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(name='hangman', description="Plays Hangman!")
    async def hangman(self, ctx: nextcord.Interaction):
        word_to_guess = "discord"  # Replace with your word selection logic
        guessed_word = ['_'] * len(word_to_guess)
        attempts_left = 6

        while attempts_left > 0 and '_' in guessed_word:
            await ctx.send(f"{' '.join(guessed_word)}\nAttempts left: {attempts_left}")
            guess = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            guess = guess.content.lower()

            if guess in word_to_guess:
                for i, letter in enumerate(word_to_guess):
                    if letter == guess:
                        guessed_word[i] = guess
            else:
                attempts_left -= 1

        if '_' not in guessed_word:
            await ctx.send(f"Congratulations! You guessed the word: {''.join(guessed_word)}")
        else:
            await ctx.send(f"Sorry, you ran out of attempts. The word was: {word_to_guess}")
            
            
def setup(bot):
    bot.add_cog(Hangman(bot))
