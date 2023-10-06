import discord
from images.urls import generate_urls
from resources.item import Item
from utils import save_player_data


class HarvestButton(discord.ui.View):
    def __init__(self, ctx, player, guild_id, player_data, crop):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.player = player
        self.guild_id = guild_id
        self.player_data = player_data
        self.crop = crop

    @discord.ui.button(label="Harvest", custom_id="harvest", style=discord.ButtonStyle.blurple)
    async def harvest(self, button, interaction):
        # Add 1 of the crop (either Wheat or Flax) to player's inventory
        crop_item = Item(name=self.crop)
        self.player.inventory.add_item_to_inventory(crop_item, amount=1)

        # After adding crop to the player's inventory
        self.player_data[str(self.ctx.author.id)]["inventory"] = self.player.inventory.to_dict()
        save_player_data(self.guild_id, self.player_data)

        # Fetch quantity of the crop in the player's inventory
        crop_count = self.player.inventory.get_item_quantity(self.crop)

        # Create the embed to reflect the new crop count
        embed = discord.Embed(
            title=f"{self.crop} Field",
            description=f"You harvested {self.crop.lower()}!",
            color=discord.Color.green()
        )
        crop_url = generate_urls("Grains", self.crop)
        embed.set_thumbnail(url=crop_url)
        embed.set_footer(text=f"+1 {self.crop}\n{crop_count} in backpack")

        await interaction.response.edit_message(embed=embed, view=self)


