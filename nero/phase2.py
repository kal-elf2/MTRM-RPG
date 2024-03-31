import discord
from utils import save_player_data
from emojis import get_emoji
class RepairView(discord.ui.View):
    def __init__(self, battle_commands):
        super().__init__()
        self.battle_commands = battle_commands

    @discord.ui.button(label="Repair Ship", style=discord.ButtonStyle.success, emoji=f"{get_emoji('Poplar Strip')}")
    async def repair_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        player_data = self.battle_commands.player_data

        # Check if there are Poplar Strips available
        if player_data['shipwreck'].get('Poplar Strip', 0) > 0:
            player_data['shipwreck']['Poplar Strip'] -= 1
            # Repair the ship
            self.battle_commands.ship.repair(500)

            # Update the player data and battle embed to reflect changes
            save_player_data(interaction.guild_id, str(interaction.user.id), player_data)
            await interaction.response.edit_message(embed=self.battle_commands.create_battle_embed(player_data), view=self)
        else:
            # Notify the user that they have no Poplar Strips left
            await interaction.response.send_message("Ye be out of Poplar Strips! Unable to repair the ship.", ephemeral=True)
