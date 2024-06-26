from resources.item import Item
import discord
from discord import Embed
from images.urls import generate_urls
from emojis import get_emoji
from exemplars.exemplars import Exemplar
from resources.ore import Ore
from resources.potion import Potion
from resources.materium import Materium
from utils import CommonResponses, refresh_player_from_data, get_server_setting

class Weapon(Item):
    def __init__(self, name, wtype, attack_modifier, special_attack, value, zone_level, description=None, stack=1):
        super().__init__(name, description, value)
        self.zone_level = zone_level
        self.wtype = wtype
        self.attack_modifier = attack_modifier
        self.special_attack = special_attack
        self.stack = stack

    def to_dict(self):
        weapon_data = super().to_dict()
        weapon_data["wtype"] = self.wtype
        weapon_data["attack_modifier"] = self.attack_modifier
        weapon_data["special_attack"] = self.special_attack
        weapon_data["stack"] = self.stack
        weapon_data["zone_level"] = self.zone_level
        return weapon_data

    @classmethod
    def from_dict(cls, data):
        return cls(name=data["name"], wtype=data["wtype"], attack_modifier=data["attack_modifier"], special_attack=data["special_attack"],
                   value=data.get("value"), zone_level=data.get("zone_level", 1), description=data.get("description"), stack=data.get("stack", 1))
class ArmorType:
    CHEST = "chest"
    BOOTS = "boots"
    GLOVES = "gloves"

class Armor(Item):
    def __init__(self, name, zone_level, defense_modifier, armor_type, description=None, value=None, stack=1):
        super().__init__(name, description, value)
        self.zone_level = zone_level
        self.defense_modifier = defense_modifier
        self.armor_type = armor_type
        self.stack = stack
    def to_dict(self):
        armor_data = super().to_dict()
        armor_data["defense_modifier"] = self.defense_modifier
        armor_data["armor_type"] = self.armor_type
        armor_data["stack"] = self.stack
        armor_data["zone_level"] = self.zone_level
        return armor_data

    @classmethod
    def from_dict(cls, data):
        if not all(key in data for key in ["name", "defense_modifier", "armor_type"]):
            raise ValueError("Armor data is missing necessary keys.")

        # Additional validation could be added to ensure the armor_type is valid
        if data["armor_type"] not in [ArmorType.CHEST, ArmorType.BOOTS, ArmorType.GLOVES]:
            raise ValueError(f"Invalid armor type: {data['armor_type']}")

        return cls(name=data["name"], defense_modifier=data["defense_modifier"], armor_type=data["armor_type"],
                   description=data.get("description"), value=data.get("value"), stack=data.get("stack", 1), zone_level=data.get("zone_level"))

class Shield(Item):
    def __init__(self, name, zone_level, defense_modifier, description=None, value=None, stack=1):
        super().__init__(name, description, value)
        self.zone_level = zone_level
        self.defense_modifier = defense_modifier
        self.stack = stack

    def to_dict(self):
        shield_data = super().to_dict()
        shield_data["defense_modifier"] = self.defense_modifier
        shield_data["stack"] = self.stack
        shield_data["zone_level"] = self.zone_level
        return shield_data

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            defense_modifier=data["defense_modifier"],
            description=data.get("description"),
            value=data.get("value"),
            stack=data.get("stack", 1),
            zone_level=data.get("zone_level")
        )

class Charm(Item):
    def __init__(self, name, description=None, value=None, stack=1):
        super().__init__(name, description, value)
        self.stack = stack

    def to_dict(self):
        charm_data = super().to_dict()
        charm_data["stack"] = self.stack
        return charm_data

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            description=data.get("description"),
            value=data.get("value"),
            stack=data.get("stack", 1)
        )

# Recipe Classes
class Recipe:
    def __init__(self, result, *ingredients):
        self.result = result
        self.ingredients = ingredients  # List of tuples (item, quantity)

    def can_craft(self, inventory):
        for ingredient, quantity in self.ingredients:
            available_quantity = inventory.get_item_quantity(ingredient.name)
            if available_quantity < quantity:
                return False
        return True

def stamina_bar(current, max_stamina):
    bar_length = 20  # Fixed bar length
    stamina_percentage = current / max_stamina
    filled_length = round(bar_length * stamina_percentage)

    # Calculate how many '◼' symbols to display
    filled_symbols = '◼' * filled_length

    # Calculate how many '◻' symbols to display
    empty_symbols = '◻' * (bar_length - filled_length)
    return filled_symbols + empty_symbols

