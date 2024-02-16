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

        options = [
            discord.SelectOption(label=f"{item.name} - {item.value} Coppers", value=item.name, emoji=get_emoji(item.name)) for item in items
        ]
        super().__init__(placeholder="Select an item to view or sell", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return


        selected_item_name = self.values[0]
        selected_item = next((item for item in self.items if item.name == selected_item_name), None)

        # Emojis for each zone
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

        # Colors for each zone
        color_mapping = {
            1: 0x969696,
            2: 0x15ce00,
            3: 0x0096f1,
            4: 0x9900ff,
            5: 0xfebd0d
        }

        # Utilize the mappings for emojis, rarities, and colors based on zone_level
        zone_level = selected_item.zone_level
        zone_emoji = get_emoji(zone_emoji_mapping.get(zone_level))
        zone_rarity_label = zone_rarity.get(zone_level)
        embed_color = color_mapping.get(zone_level)

        # Constructing the title with item name, zone rarity, and emoji
        embed_title = f"{zone_emoji} {selected_item.name} {zone_rarity_label}"

        # Constructing the description with item details
        message_content = f"**Value:** {selected_item.value:,} {get_emoji('coppers_emoji')}\n"
        if hasattr(selected_item, "attack_modifier"):
            message_content += f"**Damage:** {selected_item.attack_modifier}\n"
        if hasattr(selected_item, "defense_modifier"):
            message_content += f"**Armor:** {selected_item.defense_modifier}\n"
        if hasattr(selected_item, "special_attack"):
            message_content += f"**Special Attack:** {selected_item.special_attack}\n"
        if hasattr(selected_item, "description") and selected_item.description:
            message_content += f"**Description:** {selected_item.description}\n"
        message_content += "\nHow many would you like to sell?\n\n**Backpack:**"

        embed = discord.Embed(title=embed_title, description=message_content, color=embed_color)
        embed.set_thumbnail(
            url=generate_urls("Icons", selected_item.name.replace(" ", "%20")))

        formatted_coppers = f"{self.player.inventory.coppers:,}"
        embed.set_footer(text=f"Quantity: {selected_item.stack}\nCoppers: {formatted_coppers}")

        # Determine if the "Sell 5" button should be enabled
        can_sell_5 = selected_item.stack >= 5
        view = discord.ui.View()
        view.add_item(SellButton("Sell 1", 1, selected_item, self.guild_id, self.author_id, self.player_data, self.player))
        # Add the "Sell 5" button, enabling or disabling based on the can_sell_5 flag
        sell_5_button = SellButton("Sell 5", 5, selected_item, self.guild_id, self.author_id, self.player_data, self.player)
        sell_5_button.disabled = not can_sell_5
        view.add_item(sell_5_button)
        view.add_item(SellCustomButton(selected_item, self.guild_id, self.author_id, self.player_data, self.player))

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

        # Adjust inventory and coppers
        successful_sell = self.player.inventory.sell_item(self.item.name, self.sell_amount)
        if successful_sell:
            sell_price = self.sell_amount * self.item.value
            self.player.inventory.add_coppers(sell_price)
            save_player_data(self.guild_id, self.author_id, self.player_data)

            # Update the embed to reflect new quantity and coppers
            updated_quantity = self.player.inventory.get_item_quantity(self.item.name)
            updated_coppers = self.player.inventory.coppers
            embed = interaction.message.embeds[0]  # Assuming there's only one embed
            embed.set_footer(text=f"Quantity: {updated_quantity}\nCoppers: {updated_coppers:,}")
            # Update the message
            await interaction.response.edit_message(embed=embed, view=self.view)  # Ensure 'self.view' is updated with new button states
        else:
            await interaction.response.send_message("An error occurred while trying to sell the item.", ephemeral=True)

class SellCustomButton(discord.ui.Button, CommonResponses):
    def __init__(self, item, guild_id, author_id, player_data, player):
        super().__init__(style=discord.ButtonStyle.secondary, label="Sell X")
        self.item = item
        self.guild_id = guild_id
        self.author_id = author_id
        self.player_data = player_data
        self.player = player

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Open a modal for entering the custom sell amount
        modal = SellXModal(self.item, self.guild_id, self.author_id, self.player_data, self.player)
        await interaction.response.send_modal(modal)

class SellXModal(discord.ui.Modal, CommonResponses):
    def __init__(self, item, guild_id, author_id, player_data, player):
        super().__init__(title=f"Sell How Many {item.name}?")
        self.item = item
        self.guild_id = guild_id
        self.author_id = author_id
        self.player_data = player_data
        self.player = player

        self.quantity = discord.ui.InputText(label="Quantity", placeholder="Enter a number")
        self.add_item(self.quantity)

    async def callback(self, interaction: discord.Interaction):
        quantity_str = self.quantity.value.strip()
        if not quantity_str.isdigit() or int(quantity_str) <= 0:
            await interaction.response.send_message("Please enter a valid positive integer.", ephemeral=True)
            return

        quantity = int(quantity_str)
        if quantity > self.player.inventory.get_item_quantity(self.item.name):
            await interaction.response.send_message("You do not have enough items to sell this quantity.", ephemeral=True)
            return

        # Adjust inventory and coppers
        self.player.inventory.sell_item(self.item.name, quantity)
        sell_price = quantity * self.item.value
        self.player.inventory.add_coppers(sell_price)

        # Update and save player data
        save_player_data(self.guild_id, self.author_id, self.player.to_dict())

        # Send confirmation message
        await interaction.response.send_message(f"Successfully sold {quantity} of '{self.item.name}' for {sell_price:,} coppers.", ephemeral=True)
