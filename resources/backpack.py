from discord.ext import commands
import discord
from discord import Embed
import copy
from exemplars.exemplars import Exemplar
from utils import load_player_data, update_and_save_player_data, save_player_data, CommonResponses, refresh_player_from_data
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

        guild_id = ctx.guild.id
        author_id = str(ctx.author.id)
        player_data = load_player_data(guild_id, author_id)

        # Check if player data exists for the user
        if not player_data:
            embed = Embed(title="Captain Ner0",
                          description="Arr! What be this? No record of yer adventures? Start a new game with `/newgame` before I make ye walk the plank.",
                          color=discord.Color.dark_gold())
            embed.set_thumbnail(url=generate_urls("nero", "confused"))
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if player_data["location"] == "kraken" or player_data["location"] == "kraken_battle":
            await CommonResponses.during_kraken_battle_response(ctx)
            return

        # Display initial backpack view with Equip and Unequip buttons
        view = BackpackView(ctx)
        await ctx.respond(f"What would you like to do, {ctx.author.mention}?", view=view)


class BackpackView(discord.ui.View, CommonResponses):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.item_type_select = None
        self.original_selection = None

        # Load the player's data
        self.guild_id = self.ctx.guild.id
        self.author_id = str(self.ctx.user.id)
        self.player_data = load_player_data(self.guild_id, self.author_id)
        self.player = Exemplar(self.player_data["exemplar"],
                               self.player_data["stats"],
                               self.player_data["inventory"])

        self.inventory = self.player.inventory


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

        self.item_type_select = UnequipTypeSelect(action_type, options, self.author_id)
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

        self.item_type_select = EquipTypeSelect(action_type, options, self.author_id)
        self.add_item(self.item_type_select)

    def update_item_select_options(self):
        if self.item_type_select:
            selected_type = self.item_type_select.values[0]

            items = getattr(self.player.inventory, selected_type.lower() + "s", [])

            self.item_type_select.options.clear()

            for item in items:
                option = discord.SelectOption(label=item.name, value=item.name, emoji=getattr(item, "emoji", None))
                self.item_type_select.options.append(option)

    async def refresh_view(self, action_type):
        # Load the player's updated data
        self.player_data = load_player_data(self.ctx.guild.id, self.author_id)
        self.player.inventory = self.player_data["inventory"]

        if self.original_selection:
            # This will set the dropdown back to the originally selected type
            self.equip_add_item_type_select(f"{action_type}")

    @discord.ui.button(label="Equip", custom_id="backpack_equip", style=discord.ButtonStyle.primary, emoji="⚔️")
    async def equip(self, button, interaction):
        # Check if the user who interacted is the same as the one who initiated the view
        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player object from the latest player data
        self.player, self.player_data = await refresh_player_from_data(interaction)

        # Open the select menu for item types for the Equip action
        self.equip_add_item_type_select("equip")
        await interaction.response.edit_message(content="Choose an item type to equip:", view=self)

    @discord.ui.button(label="Unequip", custom_id="backpack_unequip", style=discord.ButtonStyle.blurple, emoji="⛔")
    async def unequip(self, button, interaction):
        # Check if the user who interacted is the same as the one who initiated the view
        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player object from the latest player data
        self.player, self.player_data = await refresh_player_from_data(interaction)

        # Open the select menu for item types for the Unequip action
        self.unequip_add_item_type_select("unequip")
        await interaction.response.edit_message(content="Choose an item type to unequip:", view=self)


    @discord.ui.button(label="Sort", custom_id="backpack_sort", style=discord.ButtonStyle.blurple, emoji="🔄")
    async def sort(self, button, interaction):
        # Check if the user who interacted is the same as the one who initiated the view
        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        self.clear_items()
        def sort_items(items, order):
            return sorted(items, key=lambda item: (getattr(item, 'zone_level', 0), order.index(item.name)))

        # Refresh player object from the latest player data
        self.player, self.player_data = await refresh_player_from_data(interaction)

        order = {
            "items": [
                "Charcoal", "Iron", "Steel", "Onyx", "Cannonball", "Pole", "Thick Pole",
                "Pine Strip", "Yew Strip", "Ash Strip", "Poplar Strip",
                "Flour", "Wheat", "Flax", "Linen", "Linen Thread", "Venison",
                "Sinew", "Rabbit Body", "Rabbit Meat", "Deer Parts",
                "Deer Skin", "Wolf Skin", "Glowing Essence", "Goblin Crown", "Leather",
                "Tough Leather", "Leather Straps", "Tough Leather Straps", "Rusty Spork"
            ],
            "trees": ["Pine", "Yew", "Ash", "Poplar"],
            "herbs": ["Ranarr", "Spirit Weed", "Snapdragon", "Bloodweed"],
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
            "charms": ["Woodcleaver", "Stonebreaker", "Loothaven", "Mightstone", "Ironhide"]
        }

        for category, sorting_order in order.items():
            if hasattr(self.player.inventory, category):
                category_items = getattr(self.player.inventory, category)
                sorted_items = sort_items(category_items, sorting_order)
                setattr(self.player.inventory, category, sorted_items)

        save_player_data(self.guild_id, self.author_id, self.player_data)
        await interaction.response.send_message(content="Inventory sorted.", view=self, ephemeral=True)

    @discord.ui.button(label="View", custom_id="backpack_inspect", style=discord.ButtonStyle.blurple, emoji="🔍")
    async def view(self, button, interaction):
        # Check if the user who interacted is the same as the one who initiated the view
        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player object from the latest player data
        self.player, self.player_data = await refresh_player_from_data(interaction)

        # Defer the response to prevent the interaction from timing out
        await interaction.response.defer()

        # Send a message to let the user know the image is being generated
        generating_message = await interaction.followup.send("Image being generated...Please wait.")

        # Generate the backpack image
        backpack_img = generate_backpack_image(interaction)
        with io.BytesIO() as image_binary:
            backpack_img.save(image_binary, 'PNG')
            image_binary.seek(0)

            # Delete the original message
            await generating_message.delete()

            # Send the generated image as an ephemeral message
            await interaction.followup.send(content=f"Here's your backpack, {interaction.user.mention}:",
                                            file=discord.File(fp=image_binary, filename='backpack_with_items.png'),
                                            ephemeral=False)

