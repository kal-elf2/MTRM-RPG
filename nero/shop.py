import discord
from emojis import get_emoji
from utils import CommonResponses, save_player_data, load_player_data
from nero.options import ResetButton
from images.urls import generate_urls
from exemplars.exemplars import Exemplar
class ShopCategorySelect(discord.ui.Select, CommonResponses):
    def __init__(self, guild_id, author_id, player_data, player):
        self.guild_id = guild_id
        self.author_id = author_id
        self.player_data = player_data
        self.player = player

        options = [
            discord.SelectOption(label="Weapons", value="weapons"),
            discord.SelectOption(label="Armors", value="armors"),
            discord.SelectOption(label="Shields", value="shields"),
            discord.SelectOption(label="Charms", value="charms"),
            discord.SelectOption(label="Potions", value="potions")
        ]
        super().__init__(placeholder="Select a category to browse items", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        selected_category = self.values[0]
        items = getattr(self.player.inventory, selected_category, [])

        self.view.clear_items()  # Clear current items
        # Dynamically create and add the DisplayItemsSelect dropdown
        if items:
            item_select = DisplayItemsSelect(interaction, items, self.author_id)
            self.view.add_item(item_select)
        self.view.add_item(ResetButton(self.author_id))  # Keep the Reset button
        self.view.add_item(RefreshShopButton(self.author_id))  # Add the Refresh Shop button
        await interaction.response.edit_message(content=f"Select an item from {selected_category}:", view=self.view)

class DisplayItemsSelect(discord.ui.Select, CommonResponses):
    def __init__(self, interaction, items, author_id):
        self.interaction = interaction
        self.items = items
        self.author_id = author_id
        self.guild_id = self.interaction.guild.id
        self.author_id = str(self.interaction.user.id)
        self.player_data = load_player_data(self.guild_id, self.author_id)
        self.player = Exemplar(self.player_data["exemplar"],
                               self.player_data["stats"],
                               self.player_data["inventory"])
        self.zone_rarity = {
            1: '(Common)',
            2: '(Uncommon)',
            3: '(Rare)',
            4: '(Epic)',
            5: '(Legendary)',
        }

        options = [
            discord.SelectOption(
                label=f"{item.name} {self.zone_rarity.get(getattr(item, 'zone_level', ''), '')} - {format(item.value, ',')} Coppers",
                # Conditionally construct value with or without zone_level
                value=f"{item.name}:{getattr(item, 'zone_level', 'None')}",
                emoji=get_emoji(item.name)
            )
            for item in items
        ]
        super().__init__(placeholder="Select an item to sell", options=options, min_values=1, max_values=1)


    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return


        selected_item_value = self.values[0]
        item_name, zone_level_str = selected_item_value.rsplit(':', 1)

        # Handle items without zone_level differently
        if zone_level_str != 'None':
            zone_level = int(zone_level_str)
            selected_item = next((item for item in self.items if
                                  item.name == item_name and getattr(item, 'zone_level', 0) == zone_level), None)
        else:
            selected_item = next(
                (item for item in self.items if item.name == item_name and not hasattr(item, 'zone_level')), None)

        embed = create_item_embed(selected_item, self.player)

        # Initialize the view for displaying buttons with the SellItemView
        view = SellItemView(selected_item, self.guild_id, self.author_id, self.player_data, self.player)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class RefreshShopButton(discord.ui.Button, CommonResponses):
    def __init__(self, author_id):
        super().__init__(label="Refresh Shop", style=discord.ButtonStyle.primary, custom_id="refresh_shop")
        self.author_id = author_id

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        guild_id = interaction.guild.id
        author_id = str(interaction.user.id)
        player_data = load_player_data(guild_id, author_id)
        player = Exemplar(player_data["exemplar"],
                          player_data["stats"],
                          player_data["inventory"])

        # Refresh the Shop view to show categories
        self.view.clear_items()
        self.view.add_item(ShopCategorySelect(guild_id, author_id, player_data, player))
        self.view.add_item(ResetButton(self.author_id))  # Ensure Reset button is still present
        # Note: The Refresh Shop button will be re-added when a category is selected, not here
        await interaction.response.edit_message(content="Select a category to browse items:", view=self.view)

class SellButton(discord.ui.Button, CommonResponses):
    def __init__(self, label, sell_amount, item, guild_id, author_id, player_data, player):
        super().__init__(style=discord.ButtonStyle.primary, label=label)
        self.sell_amount = sell_amount
        self.item = item
        self.guild_id = guild_id
        self.author_id = author_id
        self.player_data = player_data
        self.player = player

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Attempt to sell the item
        successful_sell = self.player.inventory.sell_item(self.item.name, self.sell_amount, getattr(self.item, 'zone_level', None))

        if successful_sell:
            sell_price = self.sell_amount * self.item.value  # Calculated sell price
            self.player.inventory.add_coppers(sell_price)
            save_player_data(self.guild_id, self.author_id, self.player_data)

            # Call update_view_and_message with sell_price as an additional argument
            await self.view.update_view_and_message(interaction, self.item, sell_price)
        else:
            # If sell operation was not successful, possibly due to an inventory mismatch, show a thematic error message
            pirate_embed = discord.Embed(
                title="Ye Broke Sumthin'",
                description="Arrr! Seems we've hit a snag with that transaction. Perhaps a quick refresh of the shoppe is in order?",
                color=discord.Color.dark_gold()
            )
            pirate_thumbnail_url = generate_urls("nero", "confused")
            pirate_embed.set_thumbnail(url=pirate_thumbnail_url)

            await interaction.response.send_message(embed=pirate_embed, ephemeral=True)


class SellItemView(discord.ui.View):
    def __init__(self, item, guild_id, author_id, player_data, player):
        super().__init__()
        self.item = item
        self.guild_id = guild_id
        self.author_id = author_id
        self.player_data = player_data
        self.player = player
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        item_quantity = self.player.inventory.get_item_quantity(self.item.name, getattr(self.item, 'zone_level', None))

        # Define sell amounts and labels
        potential_sell_amounts = [1, 5, 10, 25]

        # Ensure "Sell 1" button is always shown when there is at least 1 item
        if item_quantity >= 1:
            self.add_item(SellButton("Sell 1", 1, self.item, self.guild_id, self.author_id, self.player_data, self.player))

        # Add "Sell X" buttons for amounts greater than 1 based on the item quantity criteria
        for amount in potential_sell_amounts[1:]:  # Start from the second element (5) to avoid duplicating "Sell 1"
            if item_quantity >= amount and item_quantity != amount:  # Show button if you have at least that amount, excluding exact matches
                label = f"Sell {amount}"
                button = SellButton(label, amount, self.item, self.guild_id, self.author_id, self.player_data, self.player)
                self.add_item(button)

        # Always include "Sell All" if there's more than 1 item
        if item_quantity > 1:
            sell_all_label = "Sell All"
            button = SellButton(sell_all_label, item_quantity, self.item, self.guild_id, self.author_id, self.player_data, self.player)
            self.add_item(button)

    async def update_view_and_message(self, interaction, item, sell_price=None):
        item_quantity = self.player.inventory.get_item_quantity(item.name, getattr(item, 'zone_level', None))
        item.stack = item_quantity  # Ensure the item quantity is updated
        self.update_buttons()
        updated_embed = create_item_embed(item, self.player, sell_price)
        await interaction.response.edit_message(embed=updated_embed, view=self)


def create_item_embed(item, player, sell_amount=None):
    zone_emoji_mapping = {
        1: 'common_emoji',
        2: 'uncommon_emoji',
        3: 'rare_emoji',
        4: 'epic_emoji',
        5: 'legendary_emoji'
    }
    zone_rarity = {
        1: '(Common)',
        2: '(Uncommon)',
        3: '(Rare)',
        4: '(Epic)',
        5: '(Legendary)',
    }
    color_mapping = {
        1: 0x969696,
        2: 0x15ce00,
        3: 0x0096f1,
        4: 0x9900ff,
        5: 0xfebd0d
    }

    zone_level = getattr(item, 'zone_level', 0)
    zone_emoji = get_emoji(zone_emoji_mapping.get(zone_level))
    zone_rarity_label = zone_rarity.get(zone_level, '')
    embed_color = color_mapping.get(zone_level, 0x000000)

    embed_title = f"{zone_emoji} {item.name} {zone_rarity_label}"
    message_content = f"**Value:** {item.value:,} {get_emoji('coppers_emoji')}\n"
    if hasattr(item, "attack_modifier"):
        message_content += f"**Damage:** {item.attack_modifier}\n"
    if hasattr(item, "defense_modifier"):
        message_content += f"**Armor:** {item.defense_modifier}\n"
    if hasattr(item, "special_attack"):
        message_content += f"**Special Attack:** {item.special_attack}\n"
    if hasattr(item, "description") and item.description:
        message_content += f"**Description:** {item.description}\n"
    # Adjusted message content to optionally include sell_amount
    message_content += "\nHow many would you like to sell?"

    # Adding Quantity and Coppers to the main embed content
    formatted_coppers = f"{player.inventory.coppers:,}"
    coppers_emoji = get_emoji('coppers_emoji')
    message_content += f"\n\n**Backpack:**\nQuantity: {item.stack}\n{formatted_coppers} {coppers_emoji}"

    # Include sell amount if provided
    if sell_amount is not None:
        message_content += f" (+{sell_amount})"

    embed = discord.Embed(title=embed_title, description=message_content, color=embed_color)
    embed.set_thumbnail(url=generate_urls("Icons", item.name.replace(" ", "%20")))

    return embed