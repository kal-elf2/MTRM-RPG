import discord
from utils import save_player_data
class DepositButton(discord.ui.Button):
    def __init__(self, emoji, item_name, amount, player, player_data, style):
        super().__init__(style=style, label=f"x {amount}", emoji=emoji)
        self.item_name = item_name
        self.amount = amount
        self.player = player
        self.player_data = player_data

    async def callback(self, interaction: discord.Interaction):
        # Remove item from inventory and add to shipwreck
        if self.player.inventory.remove_item(self.item_name, self.amount):
            current_amount = self.player_data['shipwreck'].get(self.item_name, 0)
            self.player_data['shipwreck'][self.item_name] = current_amount + self.amount
            save_player_data(interaction.guild.id, self.player_data)

            response_text = f"Deposited {self.amount} {self.item_name} onto the ship."
            await interaction.response.send_message(response_text)
        else:
            await interaction.response.send_message("Not enough items in inventory.", ephemeral=True)
