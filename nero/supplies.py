import discord
from utils import save_player_data, CommonResponses
from emojis import get_emoji

class DepositButton(discord.ui.Button, CommonResponses):
    def __init__(self, emoji, item_name, amount, player, player_data, author_id, style, disabled=False):
        super().__init__(style=style, label=f"x {amount}", emoji=emoji, disabled=disabled)
        self.item_name = item_name
        self.amount = amount
        self.player = player
        self.player_data = player_data
        self.author_id = author_id

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Update shipwreck quantities
        current_amount = self.player_data.get('shipwreck', {}).get(self.item_name, 0)
        self.player_data['shipwreck'][self.item_name] = current_amount + self.amount
        save_player_data(interaction.guild.id, self.author_id, self.player_data)

        # Fetch updated counts from shipwreck and inventory
        poplar_count_shipwreck = self.player_data['shipwreck'].get('poplar_strip', 0)
        cannonball_count_shipwreck = self.player_data['shipwreck'].get('cannonball', 0)
        poplar_count_inventory = self.player.inventory.get_item_quantity('Poplar Strip')
        cannonball_count_inventory = self.player.inventory.get_item_quantity('Cannonball')

        # Create embed with updated counts, showing both inventory and shipwreck quantities
        embed = discord.Embed(
            title="Supplies Updated",
            description=(
                f"{get_emoji('Poplar Strip')} **Poplar Strips:** {poplar_count_inventory} in inventory, {poplar_count_shipwreck} deposited\n"
                f"{get_emoji('Cannonball')} **Cannonballs:** {cannonball_count_inventory} in inventory, {cannonball_count_shipwreck} deposited"
            ),
            color=discord.Color.blue()
        )

        # Update the view with potentially modified buttons, if necessary
        view = self.view
        for item in view.children:
            if isinstance(item, DepositButton):
                item_quantity = self.player.inventory.get_item_quantity(item.item_name)
                shipwreck_quantity = self.player_data['shipwreck'].get(item.item_name, 0)
                zone_level = self.player.stats.zone_level
                required_amount = 25 * zone_level

                # Dynamically update button states based on inventory and shipwreck counts
                item.disabled = item_quantity < item.amount or (
                            shipwreck_quantity + item.amount > required_amount and zone_level < 5)

        await interaction.response.edit_message(embed=embed, view=view)