class CraftingStation:
    def __init__(self, name):
        self.name = name
        self.recipes = []

    def add_recipe(self, recipe):
        self.recipes.append(recipe)

    def craft(self, recipe_name, player, player_data, guild_id, author_id):
        from utils import save_player_data

        recipe = next((r for r in self.recipes if r.result.name == recipe_name), None)

        # Check if the result of the crafting operation is a Charm or Potion, or an auto-consume item like 'Bread' or 'Trencher'.
        # If it is, skip the inventory check and allow crafting regardless of inventory space.
        if not isinstance(recipe.result, (Charm, Potion)) and recipe.result.name not in ["Bread", "Trencher"]:
            item_already_exists = player.inventory.has_item(recipe.result.name,
                                                            getattr(recipe.result, 'zone_level', None))
            if not item_already_exists and player.inventory.total_items_count() >= player.inventory.limit:
                return "Inventory is full. Please make some room before crafting."

        # Remove ingredients from inventory
        for ingredient, quantity in recipe.ingredients:
            player.inventory.remove_item(ingredient.name, quantity)

        # Handle auto-consume items separately
        if recipe.result.name == "Bread":
            added_stamina = 10
            player.stats.stamina = min(player.stats.stamina + added_stamina, player.stats.max_stamina)
            return recipe.result  # Return the Bread item even though it's consumed
        elif recipe.result.name == "Trencher":
            player.stats.stamina = player.stats.max_stamina
            return recipe.result  # Return the Trencher item even though it's consumed

        # Add item to inventory for other items
        player.inventory.add_item_to_inventory(recipe.result)

        save_player_data(guild_id, author_id, player_data)

        return recipe.result

class CraftView(discord.ui.View):
    def __init__(self, player, player_data, station, selected_recipe, crafted_item, guild_id, author_id, disabled=True, show_added_to_backpack=True):
        super().__init__()
        self.player = player
        self.player_data = player_data
        self.author_id = author_id
        self.disabled = disabled
        self.crafted_item = crafted_item
        self.message = None

        # Adjust here to control footer text based on the context
        self.embed_generator = EmbedGenerator(player, selected_recipe, crafted_item, player.stats.zone_level, show_added_to_backpack)

        # Add craft and refresh buttons to the view
        self.add_item(CraftButton(disabled, station, selected_recipe, player, player_data, guild_id, author_id))
        self.add_item(RefreshButton())

class EmbedGenerator:
    def __init__(self, player, selected_recipe, crafted_item, zone_level, show_added_to_backpack=True):
        self.player = player
        self.selected_recipe = selected_recipe
        self.crafted_item = crafted_item
        self.zone_level = zone_level
        self.show_added_to_backpack = show_added_to_backpack

    def generate_embed(self):
        zone_emoji_mapping = {
            1: 'common_emoji',
            2: 'uncommon_emoji',
            3: 'rare_emoji',
            4: 'epic_emoji',
            5: 'legendary_emoji'
        }
        color_mapping = {
            1: 0x969696,
            2: 0x15ce00,
            3: 0x0096f1,
            4: 0x9900ff,
            5: 0xfebd0d
        }
        zone_rarity = {
            1: '(Common)',
            2: '(Uncommon)',
            3: '(Rare)',
            4: '(Epic)',
            5: '(Legendary)'
        }

        zone_emoji = get_emoji(zone_emoji_mapping[self.zone_level])
        embed_color = color_mapping[self.zone_level]
        zone_rarity_identifier = zone_rarity[self.zone_level]

        # Adjust title based on item type
        item_title = f"{self.selected_recipe.result.name}: Auto Consume" if self.selected_recipe.result.name in [
            "Bread", "Trencher"] else f"{self.selected_recipe.result.name} {zone_emoji}"

        message_content = self.construct_message_content()
        if self.selected_recipe.result.name in ["Bread", "Trencher"]:
            message_content += self.add_stamina_bar()

        crafted_item_url = generate_urls('Icons', self.selected_recipe.result.name.replace(" ", "%20"))

        embed = discord.Embed(title=item_title, description=message_content, color=embed_color)
        embed.set_thumbnail(url=crafted_item_url)
        self.set_footer(embed, zone_rarity_identifier)
        return embed

    def construct_message_content(self):
        ingredients_list = self.check_inventory()
        item_details = []

        if hasattr(self.crafted_item, 'attack_modifier') and self.crafted_item.attack_modifier:
            item_details.append(f"**Damage:** {self.crafted_item.attack_modifier}")
        if hasattr(self.crafted_item, 'defense_modifier') and self.crafted_item.defense_modifier:
            item_details.append(f"**Armor:** {self.crafted_item.defense_modifier}")
        if hasattr(self.crafted_item, 'special_attack') and self.crafted_item.special_attack:
            item_details.append(f"**Special Attack:** {self.crafted_item.special_attack}")
        if hasattr(self.crafted_item, 'description') and self.crafted_item.description:
            item_details.append(f"**Description:** {self.crafted_item.description}")

        message_content = "\n".join(ingredients_list + ([""] if item_details else []) + item_details)
        return message_content

    def check_inventory(self):
        ingredients_list = []
        for ingredient, quantity in self.selected_recipe.ingredients:
            available_quantity = self.player.inventory.get_item_quantity(ingredient.name)
            # Format the quantities with commas
            formatted_available = "{:,}".format(available_quantity)
            formatted_required = "{:,}".format(quantity)
            ingredients_list.append(
                f"{'✅' if available_quantity >= quantity else '❌'} {ingredient.name} {formatted_available}/{formatted_required}"
            )
        return ingredients_list

    def set_footer(self, embed, zone_rarity_identifier):
        item_count = self.player.inventory.get_item_quantity(self.crafted_item.name,
                                                             getattr(self.crafted_item, 'zone_level', None))
        formatted_item_count = "{:,}".format(item_count)  # Format the item count with commas

        if self.show_added_to_backpack:
            if self.selected_recipe.result.name not in ["Bread", "Trencher"]:
                if isinstance(self.crafted_item, (Armor, Weapon, Shield)):
                    embed.set_footer(
                        text=f"+1 {self.crafted_item.name}\n{formatted_item_count} in backpack {zone_rarity_identifier}")
                else:
                    embed.set_footer(text=f"+1 {self.crafted_item.name}\n{formatted_item_count} in backpack")
        else:
            if self.selected_recipe.result.name not in ["Bread", "Trencher"]:
                if isinstance(self.crafted_item, (Armor, Weapon, Shield)):
                    embed.set_footer(
                        text=f"{formatted_item_count} in backpack {zone_rarity_identifier}")
                else:
                    embed.set_footer(text=f"{formatted_item_count} in backpack")

    def add_stamina_bar(self):
        stamina_progress = stamina_bar(self.player.stats.stamina, self.player.stats.max_stamina)
        stamina_emoji = get_emoji('stamina_emoji')
        stamina_message = f"\n\n{stamina_emoji} Stamina: {stamina_progress} {self.player.stats.stamina}/{self.player.stats.max_stamina}"
        if self.player.stats.stamina >= self.player.stats.max_stamina:
            stamina_message += " **FULL!**"
        return stamina_message

