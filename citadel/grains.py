import discord
from images.urls import generate_urls
from resources.item import Item
from utils import save_player_data, CommonResponses, refresh_player_from_data
import asyncio


class HarvestButton(discord.ui.View, CommonResponses):
    def __init__(self, ctx, crop, player_data, author_id, guild_id):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.crop = crop
        self.player_data = player_data
        self.author_id = author_id
        self.guild_id = guild_id

    @discord.ui.button(label="Harvest", custom_id="harvest", style=discord.ButtonStyle.blurple)
    async def harvest(self, button: discord.ui.Button, interaction: discord.Interaction):

        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        player, self.player_data = await refresh_player_from_data(self, self.ctx)

        if self.player_data["location"] != "citadel":
            await self.not_in_citadel_response(interaction)
            return

        crop_item = Item(name=self.crop)
        player.inventory.add_item_to_inventory(crop_item, amount=1)
        save_player_data(self.guild_id, self.author_id, self.player_data)

        crop_count = player.inventory.get_item_quantity(self.crop)
        crop_url = generate_urls("Citadel", self.crop)

        embed = discord.Embed(
            title=f"{self.crop} Field",
            description=f"You harvested {self.crop.lower()}!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=crop_url)
        embed.set_footer(text=f"+1 {self.crop}\n{crop_count} in backpack")

        # Disable the button
        button.disabled = True
        # Reflect the button's disabled state in the response
        await interaction.response.edit_message(embed=embed, view=self)

        # Wait for 1.5 seconds
        await asyncio.sleep(1.5)

        # Re-enable the button
        button.disabled = False
        # You might need to update the message again to reflect the re-enabled state
        await interaction.edit_original_response(view=self)