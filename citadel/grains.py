import discord
from images.urls import generate_urls
from resources.item import Item
from utils import save_player_data, CommonResponses, refresh_player_from_data


class HarvestButton(discord.ui.View, CommonResponses):
    def __init__(self, ctx, crop, player_data, author_id, guild_id):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.crop = crop
        self.player_data = player_data
        self.author_id = author_id
        self.guild_id = guild_id

    @discord.ui.button(label="Harvest", custom_id="harvest", style=discord.ButtonStyle.blurple)
    async def harvest(self, button, interaction):

        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player object from the latest player data
        player, self.player_data = await refresh_player_from_data(self, self.ctx)

        # Check if the player is not in the citadel
        if self.player_data["location"] != "citadel":
            await self.not_in_citadel_response(interaction)
            return

        # Add 1 of the crop (either Wheat or Flax) to player's inventory
        crop_item = Item(name=self.crop)
        player.inventory.add_item_to_inventory(crop_item, amount=1)

        save_player_data(self.guild_id, self.author_id, self.player_data)

        # Fetch quantity of the crop in the player's inventory
        crop_count = player.inventory.get_item_quantity(self.crop)

        # Create the embed to reflect the new crop count
        embed = discord.Embed(
            title=f"{self.crop} Field",
            description=f"You harvested {self.crop.lower()}!",
            color=discord.Color.green()
        )
        crop_url = generate_urls("Citadel", self.crop)
        embed.set_thumbnail(url=crop_url)
        embed.set_footer(text=f"+1 {self.crop}\n{crop_count} in backpack")

        await interaction.response.edit_message(embed=embed, view=self)