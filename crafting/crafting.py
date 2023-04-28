from resources.gathering import Gathering
from crafting.armor import Armor, ARMOR_RECIPES
from crafting.weapon import Weapon, WEAPON_RECIPES
from resources.potion import Potion, POTION_LIST


class Crafting(Gathering):
    def __init__(self, endurance_cost=10):
        super().__init__(endurance_cost)

    def craft_item(self, player, recipe):
        if self.perform_action(player):
            resources_needed = self.get_resources_needed(recipe)
            if self.check_resources_available(player, resources_needed):
                self.remove_resources_from_inventory(player, resources_needed)
                crafted_item = self.create_item(recipe['item_class'], recipe)
                player.inventory.add_item(crafted_item)
                return True, f"Successfully crafted {crafted_item.name}"
            else:
                return False, "Insufficient resources to craft this item"

    def get_resources_needed(self, recipe):
        return recipe['resources']

    def check_resources_available(self, player, resources_needed):
        for resource, amount_needed in resources_needed.items():
            if player.inventory.get_item_count(resource) < amount_needed:
                return False
        return True

    def remove_resources_from_inventory(self, player, resources_needed):
        for resource, amount_needed in resources_needed.items():
            player.inventory.remove_item(resource, amount_needed)

    def create_item(self, item_class, recipe):
        if item_class == Armor:
            item = item_class(recipe['name'], recipe['tier'], recipe['required_level'], recipe['resources'],
                              recipe['value'], recipe['armor_type'], description="", weight=0)
        elif item_class == Weapon:
            item = item_class(recipe['name'], recipe['tier'], recipe['required_level'], recipe['resources'],
                              recipe['value'], recipe['weapon_type'], description="", weight=0)
        elif item_class == Potion:
            item = item_class(recipe['name'], recipe['tier'], recipe['effect_stat'], recipe['effect_value'],
                              recipe['required_level'], recipe['resources'], recipe['value'])
        else:
            item = None
        return item

    def get_recipe(self, item_type, recipe_name):
        if item_type == "armor":
            recipes = ARMOR_RECIPES
        elif item_type == "weapon":
            recipes = WEAPON_RECIPES
        elif item_type == "potion":
            recipes = POTION_LIST
        else:
            return None

        for recipe in recipes:
            if recipe.name == recipe_name:
                return recipe
        return None

class Item:
    def __init__(self, name, item_type, tier):
        self.name = name
        self.type = item_type
        self.tier = tier
        self.stats = {}
        self.imbue = None

    def set_stats(self, stats):
        self.stats = stats

    def set_imbue(self, imbue):
        self.imbue = imbue
