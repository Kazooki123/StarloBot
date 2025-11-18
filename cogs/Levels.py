import nextcord
from nextcord.ext import commands
import random
from typing import Optional
from utils.DbHandler import db_handler

class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_cooldown = commands.CooldownMapping.from_cooldown(1, 60, commands.BucketType.user)
        self._cd = commands.CooldownMapping.from_cooldown(1, 60, commands.BucketType.member)

    async def update_experience(self, user_id: int, guild_id: int) -> bool:
        """
        Update user experience and handle level ups.
        Returns True if user leveled up, False otherwise.
        """
        try:
            async with self.bot.pg_pool.acquire() as conn:
                # Check if user exists in database
                data = await conn.fetchrow(
                    """
                    SELECT * FROM user_levels 
                    WHERE user_id = $1 AND guild_id = $2
                    """, 
                    user_id, guild_id
                )

                if not data:
                    # Create new user entry
                    await conn.execute(
                        """
                        INSERT INTO user_levels (user_id, guild_id, xp, level)
                        VALUES ($1, $2, 0, 1)
                        """,
                        user_id, guild_id
                    )
                    return False

                # Calculate XP gain (random between 15-25)
                xp_gain = random.randint(15, 25)
                new_xp = data['xp'] + xp_gain
                current_level = data['level']
                
                # Calculate level up (level * 100 XP needed)
                xp_needed = current_level * 100
                
                if new_xp >= xp_needed:
                    await conn.execute(
                        """
                        UPDATE user_levels 
                        SET level = $1, xp = 0
                        WHERE user_id = $2 AND guild_id = $3
                        """,
                        current_level + 1, user_id, guild_id
                    )
                    return True
                else:
                    await conn.execute(
                        """
                        UPDATE user_levels 
                        SET xp = $1
                        WHERE user_id = $2 AND guild_id = $3
                        """,
                        new_xp, user_id, guild_id
                    )
                    return False

        except Exception as e:
            print(f"Error updating experience: {e}")
            return False

    @nextcord.slash_command(name="level", description="Shows your current level in the server")
    @commands.guild_only()
    async def level(self, interaction, member: Optional[nextcord.Member] = None):
        """Check your or another member's level"""
        member = member or interaction.author

        try:
            async with self.bot.pg_pool.acquire() as conn:
                data = await conn.fetchrow(
                    """
                    SELECT level, xp FROM user_levels 
                    WHERE user_id = $1 AND guild_id = $2
                    """,
                    member.id, interaction.guild.id
                )

                if not data:
                    await conn.execute(
                        """
                        INSERT INTO user_levels (user_id, guild_id, xp, level)
                        VALUES ($1, $2, 0, 1)
                        """,
                        member.id, interaction.guild.id
                    )
                    data = {'level': 1, 'xp': 0}

                embed = nextcord.Embed(
                    title=f"{member.name}'s Level Stats",
                    color=0xffffff
                )
                embed.add_field(name="Level", value=str(data['level']), inline=True)
                embed.add_field(
                    name="XP Progress", 
                    value=f"{data['xp']}/{data['level'] * 100}", 
                    inline=True
                )
                
                # Add progress bar
                progress = data['xp'] / (data['level'] * 100)
                progress_bar = "█" * int(progress * 10) + "░" * (10 - int(progress * 10))
                embed.add_field(
                    name="Progress", 
                    value=f"`{progress_bar}` {int(progress * 100)}%", 
                    inline=False
                )
                
                if member.display_avatar:
                    embed.set_thumbnail(url=member.display_avatar.url)
                
                await interaction.response.send_message(embed=embed)

        except Exception as e:
            print(f"Error retrieving level data: {e}")
            await interaction.response.send_message("There was an error retrieving the level data.")

    @nextcord.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        """Handle XP gain from messages"""
        if message.author.bot or not message.guild:
            return

        # Ignore command messages
        if message.content.startswith(self.bot.command_prefix):
            return

        # Check cooldown using user bucket
        bucket = self.xp_cooldown._buckets.get(message.author.id)
        if bucket is None:
            bucket = self.xp_cooldown._buckets[message.author.id] = self.xp_cooldown._cooldown.copy()
        
        retry_after = bucket.update_rate_limit()
        if retry_after:
            return

        if not message.channel.is_nsfw():
            try:
                leveled_up = await self.update_experience(message.author.id, message.guild.id)
                if leveled_up:
                    async with self.bot.pg_pool.acquire() as conn:
                        data = await conn.fetchrow(
                            """
                            SELECT level FROM user_levels 
                            WHERE user_id = $1 AND guild_id = $2
                            """,
                            message.author.id, message.guild.id
                        )
                        
                        embed = nextcord.Embed(
                            title="Level Up! 🎉",
                            description=f"Congratulations {message.author.mention}, you've reached level {data['level']}!",
                            color=nextcord.Color.green()
                        )
                        
                        if message.author.display_avatar:
                            embed.set_thumbnail(url=message.author.display_avatar.url)
                            
                        await message.channel.send(embed=embed)
            except Exception as e:
                print(f"Error in on_message XP handling: {e}")


def setup(bot):
    if not hasattr(bot, 'db_handler'):
        from utils.DbHandler import db_handler
        bot.db_handler = db_handler

    bot.add_cog(Level(bot))
