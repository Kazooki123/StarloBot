import nextcord
from nextcord.ext import commands, tasks
from dotenv import load_dotenv
import os
import asyncio
import datetime
from utils.DbHandler import create_pool, create_table, mongo_conns

load_dotenv('.env')
mongo_conns()

TOKEN = os.getenv('DISCORD_TOKEN')
DATABASE_URL = os.getenv('POSTGRES_URL')

intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

async def setup_database():
    try:
        bot.pg_pool = await create_pool(DATABASE_URL)
        await create_table(bot.pg_pool)
    except Exception as e:
        print(f"Database connection error: {e}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        await setup_database()
        print("Database connection established")
        
        await asyncio.sleep(1)
        
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                extension = f'cogs.{filename[:-3]}'
                try:
                    await bot.load_extension(extension)
                    print(f'Successfully loaded extension: {extension}')
                except Exception as e:
                    print(f'Failed to load extension {extension}: {str(e)}')
    except Exception as e:
        print(f"Startup error: {str(e)}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandInvokeError):
        await ctx.send('There was an error executing the command.')
        print(f"Command error: {error}")


@tasks.loop(hours=12)
async def check_birthdays():
    today = datetime.datetime.today().strftime("%m/%d")
    
    async with bot.pg_pool.acquire() as conn:
        results = await conn.fetch(
            """
            SELECT user_id FROM user_data WHERE TO_CHAR(birthday, 'MM-DD') = $1;
            """, today
        )

    for record in results:
        try:
            user = await bot.fetch_user(record['user_id'])
            if user:
                embed = nextcord.Embed(
                    title="Happy Birthday!",
                    description=f"It's {user.mention}'s birthday! Have a great day!🥳🍰",
                    color=nextcord.Color.green()
                )
                
                if user.avatar:  # Check if user has avatar
                    embed.set_thumbnail(url=user.avatar.url)
                    
                await user.send(embed=embed)
        except Exception as e:
            print(f"Error sending birthday message to {record['user_id']}: {str(e)}")

@check_birthdays.before_loop
async def before_birthday_check():
    await bot.wait_until_ready()

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
        if await is_premium(ctx.author.id):
            return True
        else:
            await ctx.send('Looks like you haven\'t been premium yet, please type !premium, Thank you.')
            return False

    return commands.check(predicate)

async def main():
    check_birthdays.start()
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())