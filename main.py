import asyncio
import datetime
import os
import sys
from pathlib import Path

import nextcord
from dotenv import load_dotenv
from nextcord.ext import commands, tasks

ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

from utils.DbHandler import db_handler

# Load environment variables
load_dotenv('.env')

TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("DISCORD_TOKEN not found in environment variables!")


class StarloBot(commands.Bot):
    def __init__(self):
        intents = nextcord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)
        self.db_handler = db_handler

    async def setup_hook(self):
        """Initialize bot settings and load extensions"""
        await self.db_handler.initialize()

        # Load all cogs
        await self.load_extensions()

        # Start background tasks
        self.check_birthdays.start()

    async def load_extensions(self):
        """Load all cog extensions"""
        cogs_dir = ROOT_DIR / 'cogs'
        for filename in os.listdir(cogs_dir):
            if filename.endswith('.py'):
                extension = f'cogs.{filename[:-3]}'
                try:
                    await self.load_extension(extension)
                    print(f'Successfully loaded extension: {extension}')
                except Exception as e:
                    print(f'Failed to load extension {extension}: {str(e)}')

    async def close(self):
        """Cleanup when bot is shutting down"""
        print("Bot is shutting down...")
        await self.db_handler.close()
        await super().close()

    @tasks.loop(hours=12)
    async def check_birthdays(self):
        """Check and send birthday messages every 12 hours"""
        today = datetime.datetime.today().strftime("%m-%d")

        async with self.db_handler.pg_pool.acquire() as conn:
            results = await conn.fetch(
                """
                SELECT user_id, birthday FROM user_data 
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

    @check_birthdays.before_loop
    async def before_birthday_check(self):
        await self.wait_until_ready()

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

            print("Command Error Details:", error_details)

            await ctx.send(
                f'There was an error executing the command. Please try again later or contact support.'
            )

    async def on_voice_state_update(self, member, before, after):
        """Handle voice state updates for Lavalink"""
        if not hasattr(self, 'lavalink'):
            return

        if member.id == self.user.id:
            voice_state = {
                'sessionId': str(member.guild.voice_client.session_id if member.guild.voice_client else ''),
                'event': {
                    'userId': str(member.id),
                    'channelId': str(after.channel.id if after.channel else None),
                    'guildId': str(member.guild.id)
                }
            }
            await self.lavalink.dispatch_voice_state_update(member.guild.id, voice_state)

    async def on_voice_server_update(self, data):
        """Handle voice server updates for Lavalink"""
        if not hasattr(self, 'lavalink'):
            return
        await self.lavalink.dispatch_voice_server_update(int(data['guild_id']), data)


async def main():
    bot = StarloBot()
    try:
        await bot.start(TOKEN)
    except Exception as e:
        print(f"Critical error: {e}")
    finally:
        await bot.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot shutdown requested...")
    except Exception as e:
        print(f"Fatal error: {e}")
