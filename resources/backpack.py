from discord.ext import commands
import discord
import copy
from utils import load_player_data, update_and_save_player_data, save_player_data
from images.urls import generate_urls
from citadel.crafting import Armor
import io
from resources.backpackimage import generate_backpack_image
from emojis import get_emoji

ZONE_LEVEL_TO_RARITY = {
            1: "Common",
            2: "Uncommon",
            3: "Rare",
            4: "Epic",
            5: "Legendary"
        }
ZONE_LEVEL_TO_EMOJI = {
    1: 'common_emoji',
    2: 'uncommon_emoji',
    3: 'rare_emoji',
    4: 'epic_emoji',
    5: 'legendary_emoji'
}

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

    def unequip_add_item_type_select(self, action_type):
        # Always present all the options
        options = [
            discord.SelectOption(label="Weapon", value="Weapon"),
            discord.SelectOption(label="Armor", value="Armor"),
            discord.SelectOption(label="Shield", value="Shield"),
            discord.SelectOption(label='Charm', value="Charm")
        ]

        if self.item_type_select:
            self.remove_item(self.item_type_select)

        self.item_type_select = UnequipTypeSelect(action_type, options)
        self.add_item(self.item_type_select)

    def equip_add_item_type_select(self, action_type):
        # Always present all the options
        options = [
            discord.SelectOption(label="Weapon", value="Weapon"),
            discord.SelectOption(label="Armor", value="Armor"),
            discord.SelectOption(label="Shield", value="Shield"),
            discord.SelectOption(label='Charm', value="Charm")
        ]

        if self.item_type_select:
            self.remove_item(self.item_type_select)

        self.item_type_select = EquipTypeSelect(action_type, options)
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

    @discord.ui.button(label="Equip", custom_id="backpack_equip", style=discord.ButtonStyle.primary, emoji="⚔️")
    async def equip(self, button, interaction):
        # Open the select menu for item types for the Equip action
        self.equip_add_item_type_select("equip")
        await interaction.response.edit_message(content="Choose an item type to equip:", view=self)

    @discord.ui.button(label="Unequip", custom_id="backpack_unequip", style=discord.ButtonStyle.blurple, emoji="⛔")
    async def unequip(self, button, interaction):
        # Open the select menu for item types for the Unequip action
        self.unequip_add_item_type_select("unequip")
        await interaction.response.edit_message(content="Choose an item type to unequip:", view=self)


    @discord.ui.button(label="Sort", custom_id="backpack_sort", style=discord.ButtonStyle.blurple, emoji="🔄")
    async def sort(self, button, interaction):
        from exemplars.exemplars import Exemplar

        self.clear_items()
        def sort_items(items, order):
            return sorted(items, key=lambda item: (getattr(item, 'zone_level', 0), order.index(item.name)))

        guild_id = interaction.guild.id
        author_id = str(interaction.user.id)
        player_data = load_player_data(guild_id)
        player = Exemplar(player_data[author_id]["exemplar"],
                          player_data[author_id]["stats"],
                          player_data[author_id]["inventory"])

        order = {
            "items": [
                "Charcoal", "Iron", "Steel", "Onyx", "Pole", "Thick Pole",
                "Pine Strip", "Yew Strip", "Ash Strip", "Poplar Strip",
                "Flour", "Wheat", "Flax", "Linen", "Linen Thread", "Venison",
                "Sinew", "Rabbit Body", "Rabbit Meat", "Deer Parts",
                "Deer Skin", "Wolf Skin", "Glowing Essence", "Leather",
                "Tough Leather", "Leather Straps", "Tough Leather Straps"
            ],
            "trees": ["Pine", "Yew", "Ash", "Poplar"],
            "herbs": ["Ranarr", "Spirit Weed", "Snapdragon", "Bloodweed", "Dwarf Weed"],
            "ore": ["Iron Ore", "Coal", "Carbon"],
            "gems": ["Sapphire", "Emerald", "Ruby", "Diamond", "Black Opal"],
            "potions": ["Stamina Potion", "Health Potion", "Super Stamina Potion", "Super Health Potion"],
            "armors": [
                "Leather Armor", "Leather Boots", "Leather Gloves",
                "Padded Armor", "Padded Boots", "Padded Gloves",
                "Brigandine Armor", "Brigandine Boots", "Brigandine Gloves"
            ],
            "weapons": [
                "Short Sword", "Long Sword", "Champion Sword", "Voltaic Sword",
                "Short Spear", "Long Spear", "Champion Spear", "Club",
                "Hammer", "War Hammer", "Short Bow", "Long Bow", "Champion Bow"
            ],
            "shields": ["Buckler", "Small Shield", "Large Shield"],
            "charms": ["Mining", "Woodcutting", "Loot"]
        }

        for category, sorting_order in order.items():
            if hasattr(player.inventory, category):
                category_items = getattr(player.inventory, category)
                sorted_items = sort_items(category_items, sorting_order)
                setattr(player.inventory, category, sorted_items)

        save_player_data(guild_id, player_data)
        await interaction.response.send_message(content="Inventory sorted.", view=self, ephemeral=True)

    @discord.ui.button(label="View", custom_id="backpack_inspect", style=discord.ButtonStyle.blurple, emoji="🔍")
    async def inspect(self, button, interaction):

        # Defer the response to prevent the interaction from timing out
        await interaction.response.defer(ephemeral=True)

        # Send an ephemeral message to let the user know the image is being generated
        await interaction.followup.send("Image being generated...", ephemeral=True)

        # Generate the backpack image
        backpack_img = generate_backpack_image(interaction)
        with io.BytesIO() as image_binary:
            backpack_img.save(image_binary, 'PNG')
            image_binary.seek(0)

            # Send the generated image
            await interaction.followup.send(file=discord.File(fp=image_binary, filename='backpack_with_items.png'))

