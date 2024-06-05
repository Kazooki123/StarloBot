import nextcord
from nextcord.ext import commands
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import bot_intents

bot = commands.Bot(intents=bot_intents())

async def get_level_channel(guild_id):
    async with bot.pg_pool.acquire() as connection:
        record = await connection.fetchrow('SELECT level_channel_id FROM settings WHERE guild_id = $1', guild_id)
        return record['level_channel_id'] if record else None

async def update_experience(user_id, guild_id):
    async with bot.pg_pool.acquire() as connection:
        user_data = await connection.fetchrow('SELECT experience, level FROM user_data WHERE user_id = $1', user_id)
        
        if user_data is None:
            await connection.execute(
                'INSERT INTO user_data (user_id, experience, level) VALUES ($1, $2, $3)',
                user_id, 0, 1
            )
            experience = 0
            level = 1
        else:
            experience = user_data['experience'] if user_data['experience'] is not None else 0
            level = user_data['level'] if user_data['level'] is not None else 1
        
        experience += 20  # Increment experience by 20, adjust as needed
        new_level = level
        
        while experience >= 50 * (new_level ** 2):
            experience -= 50 * (new_level ** 2)
            new_level += 1
        
        await connection.execute(
            'UPDATE user_data SET experience = $1, level = $2 WHERE user_id = $3',
            experience, new_level, user_id
        )
    
    if new_level > level:
        user = await bot.fetch_user(user_id)
        level_channel_id = await get_level_channel(guild_id)
        if level_channel_id:
            level_channel = bot.get_channel(level_channel_id)
            if level_channel:
                await level_channel.send(f"{user.mention} is now level {new_level}!")


class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="rank")
    async def rank(self, ctx: nextcord.Interaction):
        user_id = ctx.author.id
        async with self.bot.pg_pool.acquire() as connection:
            record = await connection.fetchrow('SELECT level FROM user_data WHERE user_id = $1', user_id)
            if record:
                level = record['level']
                await ctx.send(f"{ctx.author.mention}, you're level {level}!")
            else:
                await ctx.send("You don't have a level yet.")

    @nextcord.slash_command(name="leaderboard")
    async def leaderboard(self, ctx: nextcord.Interaction, type: str):
        if type.lower() not in ["money", "level"]:
            await ctx.send("Invalid type! Please use '/leaderboard money' or '/leaderboard level'.")
            return

        async with self.bot.pg_pool.acquire() as connection:
            if type.lower() == "money":
                query = 'SELECT user_id, wallet FROM user_data ORDER BY wallet DESC LIMIT 10'
            else:
                query = 'SELECT user_id, level FROM user_data ORDER BY level DESC LIMIT 10'
            
            records = await connection.fetch(query)

        if not records:
            await ctx.send("No data available for the leaderboard.")
            return

        embed = nextcord.Embed(title=f"Top 10 Users by {type.capitalize()}", color=nextcord.Color.blue())
        
        for i, record in enumerate(records):
            user_id = record['user_id']
            value = record['wallet'] if type.lower() == "money" else record['level']
            user = await self.bot.fetch_user(user_id)
            medal = ""
            if i == 0:
                medal = "🥇"
            elif i == 1:
                medal = "🥈"
            elif i == 2:
                medal = "🥉"
            embed.add_field(name=f"{medal} {user}", value=f"{type.capitalize()}: {value}", inline=False)

        await ctx.send(embed=embed)
        
    @nextcord.slash_command(name="channellevel", description="Admin Only: Sets a level announcement into a specific channel.")
    @commands.has_permissions(administrator=True)
    async def channellevel(self, ctx: nextcord.Interaction):
        channel_id = ctx.channel.id
        guild_id = ctx.guild.id
    
        async with bot.pg_pool.acquire() as connection:
            await connection.execute(
                'INSERT INTO settings (guild_id, level_channel_id) VALUES ($1, $2) ON CONFLICT (guild_id) DO    UPDATE SET level_channel_id = $2',
                guild_id, channel_id
            )
    
        await ctx.send(f"Level-up announcements will now be sent in this channel: {ctx.channel.mention}")
        
    @bot.event
    async def on_message(message):
        if message.author.bot:
            return

        public_channels = [channel.id for channel in message.guild.text_channels if not channel.is_nsfw()]
        if message.channel.id in public_channels:
            await update_experience(message.author.id, message.guild.id)
    
        await bot.process_commands(message)

def setup(bot):
    bot.add_cog(Level(bot))