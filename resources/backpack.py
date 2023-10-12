from discord.ext import commands
import discord
import copy
from utils import load_player_data, update_and_save_player_data
from images.urls import generate_urls
from citadel.crafting import Armor

class BackpackCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Open your backpack!")
    async def backpack(self, ctx):
        # Display initial backpack view with Equip and Unequip buttons
        view = BackpackView(ctx)
        await ctx.respond("Here's your backpack:", view=view)

class BackpackView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.item_type_select = None

        # Load the player's data
        self.player_data = load_player_data(ctx.guild.id)

        # Find the specific player's inventory from the loaded data
        player_id = str(ctx.author.id)
        self.inventory = self.player_data[player_id]["inventory"]

    def update_or_add_item_type_select(self, action_type):
        # Always present all the options
        options = [
            discord.SelectOption(label="Weapon", value="Weapon"),
            discord.SelectOption(label="Armor", value="Armor"),
            discord.SelectOption(label="Shield", value="Shield"),
            discord.SelectOption(label='Charm', value="Charm")
        ]

        if self.item_type_select:
            self.remove_item(self.item_type_select)

        self.item_type_select = ItemTypeSelect(action_type, options)
        self.add_item(self.item_type_select)

    def update_item_select_options(self):
        if self.item_type_select:
            selected_type = self.item_type_select.placeholder.split(" ")[-3]  # e.g. "Choose an item type to equip"
            items = getattr(self.inventory, selected_type.lower() + "s", [])

            self.item_type_select.options.clear()

            for item in items:
                option = discord.SelectOption(label=item.name, value=item.name, emoji=getattr(item, "emoji", None))
                self.item_type_select.options.append(option)

    def refresh_view(self):
        # Load the player's updated data
        self.player_data = load_player_data(self.ctx.guild.id)
        player_id = str(self.ctx.author.id)
        self.inventory = self.player_data[player_id]["inventory"]

        # If item type select exists, update its options
        if self.item_type_select:
            self.update_item_select_options()

    @discord.ui.button(label="Equip", custom_id="backpack_equip", style=discord.ButtonStyle.primary)
    async def equip(self, button, interaction):
        # Open the select menu for item types for the Equip action
        self.update_or_add_item_type_select("equip")
        await interaction.response.edit_message(content="Choose an item type to equip:", view=self)

    @discord.ui.button(label="Unequip", custom_id="backpack_unequip", style=discord.ButtonStyle.danger)
    async def unequip(self, button, interaction):
        # Open the select menu for item types for the Unequip action
        self.update_or_add_item_type_select("unequip")
        await interaction.response.edit_message(content="Choose an item type to unequip:", view=self)

