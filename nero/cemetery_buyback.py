import discord
from probabilities import buyback_cost
from utils import save_player_data
from images.urls import generate_urls
from emojis import get_emoji

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

        # Check if the player has enough coppers
        if player_inventory.coppers < self.cost:
            return "Arr, ye be short on coppers! Can't make a deal without the coin."

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

        # Update player data
        self.player_data[self.author_id]['inventory'] = player_inventory
        # Save player data
        save_player_data(self.interaction.guild.id, self.player_data)

        message = (f"*You begrudgingly hand over {buyback_cost * self.player.stats.zone_level}{get_emoji('coppers_emoji')}*\n\n"
                  f"Avast! Your items have been restored. Check yer pockets!")

        return message

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.primary)
    async def yes_button(self, button, interaction):
        # Check if the user who clicked is the same as the one who invoked the command
        if str(interaction.user.id) != self.author_id:
            await interaction.response.send_message("This button is not for you.", ephemeral=True)
            return

        # Edit the original captain's message and remove the buttons
        message = await self.handle_buy_back()
        thumbnail_url = generate_urls("nero", "cemetery")
        nero_embed = discord.Embed(
            title="Captain Ner0",
            description=f"{message}",
            color=discord.Color.dark_gold()
        )
        nero_embed.set_thumbnail(url=thumbnail_url)
        await interaction.message.edit(embed=nero_embed, view=None)

    @discord.ui.button(label="No", style=discord.ButtonStyle.secondary)
    async def no_button(self, button, interaction):
        # Check if the user who clicked is the same as the one who invoked the command
        if str(interaction.user.id) != self.author_id:
            await interaction.response.send_message("This button is not for you.", ephemeral=True)
            return

        # Edit the original captain's message to show refusal and remove the buttons
        thumbnail_url = generate_urls("nero", "cemetery")
        nero_embed = discord.Embed(
            title="Captain Ner0",
            description="So be it, ye scurvy dog! Keep to the seas without yer trinkets.",
            color=discord.Color.dark_gold()
        )
        nero_embed.set_thumbnail(url=thumbnail_url)
        await interaction.message.edit(embed=nero_embed, view=None)