class CraftHandler:
    def __init__(self, player, player_data, selected_recipe, station, guild_id, author_id):
        self.player = player
        self.player_data = player_data
        self.selected_recipe = selected_recipe
        self.station = station
        self.guild_id = guild_id
        self.author_id = author_id

    def craft_item(self):
        crafted_item = self.station.craft(self.selected_recipe.result.name, self.player, self.player_data, self.guild_id, self.author_id)
        if isinstance(crafted_item, str):
            return None, crafted_item  # Returns error message if crafting failed.
        return crafted_item, None

class RefreshButton(discord.ui.Button, CommonResponses):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.secondary, label="🔄")

    async def callback(self, interaction: discord.Interaction):

        craft_view = self.view

        # Refresh player object from the latest player data
        craft_view.player, craft_view.player_data = await refresh_player_from_data(interaction)

        # Check if the player is not in the citadel
        if craft_view.player_data["location"] != "citadel":
            await self.not_in_citadel_response(interaction)
            return

        # Check if stamina is full only for Bread or Trencher
        if craft_view.crafted_item and craft_view.crafted_item.name in ["Bread", "Trencher"]:
            if craft_view.player.stats.stamina >= craft_view.player.stats.max_stamina:
                for item in craft_view.children:
                    if isinstance(item, CraftButton):
                        item.disabled = True  # Disable crafting if stamina is full
                # Update the view immediately if no crafting is possible
                new_embed = craft_view.embed_generator.generate_embed()
                await interaction.response.edit_message(embed=new_embed, view=craft_view)
                return

        # Recheck material availability for other items
        can_craft_again = True
        for ingredient, quantity in craft_view.embed_generator.selected_recipe.ingredients:
            available_quantity = craft_view.player.inventory.get_item_quantity(ingredient.name)
            if available_quantity < quantity:
                can_craft_again = False
                break

        # Find the craft button in the view and update its disabled state
        for item in craft_view.children:
            if isinstance(item, CraftButton):
                item.disabled = not can_craft_again

        # Update embed generator without adding to backpack info
        craft_view.embed_generator = EmbedGenerator(craft_view.player,
                                                    craft_view.embed_generator.selected_recipe,
                                                    craft_view.crafted_item, craft_view.player.stats.zone_level,
                                                    show_added_to_backpack=False)

        # Regenerate the embed with the updated crafted item
        new_embed = craft_view.embed_generator.generate_embed()
        await interaction.response.edit_message(embed=new_embed, view=craft_view)

class CraftButton(discord.ui.Button, CommonResponses):
    def __init__(self, disabled, station, selected_recipe, player, player_data, guild_id, author_id):
        super().__init__(label="Craft", style=discord.ButtonStyle.primary, disabled=disabled)
        self.station = station
        self.selected_recipe = selected_recipe
        self.player = player
        self.player_data = player_data
        self.guild_id = guild_id
        self.author_id = author_id

    async def callback(self, interaction: discord.Interaction):
        from utils import save_player_data, refresh_player_from_data

        # Refresh player object from the latest player data
        self.player, self.player_data = await refresh_player_from_data(interaction)

        # Check if the player is not in the citadel
        if self.player_data["location"] != "citadel":
            await self.not_in_citadel_response(interaction)
            return

        # Verify that the player has all required ingredients
        can_craft_again = True
        for ingredient, quantity in self.selected_recipe.ingredients:
            available_quantity = self.player.inventory.get_item_quantity(ingredient.name)
            if available_quantity < quantity:
                await interaction.response.send_message("Missing ingredients. Please refresh crafting window.", ephemeral=True)
                return

        crafted_item= self.station.craft(self.selected_recipe.result.name, self.player, self.player_data,
                                                 self.guild_id, self.author_id)

        # Update the view with the new crafted item
        self.view.crafted_item = crafted_item
        # If crafted_item is a string, it indicates an error message, handle accordingly
        if isinstance(crafted_item, str):
            await interaction.response.send_message(crafted_item, ephemeral=True)
            return

        # Check player's inventory after crafting for required ingredients
        for ingredient, quantity in self.selected_recipe.ingredients:
            if self.player.inventory.get_item_quantity(ingredient.name) < quantity:
                can_craft_again = False
                break

        # Update player stamina data after crafting bread or trencher
        if self.selected_recipe.result.name in ["Bread", "Trencher"]:
            if self.selected_recipe.result.name == "Bread":
                self.player_data["stats"]["stamina"] = self.player.stats.stamina
            elif self.selected_recipe.result.name == "Trencher":
                self.player.stats.stamina = self.player.stats.max_stamina
                self.player_data["stats"]["stamina"] = self.player.stats.stamina
            save_player_data(self.guild_id, self.author_id, self.player_data)

            # If stamina is full, disable the button
            if self.player.stats.stamina >= self.player.stats.max_stamina:
                can_craft_again = False

        # Disable the button if crafting cannot continue
        self.disabled = not can_craft_again

        # Update the view with the new crafted item
        self.view.crafted_item = crafted_item
        self.view.embed_generator.crafted_item = crafted_item

        # Generate and send the embed
        embed_generator = EmbedGenerator(self.player, self.selected_recipe, crafted_item, self.player.stats.zone_level)
        embed = embed_generator.generate_embed()
        await interaction.response.edit_message(embed=embed, view=self.view)

