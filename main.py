import asyncio
import datetime
import os
import logging

import nextcord
from dotenv import load_dotenv
from nextcord.ext import commands, tasks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bot')

print("Loading environment variables...")
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

TOKEN = os.getenv('DISCORD_TOKEN')
POSTGRES_URL = os.getenv('POSTGRES_URL')
MONGO_DB_URL = os.getenv('MONGO_DB_URL')

print("\nEnvironment Variables Status:")
print(f"DISCORD_TOKEN: {'Found' if TOKEN else 'Missing'}")
print(f"POSTGRES_URL: {'Found' if POSTGRES_URL else 'Missing'}")
print(f"MONGO_DB_URL: {'Found' if MONGO_DB_URL else 'Missing'}\n")

if not all([TOKEN, POSTGRES_URL, MONGO_DB_URL]):
    raise ValueError("Missing required environment variables!")


class StarloBot(commands.Bot):
    def __init__(self):
        intents = nextcord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)
        self.initial_extensions = []

    async def setup_hook(self):
        """Initialize bot settings and load extensions"""
        print("\nInitializing bot setup...")

        print("\nLoading extensions:")
        await self.load_all_extensions()

        self.check_birthdays.start()
        print("\nBackground tasks started")

    async def load_all_extensions(self):
        """Load all cog extensions from the cogs directory"""
        cogs_path = 'cogs/'

        if not cogs_path.exists():
            print(f"Warning: Cogs directory not found at {cogs_path}")
            return

        for filename in os.listdir(cogs_path):
            if filename.endswith('.py'):
                extension_name = f'cogs.{filename[:-3]}'
                try:
                    await self.load_extension(extension_name)
                    print(f"✓ Loaded {extension_name}")
                except Exception as e:
                    print(f"✗ Failed to load {extension_name}: {str(e)}")

    @tasks.loop(hours=12)
    async def check_birthdays(self):
        """Check and send birthday messages every 12 hours"""
        today = datetime.datetime.today().strftime("%m-%d")

        try:
            async with self.db_handler.pg_pool.acquire() as conn:
                results = await conn.fetch(
                    """
                    SELECT user_id FROM user_data 
                    WHERE TO_CHAR(birthday, 'MM-DD') = $1;
                    """, today
                )

            for record in results:
                try:
                    user = await self.fetch_user(record['user_id'])
                    if user:
                        embed = nextcord.Embed(
                            title="Happy Birthday! 🎉",
                            description=f"It's {user.mention}'s birthday! Have a great day!🥳🍰",
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
    async def before_birthday_check(self):
        await self.wait_until_ready()

    async def on_ready(self):
        """Called when the bot is ready"""
        print("\n" + "=" * 50)
        print(f"Bot Information:")
        print(f"• Logged in as: {self.user.name} (ID: {self.user.id})")
        print(f"• Total Guilds: {len(self.guilds)}")
        print(f"• Total Commands: {len(self.commands)}")
        print(f"• Total Cogs: {len(self.cogs)}")
        print("=" * 50 + "\n")

        # Set custom status
        await self.change_presence(
            activity=nextcord.Activity(
                type=nextcord.ActivityType.watching,
                name="my commands | !help"
            )
        )

    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.errors.CommandInvokeError):
            original = error.original if hasattr(error, 'original') else error

            error_details = {
                "Command": ctx.command,
                "Author": ctx.author,
                "Channel": ctx.channel,
                "Guild": ctx.guild,
                "Error": str(original)
            }

            print("\nCommand Error Details:")
            for key, value in error_details.items():
                print(f"• {key}: {value}")

            await ctx.send(
                "There was an error executing the command. Please try again later or contact support."
            )

    async def close(self):
        """Cleanup when bot is shutting down"""
        print("\nBot is shutting down...")
        if hasattr(self, 'db_handler'):
            await self.db_handler.close()
        await super().close()


async def main():
    print("\nStarting bot...")
    bot = StarloBot()

    try:
        await bot.start(TOKEN)
    except Exception as e:
        print(f"\nCritical error: {e}")
    finally:
        await bot.close()


if __name__ == "__main__":
    try:
        print("\nInitializing bot...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot shutdown requested...")
    except Exception as e:
        print(f"\nFatal error: {e}")
