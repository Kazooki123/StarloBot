import os

import nextcord
import requests
from dotenv import load_dotenv
from nextcord.ext import commands

load_dotenv("../.env")
EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY")


class CurrencyConverter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="convert", help="Converts currency!")
    async def convert_currency(self, ctx, amount: float, from_currency: str, to_currency: str):
        """
        Convert currency in real time!
        Usage: !convert 15 usd php
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/latest/{from_currency}"
        response = requests.get(url).json()

        if response["result"] != "success":
            await ctx.send(f"❌ {ctx.author.mention} **Invalid currency code or API error!**")
            return

        if to_currency not in response["conversion_rates"]:
            await ctx.send("❌ **Invalid target currency!**")
            return

        rate = response["conversion_rates"][to_currency]
        converted_amount = round(amount * rate, 2)

        embed = nextcord.Embed(
            title="💱 Currency Converter",
            color=nextcord.Color.green()
        )
        embed.add_field(name="💰 Amount", value=f"{amount} {from_currency}", inline=True)
        embed.add_field(name="➡️ Converted To", value=f"{converted_amount} {to_currency}", inline=True)
        embed.set_footer(text="Exchange rates may vary!")

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(CurrencyConverter(bot))
