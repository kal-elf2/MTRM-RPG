import discord
from utils import save_player_data
from emojis import get_emoji
class RepairView(discord.ui.View):
    def __init__(self, battle_commands):
        super().__init__()
        self.battle_commands = battle_commands

        ship = self.battle_commands.ship

        # Create repair buttons for each ship part
        self.mast_button = RepairButton("Mast", ship.get_health("Mast"), ship.mast_max_health, battle_commands)
        self.hull_button = RepairButton("Hull", ship.get_health("Hull"), ship.hull_max_health, battle_commands)
        self.helm_button = RepairButton("Helm", ship.get_health("Helm"), ship.helm_max_health, battle_commands)

        # Add buttons to the view
        self.add_item(self.mast_button)
        self.add_item(self.hull_button)
        self.add_item(self.helm_button)

class RepairButton(discord.ui.Button):
    def __init__(self, part, current_health, max_health, battle_commands):
        label = f"{part}: {current_health}/{max_health}"
        super().__init__(style=discord.ButtonStyle.secondary, label=label, disabled=current_health >= max_health)
        self.part = part
        self.battle_commands = battle_commands

    async def callback(self, interaction: discord.Interaction):
        player_data = self.battle_commands.player_data

        if player_data['shipwreck'].get('Poplar Strip', 0) > 0:
            player_data['shipwreck']['Poplar Strip'] -= 1
            current_health = self.battle_commands.ship.get_health(self.part)
            max_health = self.battle_commands.ship.__dict__[self.part + '_max_health']
            self.battle_commands.ship.repair(self.part, 1)

            # Update the button label and enable/disable state
            self.label = f"{self.part}: {current_health}/{max_health}"
            self.disabled = current_health >= max_health

            # Update the player data and battle embed to reflect changes
            save_player_data(interaction.guild_id, str(interaction.user.id), player_data)
            await interaction.response.edit_message(embed=self.battle_commands.create_battle_embed(player_data), view=self.battle_commands.repair_view)
        else:
            # Notify the user that they have no Poplar Strips left
            await interaction.response.send_message("Ye be out of Poplar Strips! Unable to repair the ship.", ephemeral=True)
