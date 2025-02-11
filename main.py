import traceback
import nextcord
from nextcord.ext import commands, tasks
from dotenv import load_dotenv
import os
import datetime
from utils.DbHandler import create_pool, create_table, mongo_conns

load_dotenv('.env')

TOKEN = os.getenv('DISCORD_TOKEN')
DATABASE_URL = os.getenv('POSTGRES_URL')

bot = commands.Bot(command_prefix="!", intents=nextcord.Intents.all())

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user.name}')
    
    # Load all cogs
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'Loaded {filename}')
            except Exception as e:
                print(f'Failed to load {filename}: {str(e)}')
                traceback.print_exc()
    
    # Database setup
    if hasattr(bot, 'pg_pool'):
        try:
            POSTGRES_URL = DATABASE_URL
            bot.pg_pool = await create_pool(POSTGRES_URL)
            await create_table(bot.pg_pool)
        except Exception as e:
            print(f"Database connection error: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandInvokeError):
        await ctx.send('There was an error executing the command.')
        print(f"Command error: {error}")


@tasks.loop(hours=12)
async def check_birthdays(ctx, member: nextcord.Member = None):
    if member is None:
        member = interaction.author

    today = datetime.today().strftime("%m/%d")

    async with bot.pg_pool.acquire() as conn:
        results = await conn.fetch(
            """
            SELECT user_id FROM user_data WHERE TO_CHAR(birthday, 'MM-DD') = $1;
            """, today
        )

    for record in results:
        user = await bot.fetch_user(record['user_id'])
        if user:
            embed = nextcord.Embed(title="Happy Birthday!",
                                   description=f"It's {user.mention}'s birthday! Have a great day!🥳🍰",
                                   color=nextcord.Color.green())

            embed.set_thumbnail(url=member.avatar.url)
            await user.send(embed=embed)


async def is_premium(user_id):
    async with bot.pg_pool.acquire() as connection:
        record = await connection.fetchrow(
            """
            SELECT premium_user FROM user_data
            WHERE user_id = $1;
            """, user_id
        )
        return record and record['premium_user']


def premium_check():
    async def predicate(ctx):
        if await is_premium(interaction.author.id):
            return True
        else:
            await ctx.send('Looks like you haven\'t been premium yet, please type !premium, Thank you.')
            return False

    return commands.check(predicate)

mongo_conns()
bot.run(TOKEN)