import nextcord
from epicstore_api import EpicGamesStoreAPI, EGSProductType
from nextcord.ext import commands


class EpicGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = EpicGamesStoreAPI()

    @commands.command(name="epicgames", help="Search Games in Epic Games!")
    async def search_epic_games(self, ctx, *, game_name: str):
        await ctx.trigger_typing()
        try:
            response = self.api.fetch_store_games(
                keywords=game_name,
                product_type=EGSProductType.PRODUCT_GAME,
                count=1,
                sort_by='releaseDate',
                sort_dir='DESC'
            )

            if not response['data']['Catalog']['searchStore']['elements']:
                await ctx.send("❌ No game found!")
                return

            game = response['data']['Catalog']['searchStore']['elements'][0]
            title = game.get('title', 'Unknown Title')
            description = game.get('description', 'No description available.')
            price_info = game.get('price', {})
            price = price_info.get('totalPrice', {}).get('fmtPrice', {}).get('originalPrice', 'Free')
            release_date = game.get('releaseDate', 'Unknown Release Date')
            image_url = game.get('keyImages', [{}])[0].get('url', '')

            embed = nextcord.Embed(
                title=title,
                description=description,
                color=nextcord.Color.dark_theme()
            )
            embed.add_field(name="💰 Price", value=price, inline=True)
            embed.add_field(name="📅 Release Date", value=release_date, inline=True)
            if image_url:
                embed.set_thumbnail(url=image_url)

            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)}")


def setup(bot):
    bot.add_cog(EpicGames(bot))
