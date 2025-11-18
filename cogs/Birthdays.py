import datetime

import nextcord
from nextcord.ext import commands


class Birthday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="birthday", description="Set your birthday and get greeted!")
    async def birthday(self, interaction: nextcord.Interaction, date: str, member: nextcord.Member = None):
        if member is None:
            member = interaction.user
    
        try:
            birthday_date = datetime.datetime.strptime(date, "%m/%d/%Y")

            async with self.bot.pg_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO user_data (user_id, birthday)
                    VALUES ($1, $2)
                    ON CONFLICT (user_id) DO UPDATE
                    SET birthday = EXCLUDED.birthday;
                    """, interaction.user.id, birthday_date
                )
                embed = nextcord.Embed(title="Birthday Set", description=f"{interaction.user.mention}, Your birthday has been set to {date}!", color=nextcord.Color.green())
            
                embed.set_thumbnail(url=member.avatar.url)
                await interaction.response.send_message(embed=embed) 
        except ValueError:
            await interaction.response.send_message("Please use the correct format: MM/DD/YYYY")


def setup(bot):
    if not hasattr(bot, 'db_handler'):
        from utils.DbHandler import db_handler
        bot.db_handler = db_handler

    bot.add_cog(Birthday(bot))
