import nextcord
from nextcord import Embed, File, Color
from nextcord.ext import commands
import aiohttp
import io


class QRGenerator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="genqr", description="Generate a QR code!")
    async def generate_qr_code(interaction: nextcord.Interaction, *, text: str):
        async with aiohttp.ClientSession() as session:
            try:
                url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={text}"

                async with session.get(url) as response:
                    if response.status == 200:
                        image_data = await response.read()

                        file = File(io.BytesIO(image_data), filename="genqrcode.png")

                        embed = Embed(
                            title="☕️ QR Code Generated",
                            description=f"```{text[:100]}{'...' if len(text) > 100 else ''}```",
                            color=Color.red()
                        )
                        embed.set_image(url="attachment://genqrcode.png")
                        embed.set_footer(text="Scan this QR code with your phone!")

                        await interaction.response.send_message(embed=embed, file=file)
                    else:
                        await interaction.response.send_message(f"❌ **Error generating QR code:** {response.status}")
            except Exception as e:
                await interaction.response.send_message(f"❌ **An error occurred:** {str(e)}")


def setup(bot):
    bot.add_cog(QRGenerator(bot))