class ItemTypeSelect(discord.ui.Select):
    def __init__(self, action_type, options):
        self.action_type = action_type
        super().__init__(placeholder=f"Choose an item type to {action_type}", options=options, min_values=1, max_values=1)

    def equip_item(self, inventory, category, selected_item, existing_item):
        """Handles equipping logic."""
        category_singular = category[:-1]
        equipped_item_key = f"equipped_{category_singular}"

        if isinstance(selected_item, Armor):
            existing_armor_piece = inventory.equipped_armor.get(selected_item.armor_type)
            if existing_armor_piece:
                self.add_to_inventory(inventory.armors, existing_armor_piece)
            inventory.equipped_armor[selected_item.armor_type] = selected_item
        else:
            current_equipped_item = getattr(inventory, equipped_item_key, None)
            if current_equipped_item:
                self.add_to_inventory(getattr(inventory, category), current_equipped_item)
            setattr(inventory, equipped_item_key, selected_item)

        if existing_item.stack == 1:
            getattr(inventory, category).remove(existing_item)
        else:
            existing_item.stack -= 1

    def unequip_item(self, inventory, category, selected_item, existing_item):
        """Handles unequipping logic."""
        category_singular = category[:-1]
        equipped_item_key = f"equipped_{category_singular}"

        if isinstance(selected_item, Armor):
            if inventory.equipped_armor[selected_item.armor_type] == selected_item:
                self.add_to_inventory(inventory.armors, selected_item)
                inventory.equipped_armor[selected_item.armor_type] = None
        else:
            if getattr(inventory, equipped_item_key) == selected_item:
                self.add_to_inventory(getattr(inventory, category), selected_item)
                setattr(inventory, equipped_item_key, None)

    def add_to_inventory(self, inventory_category, item):
        """Adds an item to the inventory and handles stacking."""
        existing_item_in_inventory = next((i for i in inventory_category if i.name == item.name), None)
        if existing_item_in_inventory:
            existing_item_in_inventory.stack += 1
        else:
            inventory_category.append(copy.deepcopy(item))

    async def callback(self, interaction: discord.Interaction):
        # Handle the selected item type and perform either equip or unequip action
        selected_value = self.values[0]

        # Retrieve the player's inventory
        view: BackpackView = self.view
        inventory = view.inventory

        # If the selected value corresponds to an item type, show the items
        if selected_value in ["Weapon", "Armor", "Shield", "Charm"]:
            items = getattr(inventory, selected_value.lower() + "s", [])

            # If no items exist in the category, send a message and return
            if not items:
                embed = create_item_embed(self.action_type, selected_value)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Clear existing options
            self.options.clear()

            # Now, append the specific items in the selected category to the options list
            for item in items:
                option = discord.SelectOption(label=item.name, value=item.name, emoji=getattr(item, "emoji", None))
                self.options.append(option)

            # Remove the item types from the options
            item_types = ["Weapon", "Armor", "Shield", "Charm"]
            self.options = [opt for opt in self.options if opt.label not in item_types]

            # Reset the placeholder to reflect the change
            self.placeholder = f"Choose a specific {selected_value} to {self.action_type}"

            # Update the interaction message to show the updated options
            await interaction.response.edit_message(content=f"Choose a specific {selected_value} to {self.action_type}:", view=view)
            return


        # If execution reaches here, it means an actual item was selected
        selected_item_name = self.values[0]

        for category in ["weapons", "armors", "shields", "charms"]:
            selected_item = next((item for item in getattr(inventory, category, []) if item.name == selected_item_name),
                                 None)

            if selected_item is None:
                continue

            category_singular = category[:-1]  # Convert 'weapons' to 'weapon', 'armors' to 'armor', etc.
            existing_item = next((item for item in getattr(inventory, category, []) if item.name == selected_item_name),
                                 None)

            equipped_item_key = f"equipped_{category_singular}"

            if isinstance(selected_item, Armor):
                if inventory.equipped_armor[selected_item.armor_type].name == selected_item_name:
                    await interaction.response.send_message(f"You already have this {category_singular} equipped.",
                                                            ephemeral=True)
                    return

            else:
                current_equipped_item = getattr(inventory, equipped_item_key, None)
                if current_equipped_item and current_equipped_item.name == selected_item_name:
                    await interaction.response.send_message(f"You already have this {category_singular} equipped.",
                                                            ephemeral=True)
                    return

            # Equip logic
            if self.action_type == "equip":
                if isinstance(selected_item, Armor):
                    existing_armor_piece = inventory.equipped_armor.get(selected_item.armor_type)
                    if existing_armor_piece:
                        existing_armor_piece_in_inventory = next(
                            (item for item in inventory.armors if item.name == existing_armor_piece.name), None)
                        if existing_armor_piece_in_inventory:
                            existing_armor_piece_in_inventory.stack += 1
                        else:
                            inventory.armors.append(copy.deepcopy(existing_armor_piece))
                    inventory.equipped_armor[selected_item.armor_type] = selected_item

                else:
                    current_equipped_item = getattr(inventory, equipped_item_key, None)
                    if current_equipped_item:
                        existing_equipped_item = next((item for item in getattr(inventory, category, []) if
                                                       item.name == current_equipped_item.name), None)
                        if existing_equipped_item:
                            existing_equipped_item.stack += 1
                        else:
                            getattr(inventory, category).append(copy.deepcopy(current_equipped_item))
                    setattr(inventory, equipped_item_key, selected_item)

                if existing_item:
                    if existing_item.stack == 1:
                        getattr(inventory, category).remove(existing_item)
                    else:
                        existing_item.stack -= 1

            # Unequip logic
            elif self.action_type == "unequip":
                if isinstance(selected_item, Armor):
                    if inventory.equipped_armor[selected_item.armor_type] == selected_item:
                        if existing_item:
                            existing_item.stack += 1
                        else:
                            inventory.armors.append(selected_item)
                        inventory.equipped_armor[selected_item.armor_type] = None

                else:
                    if getattr(inventory, equipped_item_key) == selected_item:
                        if existing_item:
                            existing_item.stack += 1
                        else:
                            getattr(inventory, category).append(selected_item)
                        setattr(inventory, equipped_item_key, None)

            update_and_save_player_data(interaction, inventory, view.player_data)
            embed = create_item_embed(self.action_type, selected_item)
            await interaction.response.send_message(embed=embed, ephemeral=True)

            # Call the refresh method here
            view.refresh_view()
            break


def create_item_embed(action, item):
    if isinstance(item, str):  # Item doesn't exist, so it's a string (e.g., "Weapon", "Armor")
        title = f"{action.capitalize()} {item}"
        description = f"You don't have any {item} to {action}."
        thumbnail_url = generate_urls("Icons", "default")  # Set a default image for non-existent items
    else:  # Item exists, so it has a `name` attribute
        title = f"{action.capitalize()}ped {item.name}"
        description = f"You have {action}ped the {item.name}."
        thumbnail_url = generate_urls("Icons", item.name)

    embed = discord.Embed(title=title, description=description, color=0x3498db)
    embed.set_thumbnail(url=thumbnail_url)

    return embed

def setup(bot):
    bot.add_cog(BackpackCog(bot))
