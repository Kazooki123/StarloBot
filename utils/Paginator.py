import asyncio
import nextcord
from typing import List, Optional, Union


class Paginator:
    """
    A utility class for creating paginated embeds with navigation buttons.
    """

    def __init__(
            self,
            ctx,
            embeds: List[nextcord.Embed],
            timeout: int = 60,
            delete_on_timeout: bool = False
    ):
        self.ctx = ctx
        self.embeds = embeds
        self.timeout = timeout
        self.delete_on_timeout = delete_on_timeout
        self.current_page = 0
        self.total_pages = len(embeds)
        self.message: Optional[nextcord.Message] = None
        self.view: Optional[nextcord.ui.View] = None

    async def send(self, channel: Optional[nextcord.TextChannel] = None):
        """
        Send the paginator to the specified channel or the context channel.

        Args:
            channel: The channel to send the paginator to. If None, uses the context channel.
        """
        if channel is None:
            channel = self.ctx.channel

        self.view = self._create_view()
        embed = self.embeds[self.current_page]

        if not embed.footer.text or "Page" not in embed.footer.text:
            embed.set_footer(text=f"Page {self.current_page + 1}/{self.total_pages}")

        self.message = await channel.send(embed=embed, view=self.view)
        return self.message

    def _create_view(self):
        """Create a view with navigation buttons."""
        view = nextcord.ui.View(timeout=self.timeout)

        first_button = nextcord.ui.Button(
            style=nextcord.ButtonStyle.secondary,
            emoji="⏮️",
            disabled=self.current_page == 0
        )
        first_button.callback = self._first_page
        view.add_item(first_button)

        previous_button = nextcord.ui.Button(
            style=nextcord.ButtonStyle.primary,
            emoji="◀️",
            disabled=self.current_page == 0
        )
        previous_button.callback = self._previous_page
        view.add_item(previous_button)

        page_indicator = nextcord.ui.Button(
            style=nextcord.ButtonStyle.secondary,
            label=f"{self.current_page + 1}/{self.total_pages}",
            disabled=True
        )
        view.add_item(page_indicator)

        next_button = nextcord.ui.Button(
            style=nextcord.ButtonStyle.primary,
            emoji="▶️",
            disabled=self.current_page == self.total_pages - 1
        )
        next_button.callback = self._next_page
        view.add_item(next_button)

        last_button = nextcord.ui.Button(
            style=nextcord.ButtonStyle.secondary,
            emoji="⏭️",
            disabled=self.current_page == self.total_pages - 1
        )
        last_button.callback = self._last_page
        view.add_item(last_button)

        close_button = nextcord.ui.Button(
            style=nextcord.ButtonStyle.danger,
            emoji="❌"
        )
        close_button.callback = self._close
        view.add_item(close_button)

        async def on_timeout():
            try:
                if self.delete_on_timeout and self.message:
                    await self.message.delete()
                else:
                    for item in self.view.children:
                        item.disabled = True
                    if self.message:
                        await self.message.edit(view=self.view)
            except (nextcord.NotFound, nextcord.HTTPException):
                pass

        view.on_timeout = on_timeout
        return view

    async def _first_page(self, interaction: nextcord.Interaction):
        """Go to the first page."""
        await interaction.response.defer()
        self.current_page = 0
        await self._update_message()

    async def _previous_page(self, interaction: nextcord.Interaction):
        """Go to the previous page."""
        try:
            await interaction.response.defer(ephemeral=False)
        except (nextcord.NotFound, nextcord.HTTPException):
            return

        self.current_page = min(self.total_pages - 1, self.current_page + 1)

        try:
            await self._update_message()
        except Exception as e:
            print(f"Error updating message: {e}")

    async def _next_page(self, interaction: nextcord.Interaction):
        """Go to the next page."""
        await interaction.response.defer()
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        await self._update_message()

    async def _last_page(self, interaction: nextcord.Interaction):
        """Go to the last page."""
        await interaction.response.defer()
        self.current_page = self.total_pages - 1
        await self._update_message()

    async def _close(self, interaction: nextcord.Interaction):
        """Close the paginator and delete the message."""
        await interaction.response.defer()
        if self.message:
            await self.message.delete()

    async def _update_message(self):
        """Update the message with the current page."""
        if not self.message:
            return

        self.view = self._create_view()
        embed = self.embeds[self.current_page]

        footer_text = embed.footer.text or ""
        if "Page" not in footer_text:
            embed.set_footer(text=f"Page {self.current_page + 1}/{self.total_pages}")
        else:
            embed.set_footer(text=f"Page {self.current_page + 1}/{self.total_pages}")

        await self.message.edit(embed=embed, view=self.view)
