from resources.item import Item
import discord

class Weapon(Item):
    def __init__(self, name, wtype, description=None, value=None):
        super().__init__(name, description, value)
        self.wtype = wtype   # New attribute for weapon type

    def to_dict(self):
        weapon_data = super().to_dict()
        weapon_data["wtype"] = self.wtype
        return weapon_data

    @classmethod
    def from_dict(cls, data):
        weapon = super().from_dict(data)
        weapon.wtype = data["wtype"]
        return weapon

class Armor(Item):
    def __init__(self, name, description=None, value=None):
        super().__init__(name, description, value)

# Recipe Classes
class Recipe:
    def __init__(self, result, *ingredients):
        self.result = result
        self.ingredients = ingredients  # List of tuples (item, quantity)

    def can_craft(self, inventory):
        for ingredient, quantity in self.ingredients:
            if inventory.get(ingredient, 0) < quantity:
                return False
        return True

class CraftingStation:
    def __init__(self, name):
        self.name = name
        self.recipes = []

    def add_recipe(self, recipe):
        self.recipes.append(recipe)

    def craft(self, recipe_name, inventory):
        recipe = next((r for r in self.recipes if r.result.name == recipe_name), None)
        if recipe and recipe.can_craft(inventory):
            for ingredient, quantity in recipe.ingredients:
                inventory[ingredient] -= quantity
            inventory[recipe.result.name] = inventory.get(recipe.result.name, 0) + 1
            return recipe.result
        return None


class CraftingSelect(discord.ui.Select):
    def __init__(self, recipes):
        # Define select options based on the provided recipes
        options = [discord.SelectOption(label=recipe.result.name, value=recipe.result.name) for recipe in recipes]

        # Initialize the Select element with the generated options
        super().__init__(placeholder="Choose an item to craft", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        # Retrieve the recipe for the selected item.
        selected_recipe = next((r for r in forge.recipes if r.result.name == self.values[0]), None)
        if selected_recipe:
            # Construct the recipe message.
            ingredients_str = ", ".join(
                [f"{quantity}x {ingredient.name}" for ingredient, quantity in selected_recipe.ingredients])
            message_content = f"Recipe for {selected_recipe.result.name}: {ingredients_str}"

            await interaction.response.send_message(message_content, ephemeral=True)
        else:
            await interaction.response.send_message(f"Recipe for {self.values[0]} not found.", ephemeral=True)


# Defining All Items
charcoal = Item("Charcoal")
iron = Item("Iron")
carbon = Item("Carbon")
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
deer_part = Item("Deer Part")
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
