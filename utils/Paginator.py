import nextcord
from nextcord.ui import View, Button
import asyncio

class Paginator(View):
    def __init__(self, ctx, embeds, timeout=60.0):
        """
        Initialize the paginator with embeds and context
        
        Parameters:
        -----------
        ctx: nextcord.Context
            The context of the command
        embeds: List[nextcord.Embed]
            List of embeds to paginate through
        timeout: float
            How long the paginator should timeout after inactivity
        """
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.embeds = embeds
        self.current_page = 0
        self.message = None
        
        for embed in self.embeds:
            if embed.color is None:
                embed.color = 0x5865F2
        
        self._update_embeds()
        
        self.add_buttons()
    
    def _update_embeds(self):
        """Update all embeds with page numbers in the footer"""
        for i, embed in enumerate(self.embeds):
            embed.set_footer(text=f"Page {i+1}/{len(self.embeds)}")
    
    def add_buttons(self):
        first_button = Button(emoji="⏮️", style=nextcord.ButtonStyle.blurple)
        first_button.callback = self.first_page
        self.add_item(first_button)
  
        prev_button = Button(emoji="◀️", style=nextcord.ButtonStyle.blurple)
        prev_button.callback = self.prev_page
        self.add_item(prev_button)

        stop_button = Button(emoji="⏹️", style=nextcord.ButtonStyle.red)
        stop_button.callback = self.stop_interaction
        self.add_item(stop_button)

        next_button = Button(emoji="▶️", style=nextcord.ButtonStyle.blurple)
        next_button.callback = self.next_page
        self.add_item(next_button)
        
        last_button = Button(emoji="⏭️", style=nextcord.ButtonStyle.blurple)
        last_button.callback = self.last_page
        self.add_item(last_button)
    
    async def interaction_check(self, interaction):
        """Check if the user interacting is the command invoker"""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("You can't use these buttons as they weren't invoked by you!", ephemeral=True)
            return False
        return True
    
    async def on_timeout(self):
        """Disable all buttons when the view times out"""
        for item in self.children:
            item.disabled = True
        
        if self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass
    
    async def first_page(self, interaction):
        """Go to the first page"""
        self.current_page = 0
        await interaction.response.edit_message(embed=self.embeds[self.current_page])
    
    async def prev_page(self, interaction):
        """Go to the previous page, or the last page if on the first page"""
        if self.current_page == 0:
            self.current_page = len(self.embeds) - 1
        else:
            self.current_page -= 1
        await interaction.response.edit_message(embed=self.embeds[self.current_page])
    
    async def stop_interaction(self, interaction):
        """Stop the paginator and remove all buttons"""
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(view=self)
        self.stop()
    
    async def next_page(self, interaction):
        """Go to the next page, or the first page if on the last page"""
        if self.current_page == len(self.embeds) - 1:
            self.current_page = 0
        else:
            self.current_page += 1
        await interaction.response.edit_message(embed=self.embeds[self.current_page])
    
    async def last_page(self, interaction):
        """Go to the last page"""
        self.current_page = len(self.embeds) - 1
        await interaction.response.edit_message(embed=self.embeds[self.current_page])
    
    async def start(self, channel=None):
        """
        Start the paginator
        
        Parameters:
        -----------
        channel: Optional[nextcord.TextChannel]
            The channel to send the paginator to, defaults to the context channel
        
        Returns:
        --------
        nextcord.Message
            The message containing the paginator
        """
        if not channel:
            channel = self.ctx.channel
        
        self.message = await channel.send(embed=self.embeds[self.current_page], view=self)
        return self.message
      
async def create_paginated_embed(ctx, items, title, description, items_per_page=10, color=0x5865F2):
    """
    Create paginated embeds from a list of items
    
    Parameters:
    -----------
    ctx: nextcord.Context
        The context of the command
    items: List[str]
        List of items to paginate
    title: str
        Title for the embeds
    description: str
        Description for the embeds
    items_per_page: int
        Number of items per page
    color: int
        Color for the embeds
        
    Returns:
    --------
    None
    """
    pages = [items[i:i + items_per_page] for i in range(0, len(items), items_per_page)]
    embeds = []
    
    for i, page in enumerate(pages):
        embed = nextcord.Embed(title=title, description=description, color=color)
        for item in page:
            embed.add_field(name=f"{item}", value="", inline=False)
        embeds.append(embed)
    
    if not embeds:
        embed = nextcord.Embed(title=title, description=description, color=color)
        embed.add_field(name="No items found", value="There are no items to display.", inline=False)
        embeds.append(embed)
    
    paginator = Paginator(ctx, embeds)
    await paginator.start()
  
