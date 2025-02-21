import nextcord
from nextcord.ext import commands


class Premium(commands.Cog):
    """Premium features management"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='premium', invoke_without_command=True)
    async def premium(self, ctx):
        """Show premium information and status"""
        is_premium = await self.bot.premium_manager.is_premium(ctx.author.id)

        embed = nextcord.Embed(
            title="Premium Features",
            color=nextcord.Color.gold() if is_premium else nextcord.Color.blue()
        )

        if is_premium:
            async with self.bot.db_handler.pg_pool.acquire() as conn:
                data = await conn.fetchrow(
                    "SELECT premium_expiry FROM user_data WHERE user_id = $1",
                    ctx.author.id
                )
                expiry_date = data['premium_expiry'] if data else None

            embed.description = "Thank you for being a premium user! 🌟"
            if expiry_date:
                embed.add_field(
                    name="Premium Status",
                    value=f"Active until {expiry_date.strftime('%Y-%m-%d')}"
                )
        else:
            embed.description = (
                "Unlock exclusive features with Premium!\n\n"
                "**Premium Features:**\n"
                "• AI Art Generation (!ai_art)\n"
                "• Advanced Questions (!question)\n"
                "• More features coming soon!\n\n"
                "Contact Starlo for premium access."
            )

        await ctx.send(embed=embed)

    @premium.command(name="add")
    @commands.has_permissions(administrator=True)
    async def add_premium(self, ctx, user: nextcord.User, days: int = 30):
        """Add a user to premium status"""
        try:
            success = await self.bot.premium_manager.add_premium(user.id, days)

            if success:
                embed = nextcord.Embed(
                    title="Premium Status Added",
                    description=f"{user.mention} has been granted premium status for {days} days!",
                    color=nextcord.Color.green()
                )

                # Send DM to user
                try:
                    user_embed = nextcord.Embed(
                        title="Premium Status Activated! 🌟",
                        description=(
                            f"**You've been granted premium status for {days} days!**\n"
                            "**You now have access to all premium features.**"
                        ),
                        color=nextcord.Color.gold()
                    )
                    await user.send(embed=user_embed)
                except:
                    embed.add_field(
                        name="Note",
                        value="Could not send DM to user"
                    )
            else:
                embed = nextcord.Embed(
                    title="Error",
                    description="Failed to add premium status",
                    color=nextcord.Color.red()
                )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @premium.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def remove_premium(self, ctx, user: nextcord.User):
        """Remove premium status from a user"""
        try:
            async with self.bot.db_handler.pg_pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE user_data 
                    SET premium_user = FALSE, premium_expiry = NULL 
                    WHERE user_id = $1
                    """,
                    user.id
                )

            embed = nextcord.Embed(
                title="Premium Status Removed",
                description=f"Premium status has been removed from {user.mention}",
                color=nextcord.Color.orange()
            )

            # Send DM to user
            try:
                user_embed = nextcord.Embed(
                    title="Premium Status Update",
                    description="Your premium status has been removed.",
                    color=nextcord.Color.orange()
                )
                await user.send(embed=user_embed)
            except:
                embed.add_field(
                    name="Note",
                    value="Could not send DM to user"
                )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @premium.command(name="list")
    @commands.has_permissions(administrator=True)
    async def list_premium(self, ctx):
        """List all premium users"""
        async with self.bot.db_handler.pg_pool.acquire() as conn:
            records = await conn.fetch(
                """
                SELECT user_id, premium_expiry 
                FROM user_data 
                WHERE premium_user = TRUE
                """
            )

        embed = nextcord.Embed(
            title="Premium Users",
            color=nextcord.Color.gold()
        )

        if not records:
            embed.description = "No premium users found"
        else:
            for record in records:
                user = self.bot.get_user(record['user_id'])
                expiry = record['premium_expiry']
                expiry_str = expiry.strftime('%Y-%m-%d') if expiry else 'No expiry'

                embed.add_field(
                    name=str(user) if user else f"User ID: {record['user_id']}",
                    value=f"Expires: {expiry_str}",
                    inline=False
                )

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Premium(bot))
