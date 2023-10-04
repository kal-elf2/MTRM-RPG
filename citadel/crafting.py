from resources.item import Item
import discord
from discord import Embed
from images.urls import generate_urls
from emojis import get_emoji
from exemplars.exemplars import Exemplar
from resources.ore import Ore


class Weapon(Item):
    def __init__(self, name, wtype, description=None, value=None, stack=1):
        super().__init__(name, description, value)
        self.wtype = wtype
        self.stack = stack

    def to_dict(self):
        weapon_data = super().to_dict()
        weapon_data["wtype"] = self.wtype
        weapon_data["stack"] = self.stack
        return weapon_data

    @classmethod
    def from_dict(cls, data):
        return cls(name=data["name"], wtype=data["wtype"], description=data.get("description"), value=data.get("value"))


class Armor(Item):
    def __init__(self, name, description=None, value=None, stack=1):
        super().__init__(name, description, value)
        self.stack = stack

    def to_dict(self):
        armor_data = super().to_dict()
        armor_data["stack"] = self.stack
        return armor_data

    @classmethod
    def from_dict(cls, data):
        armor = super().from_dict(data)
        return armor


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


class CraftingStation:
    def __init__(self, name):
        self.name = name
        self.recipes = []

    def add_recipe(self, recipe):
        self.recipes.append(recipe)

    def craft(self, recipe_name, player, player_data, guild_id):
        from utils import save_player_data

        recipe = next((r for r in self.recipes if r.result.name == recipe_name), None)
        if not recipe:
            print(f"Recipe not found for {recipe_name}.")
            return None
        if not recipe.can_craft(player.inventory):
            print(f"Cannot craft {recipe_name} due to insufficient ingredients.")
            return None
        if recipe and recipe.can_craft(player.inventory):

            for ingredient, quantity in recipe.ingredients:
                player.inventory.remove_item(ingredient.name, quantity)

            if isinstance(recipe.result, Armor):
                armor_exists = next((a for a in player.inventory.armors if a.name == recipe.result.name), None)
                if armor_exists:
                    armor_exists.stack += 1
                else:
                    # The new Armor instance will be created with a stack of 1 by default
                    player.inventory.armors.append(recipe.result)

            elif isinstance(recipe.result, Weapon):
                weapon_exists = next((w for w in player.inventory.weapons if w.name == recipe.result.name), None)
                if weapon_exists:
                    weapon_exists.stack += 1
                else:
                    # The new Weapon instance will be created with a stack of 1 by default
                    player.inventory.weapons.append(recipe.result)
            else:
                player.inventory.add_item_to_inventory(recipe.result)

            save_player_data(guild_id, player_data)

            return recipe.result
        return None


class CraftButtonView(discord.ui.View):
    def __init__(self, player, player_data, station, selected_recipe, guild_id, disabled=True):
        super().__init__()
        self.player = player
        self.disabled = disabled
        self.player_data = player_data
        self.message = None
        self.add_item(CraftButton(disabled, station, selected_recipe, player, player_data, guild_id))

class CraftButton(discord.ui.Button):
    def __init__(self, disabled, station, selected_recipe, player, player_data, guild_id):
        super().__init__(label="Craft", style=discord.ButtonStyle.primary, disabled=disabled)
        self.station = station
        self.selected_recipe = selected_recipe
        self.player = player
        self.player_data = player_data
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction):
        # Use the CraftingStation's craft method
        crafted_item = self.station.craft(self.selected_recipe.result.name, self.player, self.player_data,
                                          self.guild_id)

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

        # Colors for each zone
        color_mapping = {
            1: 0x969696,
            2: 0x15ce00,
            3: 0x0096f1,
            4: 0x9900ff,
            5: 0xfebd0d
        }

        zone_emoji = get_emoji(zone_emoji_mapping.get(zone_level))
        embed_color = color_mapping.get(zone_level)

        if crafted_item:
            # Check player's inventory for required ingredients.
            ingredients_list = []
            can_craft_again = True
            for ingredient, required_quantity in self.selected_recipe.ingredients:
                available_quantity = self.player.inventory.get_item_quantity(ingredient.name)
                if available_quantity < required_quantity:
                    can_craft_again = False
                    ingredients_list.append(f"❌ {ingredient.name} {available_quantity}/{required_quantity}")
                else:
                    ingredients_list.append(f"✅ {ingredient.name} {available_quantity}/{required_quantity}")

            # If any ingredient is not available in the required quantity, disable the button
            self.disabled = not can_craft_again

            message_content = "\n".join(ingredients_list)
            crafted_item_url = generate_urls('Icons', self.selected_recipe.result.name.replace(" ", "%20"))
            embed = Embed(title=f"{self.selected_recipe.result.name} {zone_emoji}", description=message_content,
                          color=embed_color)
            embed.set_thumbnail(url=crafted_item_url)
            crafted_item_count = self.player.inventory.get_item_quantity(crafted_item.name)
            embed.set_footer(text=f"+1 {crafted_item.name}\n{crafted_item_count} in backpack")

            await interaction.response.edit_message(embed=embed,
                                                    view=self.view)  # Update the view to reflect button state
        else:
            await interaction.response.send_message(f"Failed to craft {self.selected_recipe.result.name}.",
                                                    ephemeral=True)


