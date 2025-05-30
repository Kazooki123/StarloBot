import nextcord
from nextcord.ext import commands
from nextcord.ui import Button, View


async def get_user_balance(self, user_id):
    async with self.bot.pg_pool.acquire() as connection:
        result = await connection.fetchrow(
            """
            SELECT wallet FROM user_data WHERE user_id = $1;
            """, user_id
        )
    return result['wallet'] if result else 0

async def update_user_balance(self, user_id, amount):
    async with self.bot.pg_pool.acquire() as connection:
        await connection.execute(
            """
            UPDATE user_data 
            SET wallet = wallet + $1
            WHERE user_id = $2
            """, amount, user_id
        )

class MoneyRequestView(View):
    def __init__(self, sender_id, recipient_id, amount, bot):
        super().__init__(timeout=None)
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.amount = amount
        self.bot = bot

    @nextcord.ui.button(label="Accept✅", style=nextcord.ButtonStyle.success)
    async def accept_callback(self, ctx, button: nextcord.ui.Button):
        if ctx.user.id != self.recipient_id:
            await ctx.send("You are not the intended recipient of this request.")
            return

        # Update database
        await update_user_balance(self.recipient_id, -self.amount)
        await update_user_balance(self.sender_id, self.amount)

        await ctx.send(f"Request accepted. {self.amount}🪙 has been transferred to {ctx.guild.get_member(self.sender_id).mention}.")
        await ctx.message.delete()

    @nextcord.ui.button(label="Deny❌", style=nextcord.ButtonStyle.danger)
    async def deny_callback(self, ctx, button: nextcord.ui.Button):
        if ctx.user.id != self.recipient_id:
            await ctx.send("You are not the intended recipient of this request.")
            return

        await ctx.send(f"Request denied. {self.amount}🪙 was not transferred.")
        await ctx.message.delete()


class Requests(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="request")
    async def request(self, ctx, recipient: nextcord.User, amount: int):
        sender_id = ctx.author.id
        recipient_id = recipient.id

        # Check if the sender has enough balance
        sender_balance = await get_user_balance(sender_id)
        if sender_balance < amount:
            await ctx.send("You do not have enough balance to make this request.")
            return

        embed = nextcord.Embed(
            title="Money Request",
            description=f"{ctx.author.mention} wants to send a request of {amount}🪙 to {recipient.mention}",
            color=nextcord.Color.green()
        )

        view = MoneyRequestView(sender_id, recipient_id, amount, self.bot)

        try:
            await recipient.send(embed=embed, view=view)
            await ctx.send(f"Request sent to {recipient.mention} successfully.")
        except nextcord.Forbidden:
            await ctx.send(f"Failed to send a request. {recipient.mention} has DMs disabled.")


def setup(bot):
    bot.add_cog(Requests(bot))
