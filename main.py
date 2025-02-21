import asyncio
import datetime
import os

import nextcord
from dotenv import load_dotenv
from nextcord.ext import commands, tasks

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
        original = error.original if hasattr(error, 'original') else error
        await ctx.send(f'There was an error executing the command: {str(original)}')
        print(f"Command error: {original}")


@bot.event
async def on_voice_state_update(member, before, after):
    if not hasattr(bot, 'lavalink'):
        return
    
    if member.id == bot.user.id:
        voice_state = {
            'sessionId': str(member.guild.voice_client.session_id if member.guild.voice_client else ''),
            'event': {
                'userId': str(member.id),
                'channelId': str(after.channel.id if after.channel else None),
                'guildId': str(member.guild.id)
            }
        }
        await bot.lavalink._dispatch_voice_state_update(member.guild.id, voice_state)

@bot.event
async def on_voice_server_update(data):
    if not hasattr(bot, 'lavalink'):
        return
    
    await bot.lavalink._dispatch_voice_server_update(int(data['guild_id']), data)

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
                
                if user.avatar:
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
    try:
        check_birthdays.start()
        await bot.start(TOKEN)
    except Exception as e:
        print(f"Error in main: {e}")
        
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot is shutting down...")
    except Exception as e:
        print(f"Fatal error: {e}")
