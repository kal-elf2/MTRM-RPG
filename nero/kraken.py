import discord
from utils import CommonResponses
from utils import load_player_data, save_player_data
from exemplars.exemplars import Exemplar
from images.urls import generate_urls
from emojis import get_emoji

class ConfirmSellView(discord.ui.View, CommonResponses):
    def __init__(self, author_id, guild_id, player_data):
        super().__init__()
        self.author_id = author_id
        self.guild_id = guild_id
        self.player_data = player_data

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.blurple, custom_id="confirm_sell_yes")
    async def confirm_sell(self, button: discord.ui.Button, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            return await self.nero_unauthorized_user_response(interaction)

        player_data = load_player_data(self.guild_id, self.author_id)
        player = Exemplar(player_data["exemplar"], player_data["stats"], player_data["inventory"])
        sellable_categories = ["weapons", "armors", "shields", "charms", "potions"]
        total_coppers_earned = 0

        # Iterate over each category and remove items, adding their value to total coppers earned
        for category_name in sellable_categories:
            category_items = getattr(player.inventory, category_name, [])
            for item in list(category_items):
                total_coppers_earned += item.value * item.stack
                category_items.remove(item)

        player.inventory.coppers += total_coppers_earned
        save_player_data(self.guild_id, self.author_id, player_data)

        # Provide feedback to the player
        sell_feedback_embed = discord.Embed(
            title="Ye Sold Yer Booty!",
            description=f"All loot sold for {total_coppers_earned:,} {get_emoji('coppers_emoji')}\n\n***Ye be ready to face the Kraken!***",
            color=discord.Color.dark_gold()
        )
        sell_feedback_embed.set_thumbnail(url=generate_urls("nero", "kraken"))
        view = discord.ui.View()
        view.add_item(HuntKrakenButton(self.guild_id, self.player_data, self.author_id))
        await interaction.response.edit_message(embed=sell_feedback_embed, view=view)

    @discord.ui.button(label="No", style=discord.ButtonStyle.grey, custom_id="confirm_sell_no")
    async def cancel_sell(self, button: discord.ui.Button, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            return await self.nero_unauthorized_user_response(interaction)

        cancel_embed = discord.Embed(
            title="Change of heart, matey?",
            description="Arr, looks like ye had second thoughts. Come back and see me when ye change yer mind.",
            color=discord.Color.dark_gold()
        )
        cancel_embed.set_thumbnail(url=generate_urls("nero", "confused"))
        await interaction.response.edit_message(embed=cancel_embed, view=None)

class SellAllButton(discord.ui.Button, CommonResponses):
    def __init__(self, label: str, author_id, guild_id, player_data, style=discord.ButtonStyle.blurple):
        super().__init__(style=style, label=label)
        self.author_id = author_id
        self.guild_id = guild_id
        self.player_data = player_data

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            return await self.nero_unauthorized_user_response(interaction)

        # Confirmation message
        confirm_embed = discord.Embed(
            title="Confirm Sale",
            description="Are ye sure ye want to sell all yer loot?\n\n***There ain't no going back after this, savvy?***",
            color=discord.Color.dark_gold()
        )
        confirm_embed.set_thumbnail(url=generate_urls("nero", "gun"))
        confirm_view = ConfirmSellView(self.author_id, self.guild_id, self.player_data)
        await interaction.response.edit_message(embed=confirm_embed, view=confirm_view)

class HuntKrakenButton(discord.ui.Button, CommonResponses):
    def __init__(self, guild_id, player_data, author_id):
        super().__init__(style=discord.ButtonStyle.green, label="Hunt Kraken", emoji="🦑")
        self.guild_id = guild_id
        self.player_data = player_data
        self.author_id = author_id

        # Initialize the player from player_data
        self.player = Exemplar(self.player_data["exemplar"],
                               self.player_data["stats"],
                               self.player_data["inventory"])

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            return await self.nero_unauthorized_user_response(interaction)

        # Disable the button
        self.disabled = True

        await interaction.response.defer()

        # Set player location to None
        self.player_data["location"] = None

        zone_level = self.player.stats.zone_level

        # Handle inventory based on zone level
        if zone_level < 5:
            # Clear inventory for zones 1 through 4
            self.player.inventory.items = []
            self.player.inventory.trees = []
            self.player.inventory.herbs = []
            self.player.inventory.ore = []
            self.player.inventory.armors = []
            self.player.inventory.weapons = []
            self.player.inventory.shields = []
            self.player.inventory.charms = []
            self.player.inventory.potions = []

        else:
            # Subtract one Goblin Crown from the inventory in zone 5
            self.player.inventory.remove_item("Goblin Crown", 1)

        # Save the updated player data
        save_player_data(self.guild_id, self.author_id, self.player_data)

        # Update view to disable button
        await interaction.edit_original_response(view=self.view)

        # Placeholder for actual battle logic
        await interaction.followup.send("Kraken battle initiated! Good luck!", ephemeral=True)

