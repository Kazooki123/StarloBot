import os
import io
import aiohttp
import nextcord
from nextcord.ext import commands


class FaceSwapAI(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_endpoint = os.getenv(
            "FACESWAP_API_ENDPOINT", "https://api.piapi.ai/api/faceswap"
        )

    async def _fetch_image_bytes(self, session: aiohttp.ClientSession, url: str) -> bytes:
        """Fetch image bytes from a URL with a timeout and basic validation."""
        async with session.get(url, timeout=20) as resp:
            if resp.status != 200:
                raise ValueError(f"Failed to fetch image: HTTP {resp.status}")
            data = await resp.read()
            if not data:
                raise ValueError("Downloaded image was empty")
            return data

    async def _resolve_attachments_or_args(self, interaction, args) -> list:
        """Return up to 2 image bytes objects from attachments, mentions, or URLs."""
        images = []
        async with aiohttp.ClientSession() as session:
            for att in interaction.message.attachments:
                if len(images) >= 2:
                    break
                # Download attachment
                img_bytes = await att.read()
                images.append(img_bytes)

            if len(images) < 2 and interaction.message.mentions:
                for user in interaction.message.mentions:
                    if len(images) >= 2:
                        break
                    url = user.display_avatar.replace(size=512).url
                    img_bytes = await self._fetch_image_bytes(session, url)
                    images.append(img_bytes)

            if len(images) < 2 and args:
                for a in args:
                    if len(images) >= 2:
                        break
                    if a.startswith("http://") or a.startswith("https://"):
                        try:
                            img_bytes = await self._fetch_image_bytes(session, a)
                            images.append(img_bytes)
                        except Exception:
                            # skip invalid urls
                            continue

        return images

    @nextcord.slash_command(name="faceswap", aliases=["fswap", "swapfaces"])
    @commands.guild_only()
    async def faceswap(self, interaction: nextcord.Interaction, *args: str):
        """Swap faces between two images.

        Usage examples:
        - Attach two images to the command message: `!faceswap` (with 2 images attached)
        - Attach one image and mention a user to use their avatar: `!faceswap @OtherUser`
        - Provide two image URLs: `!faceswap <url1> <url2>`
        """

        # Check API key
        api_key = os.getenv("FACESWAP_API_KEY")
        if not api_key:
            embed = nextcord.Embed(
                title="Configuration error",
                description=(
                    "Face-swap is not configured. Missing environment variable `FACESWAP_API_KEY`."
                ),
                color=nextcord.Color.red(),
            )
            embed.set_footer(text="Ask the server admin to set FACESWAP_API_KEY")
            await interaction.response.send_message(embed=embed)
            return

        # Gather up to two images
        try:
            images = await self._resolve_attachments_or_args(interaction, args)
        except Exception as e:
            embed = nextcord.Embed(
                title="Failed to fetch images",
                description=str(e),
                color=nextcord.Color.red(),
            )
            await interaction.response.send_message(embed=embed)
            return

        if len(images) < 2:
            embed = nextcord.Embed(
                title="Not enough images",
                description=(
                    "I couldn't find two images. Attach two images, or attach one and mention a user, "
                    "or provide two image URLs."
                ),
                color=nextcord.Color.orange(),
            )
            embed.add_field(name="Examples", value="`!faceswap` (2 attachments)\n`!faceswap @user`\n`!faceswap <url1> <url2>`")
            await interaction.response.send_message(embed=embed)
            return

        # Call the external API with multipart form data
        headers = {"x-api-key": api_key}
        files = {
            "image1": images[0],
            "image2": images[1],
        }

        processing_embed = nextcord.Embed(
            title="Processing face-swap",
            description="Uploading images and waiting for the face-swap result...",
            color=nextcord.Color.blurple(),
        )
        processing_msg = await interaction.response.send_message(embed=processing_embed)

        try:
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                # Attach bytes as file-like objects
                data.add_field("image1", io.BytesIO(files["image1"]), filename="image1.jpg", content_type="image/jpeg")
                data.add_field("image2", io.BytesIO(files["image2"]), filename="image2.jpg", content_type="image/jpeg")

                async with session.post(self.api_endpoint, data=data, headers=headers, timeout=120) as resp:
                    text = await resp.text()
                    if resp.status != 200:
                        raise RuntimeError(f"API error: HTTP {resp.status} - {text}")
                    try:
                        result = await resp.json()
                    except Exception:
                        raise RuntimeError(f"Unexpected API response: {text}")

            out_url = None
            for key in ("output_url", "output", "url", "result", "image_url"):
                if isinstance(result, dict) and key in result:
                    out_url = result[key]
                    break

            if not out_url:
                raise RuntimeError(f"API did not return an output URL. Response keys: {', '.join(result.keys() if isinstance(result, dict) else [])}")

            # Fetch the output image
            async with aiohttp.ClientSession() as session:
                async with session.get(out_url, timeout=60) as r2:
                    if r2.status != 200:
                        raise RuntimeError(f"Failed to download result image: HTTP {r2.status}")
                    out_bytes = await r2.read()

            file = nextcord.File(io.BytesIO(out_bytes), filename="faceswap_result.png")

            embed = nextcord.Embed(
                title="Faceswap Result",
                description="Here's the face-swapped image.",
                color=nextcord.Color.green(),
            )
            embed.set_image(url=f"attachment://faceswap_result.png")
            embed.set_footer(text="Powered by PiAPI AI")

            await processing_msg.delete()
            await interaction.response.send_message(embed=embed, file=file)

        except Exception as e:
            try:
                await processing_msg.delete()
            except Exception:
                pass
            embed = nextcord.Embed(
                title="Faceswap Failed!",
                description=str(e),
                color=nextcord.Color.red(),
            )
            embed.add_field(name="Tips", value="Make sure the images are valid and the bot has internet access.")
            await interaction.response.send_message(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(FaceSwapAI(bot))

