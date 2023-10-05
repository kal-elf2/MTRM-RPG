import discord
from images.urls import generate_urls
from resources.item import Item
from utils import save_player_data

class HarvestButton(discord.ui.View):
    def __init__(self, ctx, player, guild_id, player_data):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.player = player
        self.guild_id = guild_id
        self.player_data = player_data

    @discord.ui.button(label="Harvest", custom_id="harvest", style=discord.ButtonStyle.blurple)
    async def harvest(self, button, interaction):

        # Add 1 wheat to player's inventory
        wheat_item = Item(name="Wheat")
        self.player.inventory.add_item_to_inventory(wheat_item, amount=1)

        # After adding wheat to the player's inventory
        self.player_data[str(self.ctx.author.id)]["inventory"] = self.player.inventory.to_dict()
        save_player_data(self.guild_id, self.player_data)

        # Fetch quantity of the wheat in the player's inventory
        wheat_count = self.player.inventory.get_item_quantity("Wheat")

        # Create the embed to reflect the new wheat count
        embed = discord.Embed(
            title="Wheat Field",
            description=f"You harvested wheat!",
            color=discord.Color.green()
        )
        wheat_url = generate_urls("Grains", "Wheat")
        embed.set_thumbnail(url=wheat_url)
        embed.set_footer(text=f"+1 Wheat\n{wheat_count} in backpack")

        await interaction.response.edit_message(embed=embed, view=self)
