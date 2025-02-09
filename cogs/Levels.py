import nextcord
from nextcord.ext import commands
import random
from typing import Optional

class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_cooldown = commands.CooldownMapping.from_cooldown(1, 60, commands.BucketType.user)

    async def update_experience(self, user_id: int, guild_id: int) -> None:
        try:
            async with self.bot.pg_pool.acquire() as conn:
                # Get current level data
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
                    return

                # Calculate XP gain (random between 15-25)
                xp_gain = random.randint(15, 25)
                new_xp = data['xp'] + xp_gain
                current_level = data['level']
                
                # Calculate level up (level * 100 XP needed)
                xp_needed = current_level * 100
                
                if new_xp >= xp_needed:
                    new_level = current_level + 1
                    # Update database with new level and reset XP
                    await conn.execute(
                        """
                        UPDATE user_levels 
                        SET level = $1, xp = 0
                        WHERE user_id = $2 AND guild_id = $3
                        """,
                        new_level, user_id, guild_id
                    )
                    return True
                else:
                    # Just update XP
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

    @nextcord.slash_command(
        name="level",
        description="Check your current level!",
        guild_ids=[1237746712291049483]
    )
    async def level(self, interaction: nextcord.Interaction, member: Optional[nextcord.Member] = None):
        member = member or interaction.user
        try:
            async with self.bot.pg_pool.acquire() as conn:
                data = await conn.fetchrow(
                    """
                    SELECT level, xp FROM user_levels 
                    WHERE user_id = $1 AND guild_id = $2
                    """,
                    member.id, interaction.guild_id
                )

                if not data:
                    await interaction.response.send_message(f"{member.mention} hasn't earned any XP yet!")
                    return

                embed = nextcord.Embed(
                    title=f"{member.name}'s Level Stats",
                    color=nextcord.Color.blue()
                )
                embed.add_field(name="Level", value=str(data['level']))
                embed.add_field(name="XP", value=f"{data['xp']}/{data['level'] * 100}")
                embed.set_thumbnail(url=member.display_avatar.url)
                
                await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message("Error retrieving level data.")

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot or not message.guild:
            return

        # Check cooldown
        bucket = self.xp_cooldown.get_bucket(message)
        if bucket.update_rate_limit():
            return

        # Only process messages in non-NSFW channels
        if not message.channel.is_nsfw():
            leveled_up = await self.update_experience(message.author.id, message.guild.id)
            if leveled_up:
                await message.channel.send(f"🎉 Congratulations {message.author.mention}, you've leveled up!")

def setup(bot):
    bot.add_cog(Level(bot))