class UnequipTypeSelect(discord.ui.Select, CommonResponses):

    def __init__(self, action_type, options, author_id):
        self.action_type = action_type
        self.author_id = author_id
        super().__init__(placeholder=f"Choose an item type to {action_type}", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        # Check if the user who interacted is the same as the one who initiated the view
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        from citadel.crafting import Charm

        def get_existing_item_in_inventory(item_to_check):
            """Check if an item exists in the inventory and return it if found."""
            items_list = getattr(inventory, category_singular + "s", [])

            # Check for charm first as they might not have a zone level.
            if isinstance(item_to_check, Charm):
                return next((item for item in items_list if item.name == item_to_check.name), None)
            else:
                if inventory.has_item(item_to_check.name, getattr(item_to_check, 'zone_level', None)):
                    for item in items_list:
                        if item.name == item_to_check.name and getattr(item, 'zone_level', None) == getattr(
                                item_to_check, 'zone_level', None):
                            return item
            return None

        # Check if item exists in the inventory based on its name and optionally its zone level.
        def item_exists_in_inventory(item_to_check, items_list):
            if isinstance(item_to_check, Charm):
                return next((item for item in items_list if item.name == item_to_check.name), None)
            else:
                return next((item for item in items_list if
                             item.name == item_to_check.name and item.zone_level == item_to_check.zone_level), None)

        selected_value = self.values[0]
        view: BackpackView = self.view
        inventory = view.inventory

        # Handle Unequipping for single-slot categories
        if self.action_type == "unequip" and selected_value in ["Weapon", "Shield", "Charm"]:
            category_singular = selected_value.lower()
            equipped_item_key = f"equipped_{category_singular}"
            equipped_item = getattr(inventory, equipped_item_key, None)

            if equipped_item:
                if selected_value == "Charm":
                    existing_charm = get_existing_item_in_inventory(equipped_item)
                    if existing_charm:
                        existing_charm.stack += 1
                    else:
                        getattr(inventory, category_singular + "s").append(copy.deepcopy(equipped_item))
                else:
                    existing_item = get_existing_item_in_inventory(equipped_item)

                    if existing_item:  # If the item exists in the inventory
                        existing_item.stack += 1
                    else:
                        # Check for full inventory
                        if inventory.total_items_count() >= inventory.limit:
                            await interaction.response.send_message(
                                f"You don't have enough space in your inventory to unequip the {selected_value}.",
                                ephemeral=True)
                            return
                        else:
                            getattr(inventory, category_singular + "s").append(copy.deepcopy(equipped_item))

                # Unequip the item
                setattr(inventory, equipped_item_key, None)

                # Need to call both because Shield & Weapon
                self.view.player.update_total_armor()
                self.view.player.update_total_damage()

                update_and_save_player_data(interaction, inventory, view.player_data, player=self.view.player)
                embed = create_item_embed(self.action_type, equipped_item, self.view.player.stats.zone_level)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            else:
                embed = create_item_embed(self.action_type, selected_value,self.view.player.stats.zone_level)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        # Handle Unequipping for Armor type
        if self.action_type == "unequip" and selected_value == "Armor":

            equipped_armors = {armor_type: Armor.from_dict(armor_data) if isinstance(armor_data, dict) else armor_data
                               for armor_type, armor_data in inventory.equipped_armor.items() if armor_data is not None}

            if not equipped_armors:
                embed = create_item_embed(self.action_type, selected_value, self.view.player.stats.zone_level)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Clear existing options
            self.options.clear()
            for armor_type, armor in equipped_armors.items():
                option = discord.SelectOption(
                    label=armor.name,
                    value=armor_type,
                    emoji=get_emoji(ZONE_LEVEL_TO_EMOJI[armor.zone_level])
                )
                self.options.append(option)

            self.placeholder = f"Choose a specific {selected_value} to {self.action_type}"
            await interaction.response.edit_message(
                content=f"Choose a specific {selected_value} to {self.action_type}:", view=view)
            return

        selected_armor_type = self.values[0]
        selected_armor = inventory.equipped_armor.get(selected_armor_type)

        if not selected_armor:
            await interaction.response.send_message(f"No item found for type: {selected_armor_type}",
                                                    ephemeral=True)
            return

        if isinstance(selected_armor, dict):
            selected_armor_obj = Armor.from_dict(selected_armor)
        else:
            selected_armor_obj = selected_armor

        existing_armor = item_exists_in_inventory(selected_armor_obj, inventory.armors)

        if existing_armor:  # Stack the item
            existing_armor.stack += 1
        else:
            # Check if there's room in the inventory
            if inventory.total_items_count() >= inventory.limit:
                await interaction.response.send_message(
                    f"You don't have enough space in your inventory to unequip the {selected_armor_obj.name}.",
                    ephemeral=True)
                return
            else:
                inventory.armors.append(copy.deepcopy(selected_armor_obj))

        # Unequip the armor
        inventory.equipped_armor[selected_armor_type] = None

        self.view.player.update_total_armor()

        # Save data
        update_and_save_player_data(interaction, inventory, view.player_data, player=self.view.player)

        # Generate the embed for the unequipped item
        embed = create_item_embed(self.action_type, selected_armor_obj, self.view.player.stats.zone_level)

        # Reset the dropdown's options to its initial state
        self.options = [
            discord.SelectOption(label='Weapon', value='Weapon'),
            discord.SelectOption(label='Armor', value='Armor'),
            discord.SelectOption(label='Shield', value='Shield'),
            discord.SelectOption(label='Charm', value='Charm')
        ]

        # Update the UI and send the embed with a single response
        await interaction.response.edit_message(content="Choose an item type to unequip:", embed=embed, view=self.view)

class EquipTypeSelect(discord.ui.Select, CommonResponses):

    def __init__(self, action_type, options, author_id):
        self._values = []
        self.action_type = action_type
        self.author_id = author_id
        super().__init__(placeholder=f"Choose an item type to {action_type}", options=options, min_values=1,
                         max_values=1)
    @property
    def values(self):
        return self._values

    @values.setter
    def values(self, new_values):
        self._values = new_values

    async def callback(self, interaction: discord.Interaction):
        # Check if the user who interacted is the same as the one who initiated the view
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return
        view: BackpackView = self.view
        inventory = view.inventory
        selected_value = interaction.data['values'][0]

        view.original_selection = selected_value

        if selected_value in ["Weapon", "Armor", "Shield", "Charm"]:
            await self.handle_item_type_selection(interaction, inventory, selected_value)
        else:
            await self.handle_item_equipping(interaction, inventory, selected_value)

    @staticmethod
    def get_item_label(item, player):
        from citadel.crafting import Weapon, Shield
        """Return the appropriate label for the item, including defense or attack modifier if applicable."""
        label = item.name
        delta = ""  # Difference string, choice to apply later

        if isinstance(item, Weapon):
            equipped_weapon = player.inventory.equipped_weapon
            if equipped_weapon:
                diff = item.attack_modifier - equipped_weapon.attack_modifier
            else:
                diff = item.attack_modifier

            # Set delta based on diff value
            if diff >= 0:
                delta = f"(+{diff})"
            else:
                delta = f"({diff})"
            label += f" | {item.attack_modifier} Damage {delta}"

        elif isinstance(item, (Armor, Shield)):
            if isinstance(item, Armor):
                equipped_armor = player.inventory.equipped_armor[item.armor_type]
            else:
                equipped_armor = player.inventory.equipped_shield
            if equipped_armor:
                diff = item.defense_modifier - equipped_armor.defense_modifier
            else:
                diff = item.defense_modifier

            # Set delta based on diff value
            if diff >= 0:
                delta = f"(+{diff})"
            else:
                delta = f"({diff})"
            label += f" | {item.defense_modifier} Armor {delta}"
        return label

    async def handle_item_type_selection(self, interaction, inventory, item_type):
        items = getattr(inventory, item_type.lower() + "s", [])

        if not items:
            embed = create_item_embed(self.action_type, item_type, self.view.player.stats.zone_level)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        player = self.view.player

        # Modify the options creation to conditionally include the rarity and the detailed label
        if item_type == "Charm":
            self.options = [
                discord.SelectOption(
                    label=self.get_item_label(item, player),  # Change here for Charm
                    value=f"{item.name}",
                    emoji=get_emoji(item.name)
                )
                for item in items
            ]
        else:
            self.options = [
                discord.SelectOption(
                    label=self.get_item_label(item, player),  # Change here for other types
                    value=f"{item.name} ({ZONE_LEVEL_TO_RARITY[item.zone_level]})",
                    emoji=get_emoji(ZONE_LEVEL_TO_EMOJI[item.zone_level])
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
        from citadel.crafting import Weapon
        from probabilities import weapon_specialty_bonus
        selected_item = self.find_item_by_name(inventory, item_name)

        if not selected_item:
            return

        message, _ = await self.equip_item(interaction, inventory, selected_item)  # Unpack the tuple here

        # Define the weapon specialty mapping
        weapon_specialty = {
            "human": "Sword",
            "elf": "Bow",
            "orc": "Spear",
            "dwarf": "Hammer",
            "halfling": "Sword"
        }

        # Determine the content or embed you want to send
        if message:
            content_to_send = message
            embed_to_send = None
        else:
            content_to_send = None
            embed_to_send = create_item_embed(self.action_type, selected_item, self.view.player.stats.zone_level)

            # Check for specialty bonus and append the message
            if isinstance(selected_item, Weapon) and selected_item.wtype == weapon_specialty.get(self.view.player.name):
                # Convert the bonus to an integer percentage value
                bonus_percentage = int(weapon_specialty_bonus * 100)
                # Format the message with the integer percentage
                specialty_bonus_message = f"\n\n**{self.view.player.name.capitalize()} weapon bonus activated!** Your {selected_item.name} grants you an extra *{bonus_percentage}% damage bonus*."
                embed_to_send.description += specialty_bonus_message

        update_and_save_player_data(interaction, inventory, self.view.player_data)

        # Reset the dropdown's options to its initial state
        self.options = [
            discord.SelectOption(label='Weapon', value='Weapon'),
            discord.SelectOption(label='Armor', value='Armor'),
            discord.SelectOption(label='Shield', value='Shield'),
            discord.SelectOption(label='Charm', value='Charm')
        ]

        # Use a single call to send your response and update the UI
        await interaction.response.edit_message(content=content_to_send or "Choose an item type to equip:",
                                                embed=embed_to_send,
                                                view=self.view)

    def move_item_back_to_inventory(self, item, inventory_category):
        existing_item_in_inventory = next((i for i in inventory_category if
                                           i.name == item.name and
                                           (hasattr(i, 'zone_level') and i.zone_level == item.zone_level or not hasattr(
                                               i, 'zone_level'))), None)
        if existing_item_in_inventory:
            existing_item_in_inventory.stack += 1
        else:
            inventory_category.append(copy.deepcopy(item))

    @staticmethod
    def find_item_by_name(inventory, item_name_with_rarity):
        # Check if rarity exists
        if " (" in item_name_with_rarity:
            item_name, rarity = item_name_with_rarity.rsplit(" (", 1)
            rarity = rarity.rstrip(")")
        else:
            item_name = item_name_with_rarity
            rarity = None

        for category in ["weapons", "armors", "shields", "charms"]:
            if rarity:
                selected_item = next(
                    (item for item in getattr(inventory, category, [])
                     if item.name == item_name and ZONE_LEVEL_TO_RARITY.get(item.zone_level) == rarity),
                    None
                )
            else:
                selected_item = next(
                    (item for item in getattr(inventory, category, []) if item.name == item_name),
                    None
                )
            if selected_item:
                return selected_item

        return None

    def remove_item_from_inventory(self, item, inventory_category):
        existing_item_in_inventory = next((i for i in inventory_category if
                                           i.name == item.name and (hasattr(i,
                                                                            'zone_level') and i.zone_level == item.zone_level or not hasattr(
                                               i, 'zone_level'))), None)
        if existing_item_in_inventory:
            if hasattr(existing_item_in_inventory, 'stack') and existing_item_in_inventory.stack > 1:
                existing_item_in_inventory.stack -= 1
            else:
                inventory_category.remove(existing_item_in_inventory)

    async def equip_item(self, interaction, inventory, selected_item):
        from citadel.crafting import Charm, Weapon, Shield
        category = next(
            (cat for cat in ["weapons", "armors", "shields", "charms"] if selected_item in getattr(inventory, cat, [])),
            None)
        if not category:
            return

        category_singular = category[:-1]  # Convert 'weapons' to 'weapon', 'armors' to 'armor', etc.
        equipped_item_key = f"equipped_{category_singular}"

        current_equipped_item = getattr(inventory, equipped_item_key, None)

        # Check if the selected item is the same as the one currently equipped
        selected_item_name = self.get_item_name(selected_item)
        current_equipped_item_name = self.get_item_name(current_equipped_item)

        if selected_item_name == current_equipped_item_name and getattr(selected_item, 'zone_level', None) == getattr(
                current_equipped_item, 'zone_level', None):
            if isinstance(selected_item, Charm):
                return f"You already have the {selected_item_name} Charm equipped.", None
            else:
                return f"You already have the {selected_item_name} equipped.", None

        # Before handling equipping logic
        # Check for inventory space based on what you're trying to equip
        if isinstance(selected_item, Armor):
            existing_armor_piece = inventory.equipped_armor.get(selected_item.armor_type)
            if existing_armor_piece:
                existing_item_in_inventory = inventory.has_item(existing_armor_piece.name,
                                                                getattr(existing_armor_piece, 'zone_level', None))
            else:
                existing_item_in_inventory = False

            is_single_stack = selected_item.stack == 1 if hasattr(selected_item, "stack") else False

            if existing_armor_piece and not existing_item_in_inventory:
                if inventory.total_items_count() >= inventory.limit and not is_single_stack:
                    return f"Your inventory is full. Make space before equipping {selected_item.name}.", None

        elif isinstance(selected_item, Weapon) and selected_item.wtype == "Bow":
            current_weapon = getattr(inventory, "equipped_weapon", None)
            current_shield = getattr(inventory, "equipped_shield", None)
            required_slots = 0

            if current_weapon:
                current_item_in_inventory = inventory.has_item(current_weapon.name,
                                                               getattr(current_weapon, 'zone_level', None))
                if not current_item_in_inventory:
                    required_slots += 1

            if current_shield:
                current_item_in_inventory = inventory.has_item(current_shield.name,
                                                               getattr(current_shield, 'zone_level', None))
                if not current_item_in_inventory:
                    required_slots += 1

            # Adjust for the scenario where the bow is a single stack
            if hasattr(selected_item, 'stack') and selected_item.stack == 1:
                required_slots -= 1  # Because it'll just swap places with the current weapon

            if inventory.total_items_count() + required_slots > inventory.limit:
                return f"Equipping {selected_item.name} requires additional space for removing a Weapon and Shield. Please make space.", None

            # Now, actually remove the current weapon and shield
            if current_weapon:
                self.move_item_back_to_inventory(current_weapon, inventory.weapons)
                inventory.equipped_weapon = None

            if current_shield:
                self.move_item_back_to_inventory(current_shield, inventory.shields)
                inventory.equipped_shield = None

            # Equip the bow to the weapon slot and set the shield slot to None
            inventory.equipped_weapon = copy.deepcopy(selected_item)
            if hasattr(inventory.equipped_weapon, 'stack'):
                inventory.equipped_weapon.stack = 1
            inventory.equipped_shield = None
            # Remove the bow from the inventory after equipping
            self.remove_item_from_inventory(selected_item, inventory.weapons)
            return None, None


        elif isinstance(selected_item, Charm):
            # Don't want charms being calculated in for an inventory space, equip logic handled in else block below
            pass

        else:
            current_equipped_item = getattr(inventory, f"equipped_{selected_item.__class__.__name__.lower()}", None)
            if current_equipped_item:
                # Check if there's an instance of the current equipped item in the inventory
                current_item_in_inventory = inventory.has_item(current_equipped_item.name,
                                                               getattr(current_equipped_item, 'zone_level', None))

                # Check if the selected item has a stack of 1
                is_single_stack = hasattr(selected_item, 'stack') and selected_item.stack == 1

                # If the current equipped item isn't in the inventory and the inventory is full and the selected item isn't a single stack item
                if not current_item_in_inventory and inventory.total_items_count() >= inventory.limit and not is_single_stack:
                    return f"Your inventory is full. Make space before equipping {selected_item.name}.", None

        # Handle item stacking and removal
        existing_item_in_inventory = next((item for item in getattr(inventory, category, []) if
                                           item.name == selected_item.name and (hasattr(item,
                                                                                        'zone_level') and item.zone_level == selected_item.zone_level or not hasattr(
                                               item, 'zone_level'))), None)
        if existing_item_in_inventory:
            if existing_item_in_inventory.stack > 1:
                existing_item_in_inventory.stack -= 1
            else:
                getattr(inventory, category).remove(existing_item_in_inventory)

        # Check if trying to equip a shield while a bow is equipped
        if isinstance(selected_item, Shield):
            current_weapon = getattr(inventory, "equipped_weapon", None)
            if current_weapon and isinstance(current_weapon, Weapon) and current_weapon.wtype == "Bow":
                return "You must first unequip your bow before equipping a shield.", None

        # Handle equipping logic
        if isinstance(selected_item, Armor):
            existing_armor_piece = inventory.equipped_armor.get(selected_item.armor_type)
            if existing_armor_piece:
                self.move_item_back_to_inventory(existing_armor_piece, inventory.armors)
            # Create a deep copy of selected_item for equipping
            equipped_selected_item = copy.deepcopy(selected_item)
            # Set the stack of the equipped item to 1
            if hasattr(equipped_selected_item, 'stack'):
                equipped_selected_item.stack = 1
            inventory.equipped_armor[selected_item.armor_type] = equipped_selected_item

            self.view.player.update_total_armor()

        else:
            current_equipped_item = getattr(inventory, equipped_item_key, None)
            if current_equipped_item:
                self.move_item_back_to_inventory(current_equipped_item, getattr(inventory, category))
            # Create a deep copy of selected_item for equipping
            equipped_selected_item = copy.deepcopy(selected_item)
            # Set the stack of the equipped item to 1
            if hasattr(equipped_selected_item, 'stack'):
                equipped_selected_item.stack = 1
            setattr(inventory, equipped_item_key, equipped_selected_item)

            # Need to call both because Shield & Weapon
            self.view.player.update_total_armor()
            self.view.player.update_total_damage()

        update_and_save_player_data(interaction, inventory, self.view.player_data, player=self.view.player)

        # At the end of the method, simply return None if there's no specific message to send
        return None, None

color_mapping = {
    1: 0x969696,
    2: 0x15ce00,
    3: 0x0096f1,
    4: 0x9900ff,
    5: 0xfebd0d
}

def create_item_embed(action, item, player_zone_level):
    if isinstance(item, str):  # Item doesn't exist, so it's a string (e.g., "Weapon", "Armor")
        title = f"{action.capitalize()} {item}"
        description = f"You don't have any {item} to {action}."
        thumbnail_url = generate_urls("Icons", "default")  # Set a default image for non-existent items
        embed_color = color_mapping.get(player_zone_level, 0x3498db)
    else:  # Item exists, so it has a `name` attribute
        title = f"{action.capitalize()}ped {item.name}"
        description = f"You have {action}ped the {item.name}."
        thumbnail_url = generate_urls("Icons", item.name)
        # Check if the item has a zone_level attribute
        if hasattr(item, 'zone_level'):
            embed_color = color_mapping.get(item.zone_level, 0x3498db)
        else:
            embed_color = color_mapping.get(player_zone_level, 0x3498db)  # Default color based on zone level

    embed = discord.Embed(title=title, description=description, color=embed_color)
    embed.set_thumbnail(url=thumbnail_url)

    return embed


def setup(bot):
    bot.add_cog(BackpackCog(bot))