class CraftingSelect(discord.ui.Select):
    def __init__(self, crafting_station):
        self.crafting_station = crafting_station

        # Define select options based on the provided recipes
        options = [discord.SelectOption(label=recipe.result.name, value=recipe.result.name)
                   for recipe in self.crafting_station.recipes]

        # Initialize the Select element with the generated options
        super().__init__(placeholder="Choose an item to craft", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        from utils import load_player_data

        guild_id = interaction.guild.id
        author_id = str(interaction.user.id)
        player_data = load_player_data(guild_id)
        player = Exemplar(player_data[author_id]["exemplar"],
                          player_data[author_id]["stats"],
                          player_data[author_id]["inventory"])

        # Get zone level from player stats
        zone_level = player.stats.zone_level

        # Emojis for each zone
        zone_emoji_mapping = {
            1: 'common_emoji',
            2: 'uncommon_emoji',
            3: 'rare_emoji',
            4: 'epic_emoji',
            5: 'legendary_emoji'
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

        # Check player's inventory for required ingredients.
        ingredients_list = []
        can_craft = True
        for ingredient, required_quantity in selected_recipe.ingredients:
            available_quantity = player.inventory.get_item_quantity(ingredient.name)
            if available_quantity < required_quantity:
                can_craft = False
                ingredients_list.append(f"❌ {ingredient.name} {available_quantity}/{required_quantity}")
            else:
                ingredients_list.append(f"✅ {ingredient.name} {available_quantity}/{required_quantity}")

        # Construct the embed message.
        message_content = "\n".join(ingredients_list)
        crafted_item_url = generate_urls('Icons', selected_recipe.result.name.replace(" ", "%20"))
        embed = Embed(title=f"{selected_recipe.result.name} {zone_emoji}", description=message_content,
                      color=embed_color)
        embed.set_thumbnail(url=crafted_item_url)

        view = CraftButtonView(player, player_data, self.crafting_station, selected_recipe, guild_id, disabled=not can_craft)
        message = await interaction.response.send_message(embed=embed, ephemeral=True, view=view)
        view.message = message


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
bread = Item("Bread")
deer_part = Item("Deer Parts")
rabbit_body = Item("Rabbit Body")
venison = Item("Venison")
sinew = Item("Sinew")
rabbit_meat = Item("Rabbit Meat")
deer_skin = Item("Deer Skin")
wolf_skin = Item("Wolf Skin")
leather = Item("Leather")
tough_leather = Item("Tough Leather")
linen = Item("Linen")
linen_thread = Item("Linen Thread")
flax = Item("Flax")

# Weapons
short_sword = Weapon("Short Sword", "Sword")
long_sword = Weapon("Long Sword", "Sword")
champion_sword = Weapon("Champion Sword", "Sword")
voltaic_sword = Weapon("Voltaic Sword", "Sword")
short_spear = Weapon("Short Spear", "Spear")
long_spear = Weapon("Long Spear", "Spear")
champion_spear = Weapon("Champion Spear", "Spear")
hammer = Weapon("Hammer", "Hammer")
war_hammer = Weapon("War Hammer", "Hammer")
club = Weapon("Club", "Hammer")
short_bow = Weapon("Short Bow", "Bow")
long_bow = Weapon("Long Bow", "Bow")
champion_bow = Weapon("Champion Bow", "Bow")

# Armors
brigandine_armor = Armor("Brigandine Armor")
brigandine_boots = Armor("Brigandine Boots")
brigandine_gloves = Armor("Brigandine Gloves")
leather_armor = Armor("Leather Armor")
leather_boots = Armor("Leather Boots")
leather_gloves = Armor("Leather Gloves")
padded_armor = Armor("Padded Armor")
padded_boots = Armor("Padded Boots")
padded_gloves = Armor("Padded Gloves")

# Forge Crafting Station and Recipes
forge = CraftingStation("Forge")
forge.add_recipe(Recipe(charcoal, (pine, 1)))
forge.add_recipe(Recipe(iron, (charcoal, 2), (iron_ore, 2)))
forge.add_recipe(Recipe(carbon, (coal, 2)))
forge.add_recipe(Recipe(steel, (charcoal, 3), (carbon, 2), (iron, 1)))
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

# WOOD SHOP Crafting Station and Recipes
woodshop = CraftingStation("Wood Shop")
woodshop.add_recipe(Recipe(club, (pole, 2)))
woodshop.add_recipe(Recipe(pole, (pine, 3)))
woodshop.add_recipe(Recipe(thick_pole, (ash, 5)))
woodshop.add_recipe(Recipe(pine_strip, (pine, 4)))
woodshop.add_recipe(Recipe(yew_strip, (yew, 4)))
woodshop.add_recipe(Recipe(poplar_strip, (poplar, 4)))
woodshop.add_recipe(Recipe(ash_strip, (ash, 4)))

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
archery_stand.add_recipe(Recipe(short_bow, (pine, 2), (linen_thread, 3)))
archery_stand.add_recipe(Recipe(long_bow, (yew, 4), (sinew, 4)))