class UnequipTypeSelect(discord.ui.Select):
    def __init__(self, action_type, options):
        self.action_type = action_type
        super().__init__(placeholder=f"Choose an item type to {action_type}", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        def get_armor_type_by_name(name: str, inventory):
            """Utility function to get armor type based on the name from the equipped armor."""
            for armor_key, armor_data in inventory.equipped_armor.items():
                if armor_data and armor_data.name == name:
                    return armor_key  # Return the key, which corresponds to the armor type.
            return None

        selected_value = self.values[0]
        view: BackpackView = self.view
        inventory = view.inventory

        # Handle Unequipping for single-slot categories
        if self.action_type == "unequip" and selected_value in ["Weapon", "Shield", "Charm"]:
            category_singular = selected_value.lower()
            equipped_item_key = f"equipped_{category_singular}"
            equipped_item = getattr(inventory, equipped_item_key, None)

            if equipped_item:
                existing_item = next((item for item in getattr(inventory, category_singular + "s", []) if
                                      item.name == equipped_item.name), None)
                if existing_item:
                    existing_item.stack += 1
                else:
                    getattr(inventory, category_singular + "s").append(copy.deepcopy(equipped_item))

                # Unequip the item
                setattr(inventory, equipped_item_key, None)

                update_and_save_player_data(interaction, inventory, view.player_data)
                embed = create_item_embed(self.action_type, equipped_item)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                view.refresh_view()
                return

            else:
                embed = create_item_embed(self.action_type, selected_value)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        # Handle Unequipping for Armor type
        if self.action_type == "unequip" and selected_value == "Armor":
            equipped_armors = [Armor.from_dict(armor_data) if isinstance(armor_data, dict) else armor_data
                               for armor_data in inventory.equipped_armor.values() if armor_data is not None]

            if not equipped_armors:
                embed = create_item_embed(self.action_type, selected_value)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Clear existing options
            self.options.clear()

            # Populate the dropdown with currently equipped armor pieces
            for armor in equipped_armors:
                option = discord.SelectOption(
                    label=armor.name,
                    value=armor.name,
                    emoji=get_emoji(ZONE_LEVEL_TO_EMOJI[armor.zone_level])
                )
                self.options.append(option)

            self.placeholder = f"Choose a specific {selected_value} to {self.action_type}"
            await interaction.response.edit_message(content=f"Choose a specific {selected_value} to {self.action_type}:", view=view)
            return

        selected_item_name = self.values[0]
        selected_item = None

        for armor_type, armor in inventory.equipped_armor.items():
            if armor and armor.name == selected_item_name:
                selected_item = armor
                break

        if not selected_item:
            await interaction.response.send_message(f"No item found with name: {selected_item_name}", ephemeral=True)
            return

        # If the selected item is an armor, handle its unequipping
        if isinstance(selected_item, Armor):
            armor_type = get_armor_type_by_name(selected_item_name, inventory)
            if inventory.equipped_armor[armor_type] and inventory.equipped_armor[armor_type].name == selected_item_name:
                existing_armor = next((armor for armor in inventory.armors if armor.name == selected_item_name), None)
                if existing_armor:
                    existing_armor.stack += 1
                else:
                    inventory.armors.append(copy.deepcopy(inventory.equipped_armor[armor_type]))

                # Unequip the armor
                inventory.equipped_armor[armor_type] = None

                # Save and send a response
                update_and_save_player_data(interaction, inventory, view.player_data)
                embed = create_item_embed(self.action_type, selected_item)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                view.refresh_view()
                return

class EquipTypeSelect(discord.ui.Select):

    def __init__(self, action_type, options):
        self.action_type = action_type
        super().__init__(placeholder=f"Choose an item type to {action_type}", options=options, min_values=1,
                         max_values=1)

    async def callback(self, interaction: discord.Interaction):
        view: BackpackView = self.view
        inventory = view.inventory
        selected_value = self.values[0]

        if selected_value in ["Weapon", "Armor", "Shield", "Charm"]:
            await self.handle_item_type_selection(interaction, inventory, selected_value)
        else:
            await self.handle_item_equipping(interaction, inventory, selected_value)

    async def handle_item_type_selection(self, interaction, inventory, item_type):
        items = getattr(inventory, item_type.lower() + "s", [])

        if not items:
            embed = create_item_embed(self.action_type, item_type)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Modify the options creation to include the rarity in the label and value and emoji based on zone level
        self.options = [
            discord.SelectOption(
                label=f"{item.name}",
                value=f"{item.name} ({ZONE_LEVEL_TO_RARITY[item.zone_level]})",
                emoji=get_emoji(ZONE_LEVEL_TO_EMOJI[item.zone_level])  # Use get_emoji function here
            )
            for item in items
        ]

        await interaction.response.edit_message(content=f"Choose a specific {item_type} to equip:", view=self.view)

    @staticmethod
    def get_item_name(item):
        """Get the name of the item, whether it's a dictionary or an object."""
        if isinstance(item, dict):
            return item.get('name')
        return getattr(item, 'name', None)

    async def handle_item_equipping(self, interaction, inventory, item_name):
        selected_item = self.find_item_by_name(inventory, item_name)

        if not selected_item:
            return

        message, _ = await self.equip_item(interaction, inventory, selected_item)  # Unpack the tuple here

        if message:  # Only send a response if there's a message to send
            await interaction.response.send_message(message, ephemeral=True)
        else:
            embed = create_item_embed(self.action_type, selected_item)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        update_and_save_player_data(interaction, inventory, self.view.player_data)
        self.view.refresh_view()

    @staticmethod
    def find_item_by_name(inventory, item_name_with_rarity):
        # Split the name and rarity
        item_name, rarity = item_name_with_rarity.rsplit(" (", 1)
        rarity = rarity.rstrip(")")

        for category in ["weapons", "armors", "shields", "charms"]:
            selected_item = next(
                (item for item in getattr(inventory, category, [])
                 if item.name == item_name and ZONE_LEVEL_TO_RARITY[item.zone_level] == rarity),
                None
            )
            if selected_item:
                return selected_item

        return None

    async def equip_item(self, interaction, inventory, selected_item):
        category = next((cat for cat in ["weapons", "armors", "shields", "charms"] if selected_item in getattr(inventory, cat, [])), None)
        if not category:
            return

        category_singular = category[:-1]  # Convert 'weapons' to 'weapon', 'armors' to 'armor', etc.
        equipped_item_key = f"equipped_{category_singular}"

        # Check if the item is already equipped
        if isinstance(selected_item, Armor):
            current_equipped_armor = inventory.equipped_armor.get(selected_item.armor_type)

            # Check if the armor is already equipped by name and zone_level
            if current_equipped_armor and current_equipped_armor.name == selected_item.name and current_equipped_armor.zone_level == selected_item.zone_level:
                return f"You already have {selected_item.name} equipped.", None
        else:
            current_equipped_item = getattr(inventory, equipped_item_key, None)
            if current_equipped_item and current_equipped_item.name == selected_item.name and current_equipped_item.zone_level == selected_item.zone_level:
                return f"You already have this {category_singular} equipped.", None

        # Handle item stacking and removal
        existing_item_in_inventory = next((item for item in getattr(inventory, category, []) if item.name == selected_item.name), None)
        if existing_item_in_inventory:
            if existing_item_in_inventory.stack == 1:
                getattr(inventory, category).remove(existing_item_in_inventory)
            else:
                existing_item_in_inventory.stack -= 1

        # Handle equipping logic
        if isinstance(selected_item, Armor):
            existing_armor_piece = inventory.equipped_armor.get(selected_item.armor_type)
            if existing_armor_piece:
                existing_armor_piece_in_inventory = next((item for item in inventory.armors if item.name == existing_armor_piece.name), None)
                if existing_armor_piece_in_inventory:
                    existing_armor_piece_in_inventory.stack += 1
                else:
                    inventory.armors.append(copy.deepcopy(existing_armor_piece))
            inventory.equipped_armor[selected_item.armor_type] = selected_item
        else:
            current_equipped_item = getattr(inventory, equipped_item_key, None)
            if current_equipped_item:
                existing_equipped_item = next((item for item in getattr(inventory, category, []) if item.name == current_equipped_item.name), None)
                if existing_equipped_item:
                    existing_equipped_item.stack += 1
                else:
                    getattr(inventory, category).append(copy.deepcopy(current_equipped_item))
            setattr(inventory, equipped_item_key, selected_item)

        # At the end of the method, simply return None if there's no specific message to send
        return None, None

color_mapping = {
    1: 0x969696,
    2: 0x15ce00,
    3: 0x0096f1,
    4: 0x9900ff,
    5: 0xfebd0d
}

def create_item_embed(action, item):
    if isinstance(item, str):  # Item doesn't exist, so it's a string (e.g., "Weapon", "Armor")
        title = f"{action.capitalize()} {item}"
        description = f"You don't have any {item} to {action}."
        thumbnail_url = generate_urls("Icons", "default")  # Set a default image for non-existent items
        embed_color = 0x3498db  # Default color
    else:  # Item exists, so it has a `name` attribute
        title = f"{action.capitalize()}ped {item.name}"
        description = f"You have {action}ped the {item.name}."
        thumbnail_url = generate_urls("Icons", item.name)
        embed_color = color_mapping.get(item.zone_level, 0x3498db)  # Fetch color based on zone_level or use default

    embed = discord.Embed(title=title, description=description, color=embed_color)
    embed.set_thumbnail(url=thumbnail_url)

    return embed


def setup(bot):
    bot.add_cog(BackpackCog(bot))
