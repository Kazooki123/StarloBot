import datetime
import os
import sys
import signal
import logging
from pathlib import Path

import nextcord
from dotenv import load_dotenv
from nextcord.ext import commands, tasks

from utils.DbHandler import DatabaseHandler

# Set up logging with a custom formatter that includes shard info
class ShardFormatter(logging.Formatter):
    def __init__(self, fmt, shard_id, shard_count):
        super().__init__(fmt)
        self.shard_id = shard_id
        self.shard_count = shard_count
    
    def format(self, record):
        record.shard_id = self.shard_id
        record.shard_count = self.shard_count
        return super().format(record)

logger = logging.getLogger('bot')

print("Loading environment variables...")
load_dotenv(".env")

TOKEN = os.getenv('DISCORD_TOKEN')
POSTGRES_URL = os.getenv('POSTGRES_URL')
MONGO_DB_URL = os.getenv('MONGO_DB_URL')
SHARD_ID = int(os.environ.get('SHARD_ID', 0))
SHARD_COUNT = int(os.environ.get('SHARD_COUNT', 1))

# Configure logging with custom formatter
log_format = '%(asctime)s - [Shard %(shard_id)s/%(shard_count)s] - %(levelname)s - %(message)s'
file_handler = logging.FileHandler("starlobot.log")
stream_handler = logging.StreamHandler()

for handler in [file_handler, stream_handler]:
    formatter = ShardFormatter(log_format, SHARD_ID, SHARD_COUNT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

logger.setLevel(logging.INFO)

print("\nEnvironment Variables Status:")
print(f"DISCORD_TOKEN: {'Found!' if TOKEN else 'Missing!'}")
print(f"POSTGRES_URL: {'Found!' if POSTGRES_URL else 'Missing!'}")
print(f"MONGO_DB_URL: {'Found!' if MONGO_DB_URL else 'Missing!'}\n")

if not all([TOKEN, POSTGRES_URL, MONGO_DB_URL]):
    raise ValueError("Missing required environment variables!")

# Initialize database handler
db_handler = DatabaseHandler()

bot = commands.Bot(
    intents=nextcord.Intents.all(),
    shard_id=SHARD_ID,
    shard_count=SHARD_COUNT
)

# Attach db_handler to bot for access in cogs
bot.db_handler = db_handler

@bot.event
async def on_ready():
    print(f"\nLogged in as {bot.user.name} ({bot.user.id})")
    logging.info(f'Serving {len(bot.guilds)} guilds')
    
    # Initialize database if not already done
    if bot.db_handler.pg_pool is None:
        try:
            await bot.db_handler.initialize()
            logging.info("Database initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize database: {str(e)}")
            return
    
    print("\nLoading cogs:")
    cogs_dir = Path('./cogs')

    if not cogs_dir.exists():
        print(f"Error: Cogs directory not found at {cogs_dir.absolute()}")
        return

    loaded_count = 0
    failed_cogs = []
    
    for filename in sorted(os.listdir(cogs_dir)):
        if filename.endswith('.py') and filename != '__init__.py':
            cog_name = filename[:-3]
            try:
                await bot.load_extension(f'cogs.{cog_name}')
                print(f"✓ Loaded cogs.{cog_name}")
                loaded_count += 1
            except Exception as e:
                print(f"✗ Failed to load cogs.{cog_name}: {type(e).__name__}: {str(e)}")
                failed_cogs.append((cog_name, str(e)))
                logging.error(f"Failed to load cogs.{cog_name}: {str(e)}")

    print(f"\nTotal loaded cogs: {loaded_count}")
    
    # Get command count (synced commands)
    try:
        synced = await bot.sync_all_application_commands()
        print(f"Total commands: {len(synced)}")
    except Exception as e:
        print(f"Could not sync commands: {str(e)}")
    
    if failed_cogs:
        print(f"\nFailed cogs ({len(failed_cogs)}):")
        for cog_name, error in failed_cogs:
            print(f"  - {cog_name}: {error}")

    application_id = bot.user.id
    print(f"\nApplication ID: {application_id}")
    print(f"Bot permissions enabled: {bot.intents.value}")
    print(f"Message content intent: {bot.intents.message_content}")
    
    logging.info(f'Running as shard {SHARD_ID} of {SHARD_COUNT}')

    # Set status
    await bot.change_presence(
        activity=nextcord.Activity(
            type=nextcord.ActivityType.playing,
            name="Commands | /customhelp"
        )
    )
    print("\n✓ Bot is ready!")

def signal_handler(sig, frame):
    logging.info(f"Received signal {sig}, shutting down...")
    if bot.loop and not bot.loop.is_closed():
        bot.loop.create_task(bot.close())
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

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
    # Ensure database is initialized
    if bot.db_handler.pg_pool is None:
        try:
            await bot.db_handler.initialize()
        except Exception as e:
            logging.error(f"Failed to initialize database for birthday check: {str(e)}")


# Error handling for commands
@bot.event
async def on_application_command_error(interaction, error):
    """Handle errors in slash commands"""
    print(f"\nCommand Error in {interaction.data.get('name', 'unknown')}:")
    print(f"Author: {interaction.user}")
    print(f"Channel: {interaction.channel}")
    print(f"Guild: {interaction.guild}")
    print(f"Error: {type(error).__name__}: {str(error)}")
    
    # Try to send error message if not already responded
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"**An error occurred executing this command.**\nError: {str(error)[:100]}",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"**An error occurred.**\nError: {str(error)[:100]}",
                ephemeral=True
            )
    except Exception as e:
        print(f"Could not send error message: {str(e)}")
        logging.error(f"Error message failed: {str(e)}")


# Error handling for regular commands
@bot.event
async def on_command_error(interaction, error):
    if isinstance(error, commands.errors.CommandInvokeError):
        original = error.original if hasattr(error, 'original') else error
        print(f"\nCommand Error in {interaction.command}:")
        print(f"Author: {interaction.author}")
        print(f"Channel: {interaction.channel}")
        print(f"Guild: {interaction.guild}")
        print(f"Error: {str(original)}")

        await interaction.response.send_message("**There was an error executing the command.** Please try again later.")

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