class CraftingSelect(discord.ui.Select, CommonResponses):
    def __init__(self, crafting_station, interaction, author_id, context=None):
        self.crafting_station = crafting_station
        self.interaction = interaction
        self.author_id = author_id

        # Load the player data here
        from utils import load_player_data
        self.guild_id = self.interaction.guild.id
        self.author_id = str(self.interaction.user.id)
        self.player_data = load_player_data(self.guild_id, self.author_id)
        self.player = Exemplar(self.player_data["exemplar"],
                               self.player_data["stats"],
                               self.guild_id,
                               self.player_data["inventory"])


        # Define select options based on the provided recipes
        options = [
            discord.SelectOption(
                label=self._get_item_label(recipe.result),
                value=recipe.result.name,
                emoji=get_emoji(recipe.result.name)
            )
            for recipe in self.crafting_station.recipes
        ]

        # Conditional placeholder message
        placeholder_message = "Choose an item to craft"
        if context == "tavern":
            placeholder_message = f"What brings you in today?"

        # Initialize the Select element with the generated options
        super().__init__(placeholder=placeholder_message, options=options, min_values=1, max_values=1)

    def _get_item_label(self, item):
        """Return the appropriate label for the item, including defense or attack modifier if applicable."""
        label = item.name
        delta = ""  # Difference string, choice to apply later

        if isinstance(item, Weapon):
            equipped_weapon = self.player.inventory.equipped_weapon
            if equipped_weapon:
                diff = item.attack_modifier - equipped_weapon.attack_modifier
            else:
                diff = item.attack_modifier
            if diff > 0:
                delta = f"(+{diff})"
            elif diff < 0:
                delta = f"({diff})"
            label += f" [{item.attack_modifier} Damage]"

        elif isinstance(item, (Armor, Shield)):
            if isinstance(item, Armor):
                equipped_armor = self.player.inventory.equipped_armor[item.armor_type]
            else:
                equipped_armor = self.player.inventory.equipped_shield
            if equipped_armor:
                diff = item.defense_modifier - equipped_armor.defense_modifier
            else:
                diff = item.defense_modifier
            if diff > 0:
                delta = f"(+{diff})"
            elif diff < 0:
                delta = f"({diff})"
            label += f" [{item.defense_modifier} Armor]"
        return label

    async def callback(self, interaction: discord.Interaction):

        # Check authorization
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player object from the latest player data
        self.player, self.player_data = await refresh_player_from_data(interaction)

        # Check if the player is not in the citadel
        if self.player_data["location"] != "citadel":
            await self.not_in_citadel_response(interaction)
            return

        from nero.TES import handle_three_eyed_snake_selection

        # Check for the 3ES selection
        if self.values[0] == 'three_eyed_snake':
            await handle_three_eyed_snake_selection(interaction)
        else:

            # Get zone level from player stats
            zone_level = self.player.stats.zone_level

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

            # Get the appropriate emoji and color for the current zone
            zone_emoji = get_emoji(zone_emoji_mapping.get(zone_level))
            embed_color = color_mapping.get(zone_level)

            # Retrieve the recipe for the selected item.
            selected_recipe = next((r for r in self.crafting_station.recipes if r.result.name == self.values[0]), None)

            # Check player's inventory for quantity of the crafted item with zone_level rarity
            if isinstance(selected_recipe.result, (Weapon, Armor, Shield)):
                crafted_item_count = self.player.inventory.get_item_quantity(selected_recipe.result.name, zone_level)
            # Check player's inventory for quantity of other items without zone_level rarity
            else:
                crafted_item_count = self.player.inventory.get_item_quantity(selected_recipe.result.name)

            embed_title = f"{selected_recipe.result.name} {zone_emoji}"
            if selected_recipe.result.name == "Bread":
                embed_title = "Bread: Auto Consume"
            elif selected_recipe.result.name == "Trencher":
                embed_title = "Trencher: Auto Consume"

            # Check player's inventory for required ingredients.
            ingredients_list = []
            can_craft = True
            for ingredient, required_quantity in selected_recipe.ingredients:
                available_quantity = self.player.inventory.get_item_quantity(ingredient.name)
                if available_quantity < required_quantity:
                    can_craft = False
                    # Format the quantities with commas
                    formatted_available = "{:,}".format(available_quantity)
                    formatted_required = "{:,}".format(required_quantity)
                    ingredients_list.append(f"❌ {ingredient.name} {formatted_available}/{formatted_required}")
                else:
                    # Format the quantities with commas
                    formatted_available = "{:,}".format(available_quantity)
                    formatted_required = "{:,}".format(required_quantity)
                    ingredients_list.append(f"✅ {ingredient.name} {formatted_available}/{formatted_required}")

            # Construct the embed message.
            message_content = "\n".join(ingredients_list)

            # Add an extra newline to separate the ingredients from the attributes
            message_content += "\n"

            # Check and include damage if attack_modifier exists
            if hasattr(selected_recipe.result, "attack_modifier") and selected_recipe.result.attack_modifier is not None:
                message_content += f"\n**Damage:** {selected_recipe.result.attack_modifier}"

            # Check and include armor if defense_modifier exists
            if hasattr(selected_recipe.result, "defense_modifier") and selected_recipe.result.defense_modifier is not None:
                message_content += f"\n**Armor:** {selected_recipe.result.defense_modifier}"

            # Check and include special attacks if special_attack exists
            if hasattr(selected_recipe.result, "special_attack") and selected_recipe.result.special_attack is not None:
                message_content += f"\n**Special Attack:** {selected_recipe.result.special_attack}"

            # Check and include the description of the selected item, if it exists
            if hasattr(selected_recipe.result, "description") and selected_recipe.result.description:
                message_content += f"\n**Description:** {selected_recipe.result.description}"

            crafted_item_url = generate_urls('Icons', selected_recipe.result.name.replace(" ", "%20"))
            embed = Embed(title=embed_title, description=message_content, color=embed_color)
            embed.set_thumbnail(url=crafted_item_url)

            # Setting the footer with crafted item count in backpack, except for Bread and Trencher
            if selected_recipe.result.name not in ["Bread", "Trencher"]:
                formatted_crafted_item_count = "{:,}".format(
                    crafted_item_count)  # Format the crafted item count with commas
                footer_text = f"{formatted_crafted_item_count} in backpack"

                # Check if the item class is Armor, Weapon, or Shield and adjust the footer text
                if isinstance(selected_recipe.result, (Armor, Weapon, Shield)):
                    rarity_label = zone_rarity.get(zone_level)
                    footer_text += f" {rarity_label}"

                embed.set_footer(text=footer_text)

            # Check if it's "Bread" or "Trencher" and add stamina bar to description
            if selected_recipe.result.name in ["Bread", "Trencher"]:
                stamina_progress = stamina_bar(self.player.stats.stamina, self.player.stats.max_stamina)
                stamina_emoji = get_emoji('stamina_emoji')

                # Check if stamina is full and modify the message accordingly
                if self.player.stats.stamina >= self.player.stats.max_stamina:
                    stamina_message = f"\n\n{stamina_emoji} Stamina: {stamina_progress} {self.player.stats.stamina}/{self.player.stats.max_stamina} **FULL!**"
                    can_craft = False  # Disable the Craft button if stamina is full
                else:
                    stamina_message = f"\n\n{stamina_emoji} Stamina: {stamina_progress} {self.player.stats.stamina}/{self.player.stats.max_stamina}"

                embed.description += stamina_message

            # Initialize CraftView with the crafted item
            view = CraftView(
                player=self.player,
                player_data=self.player_data,
                station=self.crafting_station,
                selected_recipe=selected_recipe,
                crafted_item=selected_recipe.result,
                guild_id=self.guild_id,
                author_id=self.author_id,
                disabled=not can_craft
            )

            message = await interaction.response.send_message(embed=embed, ephemeral=True, view=view)
            view.message = message

