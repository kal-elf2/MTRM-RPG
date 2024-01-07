import discord
from probabilities import buyback_cost
from utils import save_player_data

class NeroView(discord.ui.View):
    def __init__(self, interaction, player_data, author_id, player, saved_inventory):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.player_data = player_data
        self.author_id = author_id
        self.player = player
        self.saved_inventory = saved_inventory
        self.cost = buyback_cost * self.player.stats.zone_level

    async def handle_buy_back(self):
        player_inventory = self.player.inventory
        player_stats = self.player.stats

        # Check if the player has enough coppers
        if player_inventory.coppers < self.cost:
            return "Arr, ye be short on coppers! Can't make a deal without the coin."

        # Check if any inventory slots are filled
        inventory_slots = [
            player_inventory.items, player_inventory.trees, player_inventory.herbs,
            player_inventory.ore, player_inventory.armors, player_inventory.weapons,
            player_inventory.shields
        ]

        # Check equipped items
        equipped_slots = [
            player_inventory.equipped_armor['chest'], player_inventory.equipped_armor['boots'],
            player_inventory.equipped_armor['gloves'], player_inventory.equipped_weapon,
            player_inventory.equipped_shield
        ]

        if any(inventory_slots) or any(equipped_slots):
            return "Err...sorry, matey. Since you went out and collected more stuff, I assumed you didn't want your stuff back and sold it to someone else."

        # Deduct the coppers
        player_inventory.coppers -= self.cost

        # Restore the items from saved_inventory
        player_inventory.items = self.saved_inventory.items
        player_inventory.trees = self.saved_inventory.trees
        player_inventory.herbs = self.saved_inventory.herbs
        player_inventory.ore = self.saved_inventory.ore
        player_inventory.armors = self.saved_inventory.armors
        player_inventory.weapons = self.saved_inventory.weapons
        player_inventory.shields = self.saved_inventory.shields
        player_inventory.equipped_armor = self.saved_inventory.equipped_armor
        player_inventory.equipped_weapon = self.saved_inventory.equipped_weapon
        player_inventory.equipped_shield = self.saved_inventory.equipped_shield
        player_inventory.equipped_charm = self.saved_inventory.equipped_charm

        # Update player data
        self.player_data[self.author_id]['inventory'] = player_inventory
        # Save player data
        save_player_data(self.interaction.guild.id, self.player_data)

        return "Avast! Your items have been restored. Check yer pockets!"

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.primary)
    async def yes_button(self, button, interaction):
        # Check if the user who clicked is the same as the one who invoked the command
        if str(interaction.user.id) != self.author_id:
            await interaction.response.send_message("This button is not for you.", ephemeral=True)
            return

        message = await self.handle_buy_back()
        await interaction.response.send_message(message, ephemeral=True)

    @discord.ui.button(label="No", style=discord.ButtonStyle.secondary)
    async def no_button(self, button, interaction):
        # Check if the user who clicked is the same as the one who invoked the command
        if str(interaction.user.id) != self.author_id:
            await interaction.response.send_message("This button is not for you.", ephemeral=True)
            return

        await interaction.response.send_message("So be it, ye scurvy dog! Keep to the seas without yer trinkets.",
                                                ephemeral=True)