import asyncio
import datetime
import os
import logging
from pathlib import Path

import nextcord
from dotenv import load_dotenv
from nextcord.ext import commands, tasks

from utils.DbHandler import db_handler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bot')

print("Loading environment variables...")
load_dotenv(".env")

TOKEN = os.getenv('DISCORD_TOKEN')
POSTGRES_URL = os.getenv('POSTGRES_URL')
MONGO_DB_URL = os.getenv('MONGO_DB_URL')

print("\nEnvironment Variables Status:")
print(f"DISCORD_TOKEN: {'Found!' if TOKEN else 'Missing!'}")
print(f"POSTGRES_URL: {'Found!' if POSTGRES_URL else 'Missing!'}")
print(f"MONGO_DB_URL: {'Found!' if MONGO_DB_URL else 'Missing!'}\n")

if not all([TOKEN, POSTGRES_URL, MONGO_DB_URL]):
    raise ValueError("Missing required environment variables!")

bot = commands.Bot(command_prefix="!", intents=nextcord.Intents.all())


@bot.event
async def on_ready():
    print(f"\nLogged in as {bot.user.name} ({bot.user.id})")
    print("\nLoading cogs:")
    cogs_dir = Path('./cogs')

    if not cogs_dir.exists():
        print(f"Error: Cogs directory not found at {cogs_dir.absolute()}")
        return

    for filename in os.listdir(cogs_dir):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f"✓ Loaded cogs.{filename[:-3]}")
            except Exception as e:
                print(f"✗ Failed to load cogs.{filename[:-3]}: {str(e)}")

    print(f"\nTotal loaded cogs: {len(bot.cogs)}")
    print(f"Total commands: {len(bot.commands)}")

    application_id = bot.user.id
    print(f"Application ID: {application_id}")
    print(f"Bot permissions enabled: {bot.intents.value}")
    print(f"Message content intent: {bot.intents.message_content}")

    # Set status
    await bot.change_presence(
        activity=nextcord.Activity(
            type=nextcord.ActivityType.listening,
            name="The users! | !customhelp"
        )
    )


@bot.event
async def on_interaction(interaction):
    print(f"Interaction received from {interaction.user} in {interaction.channel}")


@tasks.loop(hours=12)
async def check_birthdays():
    today = datetime.datetime.today().strftime("%m-%d")

    try:
        async with bot.db_handler.pg_pool.acquire() as conn:
            results = await conn.fetch(
                """
                SELECT user_id FROM user_data 
                WHERE TO_CHAR(birthday, 'MM-DD') = $1;
                """, today
            )

        for record in results:
            try:
                user = await bot.fetch_user(record['user_id'])
                if user:
                    embed = nextcord.Embed(
                        title="Happy Birthday! 🎉",
                        description=f"**It's {user.mention}'s birthday!** Have a great day!🥳🍰",
                        color=nextcord.Color.brand_green()
                    )
                    if user.avatar:
                        embed.set_thumbnail(url=user.avatar.url)
                    await user.send(embed=embed)
            except Exception as e:
                print(f"Error sending birthday message to {record['user_id']}: {str(e)}")
    except Exception as e:
        print(f"Error in birthday check: {str(e)}")


@check_birthdays.before_loop
async def before_birthday_check():
    await bot.wait_until_ready()


# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandInvokeError):
        original = error.original if hasattr(error, 'original') else error
        print(f"\nCommand Error in {ctx.command}:")
        print(f"Author: {ctx.author}")
        print(f"Channel: {ctx.channel}")
        print(f"Guild: {ctx.guild}")
        print(f"Error: {str(original)}")

        await ctx.send("**There was an error executing the command.** Please try again later.")

    print(f"Error details: {type(error).__name__}: {str(error)}")
    if hasattr(error, '__cause__') and error.__cause__:
        print(f"Caused by: {type(error.__cause__).__name__}: {str(error.__cause__)}")


# Start the bot
def run_bot():
    print("\nStarting bot...")
    check_birthdays.start()
    bot.run(TOKEN)


if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\nBot shutdown requested...")
    except Exception as e:
        print(f"\nFatal error: {e}")
