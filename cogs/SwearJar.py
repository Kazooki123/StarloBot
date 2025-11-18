import os
import asyncio
import nextcord
from nextcord.ext import commands
from utils.DbHandler import db_handler


class SwearJar(commands.Cog):
    """Tracks swear words used by members and maintains a count"""
    
    def __init__(self, bot):
        self.bot = bot
        self.swear_words = []
        self.load_swear_words()
        self.db_ready = asyncio.Event()
        self.bot.loop.create_task(self.setup_database())
        
    def load_swear_words(self):
        try:
            file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bad-words.txt")
            with open(file_path, "r", encoding="utf-8") as file:
                self.swear_words = [word.strip().lower() for word in file.readlines() if word.strip()]
            print(f"Loaded {len(self.swear_words)} words into the swear jar filter")
        except Exception as e:
            print(f"Error loading swear words: {e}")
            self.swear_words = []
    
    async def setup_database(self):
        await self.bot.wait_until_ready()
        try:
            if not db_handler.pg_pool:
                print("Waiting for PostgreSQL connection to be established...")
                for _ in range(30):
                    if db_handler.pg_pool:
                        break
                    await asyncio.sleep(1)
                
                if not db_handler.pg_pool:
                    print("Failed to connect to PostgreSQL after 30 seconds")
                    return
            
            async with db_handler.pg_pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS swear_jar (
                        user_id BIGINT,
                        guild_id BIGINT,
                        count INTEGER DEFAULT 0,
                        PRIMARY KEY (user_id, guild_id)
                    )
                """)
                print("SwearJar table created successfully")
                self.db_ready.set()
        except Exception as e:
            print(f"Error creating SwearJar table: {e}")
    
    async def increment_swear_count(self, user_id, guild_id):
        await self.db_ready.wait()
        try:
            async with db_handler.pg_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO swear_jar (user_id, guild_id, count)
                    VALUES ($1, $2, 1)
                    ON CONFLICT (user_id, guild_id)
                    DO UPDATE SET count = swear_jar.count + 1
                """, user_id, guild_id)
        except Exception as e:
            print(f"Error incrementing swear count: {e}")
    
    async def get_swear_count(self, user_id, guild_id):
        await self.db_ready.wait()
        try:
            async with db_handler.pg_pool.acquire() as conn:
                count = await conn.fetchval("""
                    SELECT count FROM swear_jar
                    WHERE user_id = $1 AND guild_id = $2
                """, user_id, guild_id)
                return count or 0
        except Exception as e:
            print(f"Error getting swear count: {e}")
            return 0
    
    async def reset_swear_count(self, user_id, guild_id):
        await self.db_ready.wait()
        try:
            async with db_handler.pg_pool.acquire() as conn:
                await conn.execute("""
                    DELETE FROM swear_jar
                    WHERE user_id = $1 AND guild_id = $2
                """, user_id, guild_id)
        except Exception as e:
            print(f"Error resetting swear count: {e}")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        if not message.guild:
            return
            
        message_content = message.content.lower()
        words = message_content.split()
        
        if any(word in self.swear_words for word in words):
            await self.increment_swear_count(message.author.id, message.guild.id)

            count = await self.get_swear_count(message.author.id, message.guild.id)

            await message.channel.send(f"**{message.author.display_name}** has sworn {count} times.")
    
    @nextcord.slash_command(name="swears")
    async def check_swears(self, interaction, member: nextcord.Member = None):
        target = member or interaction.author
        count = await self.get_swear_count(target.id, interaction.guild.id)
        
        if count == 0:
            await interaction.response.send_message(f"**{target.display_name}** has not sweared yet. What an angel!")
        else:
            await interaction.response.send_message(f"**{target.display_name}** has swear {count} times.")
    
    @nextcord.slash_command(name="resetswears")
    @commands.has_permissions(manage_messages=True)
    async def reset_swears(self, interaction, member: nextcord.Member):
        await self.reset_swear_count(member.id, interaction.guild.id)
        await interaction.response.send_message(f"Reset swear count for **{member.display_name}**.")
    
    @nextcord.slash_command(name="topswearers")
    async def top_swearers(self, interaction, limit: int = 5):
        await self.db_ready.wait()
        if limit < 1:
            await interaction.response.send_message("Please provide a positive number.")
            return
            
        if limit > 25:
            limit = 25
            
        try:
            async with db_handler.pg_pool.acquire() as conn:
                records = await conn.fetch("""
                    SELECT user_id, count FROM swear_jar
                    WHERE guild_id = $1
                    ORDER BY count DESC
                    LIMIT $2
                """, interaction.guild.id, limit)
                
            if not records:
                await interaction.response.send_message("No one has sweared in this server yet!")
                return
                
            response = "**Top Swearers:**\n"
            for i, record in enumerate(records, 1):
                user = interaction.guild.get_member(record['user_id'])
                name = user.display_name if user else f"Unknown User ({record['user_id']})"
                response += f"{i}. **{name}**: {record['count']} times\n"
                
            await interaction.response.send_message(response)
        except Exception as e:
            print(f"Error getting top swearers: {e}")
            await interaction.response.send_message("Error getting top swearers.")


def setup(bot):
    bot.add_cog(SwearJar(bot))
    