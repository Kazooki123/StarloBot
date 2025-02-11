import nextcord
from nextcord.ext import commands

class Hangman(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(
        name="hangman"
    )
    async def hangman(self, ctx):
        word_to_guess = "discord"  # Replace with word selection logic
        guessed_word = ['_'] * len(word_to_guess)
        attempts_left = 6
        guessed_letters = set()

        embed = nextcord.Embed(title="Hangman", color=nextcord.Color.blue())
        embed.add_field(name="Word", value=' '.join(guessed_word), inline=False)
        embed.add_field(name="Attempts Left", value=str(attempts_left), inline=False)
        embed.add_field(name="Guessed Letters", value=' '.join(guessed_letters) or "None", inline=False)
        
        await ctx.send(embed=embed)

        def check(m):
            return m.author.id == ctx.user.id and m.channel.id == ctx.channel.id

        while attempts_left > 0 and '_' in guessed_word:
            try:
                guess_msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                guess = guess_msg.content.lower()

                if len(guess) != 1:
                    await ctx.channel.send("Please guess one letter at a time!")
                    continue

                if guess in guessed_letters:
                    await ctx.channel.send("You already guessed that letter!")
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
                
                await ctx.channel.send(embed=embed)

            except TimeoutError:
                await ctx.channel.send("Game timed out!")
                return

        if '_' not in guessed_word:
            await ctx.channel.send("🎉 Congratulations! You won!")
        else:
            await ctx.channel.send(f"Game Over! The word was: {word_to_guess}")

def setup(bot):
    bot.add_cog(Hangman(bot))