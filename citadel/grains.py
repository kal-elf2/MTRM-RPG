import discord
from images.urls import generate_urls
from resources.item import Item
from utils import save_player_data, load_player_data
from exemplars.exemplars import Exemplar


class HarvestButton(discord.ui.View):
    def __init__(self, ctx, crop):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.crop = crop

    @discord.ui.button(label="Harvest", custom_id="harvest", style=discord.ButtonStyle.blurple)
    async def harvest(self, button, interaction):
        author_id = str(interaction.user.id)
        guild_id = self.ctx.guild.id

        player_data = load_player_data(guild_id)
        player = Exemplar(
            player_data[author_id]["exemplar"],
            player_data[author_id]["stats"],
            player_data[author_id]["inventory"]
        )

        # Add 1 of the crop (either Wheat or Flax) to player's inventory
        crop_item = Item(name=self.crop)
        player.inventory.add_item_to_inventory(crop_item, amount=1)

        save_player_data(guild_id, player_data)

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


