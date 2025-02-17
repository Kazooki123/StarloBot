import nextcord
from nextcord.ext import commands
import datetime

intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


class Birthday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="birthday")
    async def birthday(self, ctx, date: str, member: nextcord.Member = None):
        if member is None:
            member = ctx.user
    
        try:
            birthday_date = datetime.datetime.strptime(date, "%m/%d/%Y")
        
            async with bot.pg_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO user_data (user_id, birthday)
                    VALUES ($1, $2)
                    ON CONFLICT (user_id) DO UPDATE
                    SET birthday = EXCLUDED.birthday;
                    """, ctx.user.id, birthday_date
                )
                embed = nextcord.Embed(title="Birthday Set", description=f"{ctx.user.mention}, Your birthday has been set to {date}!", color=nextcord.Color.green())
            
                embed.set_thumbnail(url=member.avatar.url)
                await ctx.send(embed=embed) 
        except ValueError:
            await ctx.send("Please use the correct format: MM/DD/YYYY")


def setup(bot):
    bot.add_cog(Birthday(bot))
