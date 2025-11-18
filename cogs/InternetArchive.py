import nextcord
from nextcord.ext import commands
from nextcord import Embed
import aiohttp
from datetime import datetime
from urllib.parse import quote
from requests import session


async def display_archive_item(interaction: nextcord.Interaction, metadata, identifier):
    meta = metadata.get("metadata", {})
    files = metadata.get("files", [])
    
    title = meta.get("title", "Unknown Title")
    if isinstance(title, list):
        title = title[0]
        
    description = meta.get("description", "No description available")
    if isinstance(description, list):
        description = description[0]
        
    if len(description) > 500:
        description = description[:497] + "..."
        
    date = meta.get("date", meta.get("publicdate", "Unknown"))
    if isinstance(date, list):
        date = date[0]
        
    mediatype = meta.get("mediatype", "unknown")
    creator = meta.get("creator", "Unknown")
    if isinstance(creator, list):
        creator = ", ".join(creator[:3])
        
    subject = meta.get("subject", [])
    if isinstance(subject, str):
        subject = [subject]
    subjects_str = ", ".join(subject[:5]) if subject else "N/A"
    
    embed = Embed(
        title=f"📚 {title[:256]}",
        description=description,
        color=0x0066cc,
        url=f"https://archive.org/details/{identifier}"
    )
    
    embed.add_field(name="📆 Date", value=date, inline=True)
    embed.add_field(name="📂 Media Type", value=mediatype.capitalize(), inline=True)
    embed.add_field(name="👤 Creator", value=creator[:100], inline=True)
    
    if subjects_str != "N/A":
        embed.add_field(name="🏷️ Tags", value=subjects_str[:1024], inline=False)
        
    embed.add_field(
        name="🔗 View it on Internet Archive:",
        value=f"[Click Here!](https://archive.org/details/{identifier})",
        inline=False
    )
    
    thumbnail_url = None
    
    thumbnail_url = f"https://archive.org/services/img/{identifier}"
    
    image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    for file in files:
        file_name = file.get("name", "").lower()
        if any(file_name.endswith(ext) for ext in image_extensions):
            if "thumb" in file_name or "cover" in file_name or "preview" in file_name:
                thumbnail_url = f"https://archive.org/download/{identifier}/{file.get('name')}"
                break
            
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
        
    embed.set_footer(
        text=f"Identifier: {identifier}",
        icon_url="https://archive.org/images/glogo.png"
    )
    
    try:
        if date and date != "Unknown":
            for fmt in ["%Y-%m-%d", "%Y-%m", "%Y", "%Y-%m-%dT%H:%M:%SZ"]:
                try:
                    dt = datetime.strptime(date.split("T")[0] if "T" in date else date, fmt)
                    embed.timestamp = dt
                    break
                except:
                    continue
    except:
        pass
    
    await interaction.response.send_message(embed=embed)


class InternetArchive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="archive", description="searches through internet archive and displays metadata")
    async def search_archive(interaction: nextcord.Interaction, *, query: str):
        try:
            search_url = f"https://archive.org/advancedsearch.php?q={quote(query)}&fl[]=identifier,title,description,date,mediatype,creator,subject&sort[]=downloads+desc&rows=1&page=1&output=json"
            
            await interaction.response.send_message(f"🔎 Searching Internet Archive for: **{query}**...")
            
            async with session.get(search_url) as response:
                data = await response.json()
                docs = data.get("response", {}).get("docs", [])
                
                if not docs:
                    await interaction.response.send_message("❌ No results found.")
                    return

                item = docs[0]
                identifier = item.get("identifier")

                metadata_url = f"https://archive.org/metadata/{identifier}"
                async with session.get(metadata_url) as meta_response:
                    if meta_response.status == 200:
                        metadata = await meta_response.json()
                        await display_archive_item(interaction, metadata, identifier)
                    else:
                        await interaction.response.send_message(f"❌ Search error: {response.status}")
                        
        except Exception as e:
            await interaction.response.send_message(f"🛑 An error occurred: {e}")
            
    @nextcord.slash_command(name="archiveid", description="Gets the IA item by identifier.")
    async def archive_by_id(interaction: nextcord.Interaction, identifier: str):
        """Usage: !archiveid <identifier>"""
        async with aiohttp.ClientSession() as session:
            try:
                await interaction.response.send_message(f"📦 Fetching item: **{identifier}**...")
                
                metadata_url = f"https://archive.org/metadata/{identifier}"
                async with session.get(metadata_url) as response:
                    if response.status == 200:
                        metadata = await response.json()
                        
                        if metadata.get("is_dark") or not metadata.get("metadata"):
                            await interaction.response.send_message(f"❌ Item not found or not available: **{identifier}**")
                            return
                        
                        await display_archive_item(interaction, metadata, identifier)
                    else:
                        await interaction.response.send_message(f"❌ **Error fetching item:** {response.status}")
                        
            except Exception as e:
                await interaction.response.send_message(f"❌ **An error occurred:** {str(e)}")


def setup(bot):
    bot.add_cog(InternetArchive(bot))