def create_crafting_stations(interaction, station_name=None):
    from utils import load_player_data

    guild_id = interaction.guild.id
    author_id = str(interaction.user.id)
    player_data = load_player_data(guild_id, author_id)
    player = Exemplar(player_data["exemplar"],
                      player_data["stats"],
                      guild_id,
                      player_data["inventory"])

    # Get zone level from player stats
    zone_level = player.stats.zone_level

    # Defining All Items
    charcoal = Item("Charcoal")
    iron = Item("Iron")
    carbon = Ore("Carbon")
    steel = Item("Steel")
    pine = Item("Pine")
    iron_ore = Item("Iron Ore")
    coal = Item("Coal")
    leather_straps = Item("Leather Straps")
    thick_pole = Item("Thick Pole")
    glowing_essence = Item("Glowing Essence")
    pole = Item("Pole")
    onyx = Item("Onyx")
    cannonball = Item("Cannonball")
    tough_leather_straps = Item("Tough Leather Straps")
    ash = Item("Ash")
    yew = Item("Yew")
    poplar = Item("Poplar")
    pine_strip = Item("Pine Strip")
    ash_strip = Item("Ash Strip")
    yew_strip = Item("Yew Strip")
    poplar_strip = Item("Poplar Strip")
    wheat = Item("Wheat")
    flour = Item("Flour")
    bread = Item("Bread", description="Restore 10 Stamina")
    deer_part = Item("Deer Parts")
    rabbit_body = Item("Rabbit Body")
    venison = Item("Venison")
    sinew = Item("Sinew")
    rabbit_meat = Item("Rabbit Meat")
    deer_skin = Item("Deer Skin")
    wolf_skin = Item("Wolf Skin")
    leather = Item("Leather")
    trencher = Item("Trencher", description="Restore Stamina to 100%")
    tough_leather = Item("Tough Leather")
    linen = Item("Linen")
    linen_thread = Item("Linen Thread")
    flax = Item("Flax")
    ranarr = Item("Ranarr")
    spirit_weed = Item("Spirit Weed")
    snapdragon = Item("Snapdragon")
    bloodweed = Item("Bloodweed")
    materium = Materium()
    goblin_crown = Item("Goblin Crown")

    # Shields
    buckler = Shield("Buckler", defense_modifier=round(1 * zone_level), value=30 + round(zone_level ** 2) * 1,
                     zone_level=zone_level)
    small_shield = Shield("Small Shield", defense_modifier=round(3 * zone_level),
                          value=round(40 + (zone_level ** 2) * 1.5), zone_level=zone_level)
    large_shield = Shield("Large Shield", defense_modifier=round(5 * zone_level), value=50 + round(zone_level ** 2) * 2,
                          zone_level=zone_level)

    # Armors
    brigandine_armor = Armor("Brigandine Armor", defense_modifier=round(14 * zone_level), armor_type=ArmorType.CHEST,
                             value=80 + round(zone_level ** 2) * 5, zone_level=zone_level)
    brigandine_boots = Armor("Brigandine Boots", defense_modifier=round(5 * zone_level), armor_type=ArmorType.BOOTS,
                             value=50 + round(zone_level ** 2) * 3, zone_level=zone_level)
    brigandine_gloves = Armor("Brigandine Gloves", defense_modifier=round(9 * zone_level),
                              armor_type=ArmorType.GLOVES, value=50 + round(zone_level ** 2) * 3, zone_level=zone_level)

    leather_armor = Armor("Leather Armor", defense_modifier=round(9 * zone_level), armor_type=ArmorType.CHEST,
                          value=60 + round(zone_level ** 2) * 4, zone_level=zone_level)
    leather_boots = Armor("Leather Boots", defense_modifier=round(3 * zone_level), armor_type=ArmorType.BOOTS,
                          value=round(40 + (zone_level ** 2) * 2.5), zone_level=zone_level)
    leather_gloves = Armor("Leather Gloves", defense_modifier=round(6 * zone_level), armor_type=ArmorType.GLOVES,
                           value=round(40 + (zone_level ** 2) * 2.5), zone_level=zone_level)

    padded_armor = Armor("Padded Armor", defense_modifier=round(6 * zone_level), armor_type=ArmorType.CHEST,
                         value=40 + round(zone_level ** 2) * 4, zone_level=zone_level)
    padded_boots = Armor("Padded Boots", defense_modifier=round(2 * zone_level), armor_type=ArmorType.BOOTS,
                         value=20 + round(zone_level ** 2) * 2, zone_level=zone_level)
    padded_gloves = Armor("Padded Gloves", defense_modifier=round(4 * zone_level), armor_type=ArmorType.GLOVES,
                          value=20 + round(zone_level ** 2) * 2, zone_level=zone_level)

    # Swords
    short_sword = Weapon("Short Sword", "Sword", attack_modifier=3 * zone_level, special_attack=1,
                         value=30 + round(zone_level ** 2) * 1, zone_level=zone_level)
    long_sword = Weapon("Long Sword", "Sword", attack_modifier=5 * zone_level, special_attack=2,
                        value=50 + round(zone_level ** 2) * 2, zone_level=zone_level)
    champion_sword = Weapon("Champion Sword", "Sword", attack_modifier=7 * zone_level, special_attack=3,
                            value=70 + round(zone_level ** 2) * 3, zone_level=zone_level)
    voltaic_sword = Weapon("Voltaic Sword", "Sword", attack_modifier=12 * zone_level, special_attack=4,
                           value=90 + round(zone_level ** 2) * 4, zone_level=zone_level)

    # Spears
    short_spear = Weapon("Short Spear", "Spear", attack_modifier=3 * zone_level, special_attack=1,
                         value=round(35 + (zone_level ** 2) * 1.5), zone_level=zone_level)
    long_spear = Weapon("Long Spear", "Spear", attack_modifier=5 * zone_level, special_attack=2,
                        value=round(55 + (zone_level ** 2) * 2.5), zone_level=zone_level)
    champion_spear = Weapon("Champion Spear", "Spear", attack_modifier=7 * zone_level, special_attack=3,
                            value=round(75 + (zone_level ** 2) * 3.5), zone_level=zone_level)

    # Hammers
    club = Weapon("Club", "Hammer", attack_modifier=1 * zone_level, special_attack=1,
                  value=20 + round(zone_level ** 2) * 1, zone_level=zone_level)
    hammer = Weapon("Hammer", "Hammer", attack_modifier=4 * zone_level, special_attack=2,
                    value=40 + round(zone_level ** 2) * 2, zone_level=zone_level)
    war_hammer = Weapon("War Hammer", "Hammer", attack_modifier=7 * zone_level, special_attack=3,
                        value=60 + round(zone_level ** 2) * 3, zone_level=zone_level)

    # Bows
    short_bow = Weapon("Short Bow", "Bow", attack_modifier=3 * zone_level, special_attack=1,
                       value=40 + round(zone_level ** 2) * 1, zone_level=zone_level)
    long_bow = Weapon("Long Bow", "Bow", attack_modifier=5 * zone_level, special_attack=2,
                      value=60 + round(zone_level ** 2) * 2, zone_level=zone_level)
    champion_bow = Weapon("Champion Bow", "Bow", attack_modifier=7 * zone_level, special_attack=3,
                          value=80 + round(zone_level ** 2) * 3, zone_level=zone_level)

    # Charms
    woodcrafters_charm = Charm("Woodcleaver",
                               description=f"Increase woodcutting success rate by {int(round(get_server_setting(guild_id, 'woodcleaver_percent') * 100))}% while wearing",
                               value=25000)
    miners_charm = Charm("Stonebreaker",
                         description=f"Increase mining success rate by {int(round(get_server_setting(guild_id, 'stonebreaker_percent') * 100))}% while wearing",
                         value=25000)
    lootmasters_charm = Charm("Loothaven",
                              description=f"Gives a {int(round(get_server_setting(guild_id, 'loothaven_percent') * 100))}% chance to **double** your monster loot *and* drop rates of bonus loot while wearing",
                              value=25000)
    strength_charm = Charm("Mightstone",
                           description=f"Doubles your critical hit chance *and* damage multiplier (**{int(round((get_server_setting(guild_id, 'mightstone_multiplier') * get_server_setting(guild_id, 'critical_hit_chance')) * 100))}%** and **{int(get_server_setting(guild_id, 'critical_hit_multiplier') * 2)}x**) while wearing",
                           value=25000)
    defenders_charm = Charm("Ironhide",
                            description=f"Increases your chance to **evade all attacks** by {int(round(get_server_setting(guild_id, 'ironhide_percent') * 100))}% and **run chance** by **{int(get_server_setting(guild_id, 'ironhide_multiplier'))}x** while wearing",
                            value=25000)

    # Potions
    stamina_potion = Potion("Stamina Potion", effect_stat="stamina", effect_value=50, value=10,
                            description="Restores 50 stamina")
    health_potion = Potion("Health Potion", effect_stat="health", effect_value=50, value=10,
                           description="Restores 50 health")
    super_stamina_potion = Potion("Super Stamina Potion", effect_stat="stamina", effect_value=250, value=20,
                                  description="Restores 250 stamina")
    super_health_potion = Potion("Super Health Potion", effect_stat="health", effect_value=250, value=20,
                                 description="Restores 250 health")

    # Forge Crafting Station and Recipes
    forge = CraftingStation("Forge")
    forge.add_recipe(Recipe(charcoal, (pine, 1)))
    forge.add_recipe(Recipe(iron, (charcoal, 2), (iron_ore, 2)))
    forge.add_recipe(Recipe(carbon, (coal, 2)))
    forge.add_recipe(Recipe(steel, (charcoal, 3), (carbon, 2), (iron, 1)))
    forge.add_recipe(Recipe(cannonball, (onyx, 3), (carbon, 2), (steel, 2)))
    forge.add_recipe(Recipe(short_sword, (charcoal, 3), (iron, 3), (leather_straps, 2)))
    forge.add_recipe(Recipe(long_sword, (charcoal, 3), (steel, 3), (leather_straps, 4)))
    forge.add_recipe(Recipe(champion_sword, (charcoal, 5), (steel, 5), (leather_straps, 4)))
    forge.add_recipe(Recipe(voltaic_sword, (charcoal, 5), (thick_pole, 10), (steel, 10), (leather_straps, 5), (glowing_essence, 1)))
    forge.add_recipe(Recipe(short_spear, (charcoal, 2), (pole, 2), (iron, 3)))
    forge.add_recipe(Recipe(long_spear, (charcoal, 2), (pole, 2), (steel, 3)))
    forge.add_recipe(Recipe(champion_spear, (charcoal, 2), (thick_pole, 4), (steel, 3)))
    forge.add_recipe(Recipe(hammer, (charcoal, 2), (pole, 2), (iron, 2)))
    forge.add_recipe(Recipe(war_hammer, (charcoal, 3), (thick_pole, 2), (steel, 3), (leather_straps, 3)))
    forge.add_recipe(Recipe(brigandine_armor, (charcoal, 6), (steel, 5), (tough_leather_straps, 3), (onyx, 12)))
    forge.add_recipe(Recipe(brigandine_boots, (charcoal, 4), (steel, 3), (tough_leather_straps, 2), (onyx, 6)))
    forge.add_recipe(Recipe(brigandine_gloves, (charcoal, 2), (steel, 2), (tough_leather_straps, 1), (onyx, 3)))
    forge.add_recipe(Recipe(buckler, (pine_strip, 5), (leather_straps, 3), (iron, 2)))
    forge.add_recipe(Recipe(small_shield, (ash_strip, 3), (tough_leather_straps, 2), (steel, 2)))
    forge.add_recipe(Recipe(large_shield, (yew_strip, 4), (tough_leather_straps, 4), (iron, 3), (steel, 5)))


    # WOOD SHOP Crafting Station and Recipes
    woodshop = CraftingStation("Wood Shop")
    woodshop.add_recipe(Recipe(club, (pole, 2)))
    woodshop.add_recipe(Recipe(pole, (pine, 3)))
    woodshop.add_recipe(Recipe(thick_pole, (ash, 5)))
    woodshop.add_recipe(Recipe(pine_strip, (pine, 4)))
    woodshop.add_recipe(Recipe(yew_strip, (yew, 4)))
    woodshop.add_recipe(Recipe(ash_strip, (ash, 4)))
    woodshop.add_recipe(Recipe(poplar_strip, (poplar, 4)))

    # BREAD STAND Crafting Station and Recipes
    bread_stand = CraftingStation("Bread Stand")
    bread_stand.add_recipe(Recipe(flour, (wheat, 2)))
    bread_stand.add_recipe(Recipe(bread, (flour, 1)))

    # MEAT STAND Crafting Station and Recipes
    meat_stand = CraftingStation("Meat Stand")
    meat_stand.add_recipe(Recipe(venison, (deer_part, 4)))
    meat_stand.add_recipe(Recipe(sinew, (deer_part, 2)))
    meat_stand.add_recipe(Recipe(rabbit_meat, (rabbit_body, 2)))

    # TANNERY Crafting Station and Recipes
    tannery = CraftingStation("Tannery")
    tannery.add_recipe(Recipe(leather, (deer_skin, 1)))
    tannery.add_recipe(Recipe(tough_leather, (wolf_skin, 1)))
    tannery.add_recipe(Recipe(leather_straps, (leather, 3)))
    tannery.add_recipe(Recipe(tough_leather_straps, (tough_leather, 3)))
    tannery.add_recipe(Recipe(leather_armor, (leather, 2), (leather_straps, 4), (linen, 6), (linen_thread, 6)))
    tannery.add_recipe(Recipe(leather_boots, (leather, 1), (leather_straps, 1), (linen, 2), (linen_thread, 2)))
    tannery.add_recipe(Recipe(leather_gloves, (leather, 1), (leather_straps, 1), (linen, 2), (linen_thread, 2)))

    # CLOTHIERY Crafting Station and Recipes
    clothiery = CraftingStation("Clothiery")
    clothiery.add_recipe(Recipe(linen, (flax, 3)))
    clothiery.add_recipe(Recipe(linen_thread, (flax, 1)))
    clothiery.add_recipe(Recipe(padded_armor, (linen_thread, 3), (linen, 3)))
    clothiery.add_recipe(Recipe(padded_boots, (linen_thread, 2), (linen, 2)))
    clothiery.add_recipe(Recipe(padded_gloves, (linen_thread, 1), (linen, 1)))

    # ARCHERY STAND Crafting Station and Recipes
    archery_stand = CraftingStation("Archery Stand")
    archery_stand.add_recipe(Recipe(short_bow, (pine_strip, 2), (linen_thread, 3)))
    archery_stand.add_recipe(Recipe(long_bow, (yew_strip, 4), (sinew, 4)))
    archery_stand.add_recipe(Recipe(champion_bow, (ash_strip, 5), (sinew, 5)))

    # Tavern Trencher
    tavern = CraftingStation("Tavern")
    tavern.add_recipe(Recipe(trencher, (venison, 5), (rabbit_meat, 5), (flour, 5)))

    # Potion Shop
    potion_shop = CraftingStation("Potion Shop")
    potion_shop.add_recipe(Recipe(stamina_potion, (ranarr, 1), (sinew, 2)))
    potion_shop.add_recipe(Recipe(health_potion, (spirit_weed, 1), (venison, 1)))
    potion_shop.add_recipe(Recipe(super_stamina_potion, (snapdragon, 1), (sinew, 6), (onyx, 3)))
    potion_shop.add_recipe(Recipe(super_health_potion, (bloodweed, 1), (venison, 3), (onyx, 3)))
    potion_shop.add_recipe(Recipe(woodcrafters_charm, (materium, 5), (poplar_strip, 5), (steel, 5), (carbon, 3), (charcoal, 2)))
    potion_shop.add_recipe(Recipe(miners_charm, (materium, 5), (ash_strip, 5), (steel, 5), (coal, 4), (iron_ore, 3)))
    potion_shop.add_recipe(Recipe(lootmasters_charm, (goblin_crown, 1), (materium, 5), (onyx, 30), (carbon, 5), (charcoal, 5)))
    potion_shop.add_recipe(Recipe(strength_charm, (materium, 5), (thick_pole, 10), (steel, 10), (charcoal, 5), (carbon, 3)))
    potion_shop.add_recipe(Recipe(defenders_charm, (materium, 5), (onyx, 4), (tough_leather_straps, 3), (steel, 5), (charcoal, 4)))

    stations = {
        "forge": forge,
        "woodshop": woodshop,
        "bread_stand": bread_stand,
        "meat_stand": meat_stand,
        "tannery": tannery,
        "clothiery": clothiery,
        "archery_stand": archery_stand,
        "tavern": tavern,
        "potion_shop": potion_shop
    }

    if station_name:
        return stations.get(station_name)
    return stations