from resources.materium import Materium
from resources.herb import Herb
from resources.potion import Potion
from resources.item import Item
from resources.ore import Ore
from resources.tree import Tree

class Inventory:

    def __init__(self, limit=49):
        from citadel.crafting import ArmorType
        self.coppers = 0
        self.items = []
        self.trees = []
        self.herbs = []
        self.ore = []
        self.potions = []
        self.limit = limit
        self.armors = []
        self.equipped_armor = {
            ArmorType.CHEST: None,
            ArmorType.BOOTS: None,
            ArmorType.GLOVES: None
        }
        self.weapons = []
        self.equipped_weapon = None
        self.shields = []
        self.equipped_shield = None
        self.charms = []
        self.equipped_charm = None
        self.materium = 0

    def to_dict(self):
        return {
            "coppers": self.coppers,
            "items": [item.to_dict() for item in self.items],
            "trees": [tree.to_dict() for tree in self.trees],
            "herbs": [herb.to_dict() for herb in self.herbs],
            "ore": [ore.to_dict() for ore in self.ore],
            "potions": [potion.to_dict() for potion in self.potions],
            "limit": self.limit,
            "armors": [armor.to_dict() for armor in self.armors],
            "equipped_armor": {k: v.to_dict() if hasattr(v, 'to_dict') else None for k, v in self.equipped_armor.items()},
            "weapons": [weapon.to_dict() for weapon in self.weapons],
            "equipped_weapon": self.equipped_weapon.to_dict() if self.equipped_weapon else None,
            "shields": [shield.to_dict() for shield in self.shields],
            "equipped_shield": self.equipped_shield.to_dict() if self.equipped_shield else None,
            "charms": [charm.to_dict() for charm in self.charms],
            "equipped_charm": self.equipped_charm.to_dict() if self.equipped_charm else None,
            "materium": self.materium,
        }

    @classmethod
    def from_dict(cls, data):
        from citadel.crafting import Weapon, Armor, Shield, Charm
        inventory = cls(limit=data["limit"] if "limit" in data else 40)
        inventory.coppers = data["coppers"]
        inventory.items = [Item.from_dict(item_data) for item_data in data["items"]]
        inventory.trees = [Tree.from_dict(tree_data) for tree_data in data["trees"]]
        inventory.herbs = [Herb.from_dict(herb_data) for herb_data in data["herbs"]]
        inventory.ore = [Ore.from_dict(ore_data) for ore_data in data["ore"]]
        inventory.potions = [Potion.from_dict(potion_data) for potion_data in data["potions"]]
        inventory.weapons = [Weapon.from_dict(weapon_data) for weapon_data in data["weapons"]]
        inventory.armors = [Armor.from_dict(armor_data) for armor_data in data["armors"]]
        inventory.equipped_armor = {k: Armor.from_dict(v_data) if v_data else None for k, v_data in data["equipped_armor"].items()}
        inventory.equipped_weapon = Weapon.from_dict(data["equipped_weapon"]) if data["equipped_weapon"] else None
        inventory.shields = [Shield.from_dict(shield_data) for shield_data in data["shields"]]
        inventory.equipped_shield = Shield.from_dict(data["equipped_shield"]) if data["equipped_shield"] else None
        inventory.charms = [Charm.from_dict(charm_data) for charm_data in data.get("charms", [])]
        inventory.equipped_charm = Charm.from_dict(data["equipped_charm"]) if data.get("equipped_charm") else None
        inventory.materium = data["materium"]
        return inventory

    def add_coppers(self, amount):
        self.coppers += amount

    def add_item_to_inventory(self, item, amount=1):
        from citadel.crafting import Weapon, Armor, Shield, Charm
        if isinstance(item, Materium):
            self.materium += amount
        elif isinstance(item, Tree):
            self._add_item_to_specific_inventory(item, amount, self.trees)
        elif isinstance(item, Herb):
            self._add_item_to_specific_inventory(item, amount, self.herbs)
        elif isinstance(item, Ore):
            self._add_item_to_specific_inventory(item, amount, self.ore)
        elif isinstance(item, Potion):
            self._add_item_to_specific_inventory(item, amount, self.potions)
        elif isinstance(item, Weapon):
            self._add_item_to_specific_inventory(item, amount, self.weapons)
        elif isinstance(item, Armor):
            self._add_item_to_specific_inventory(item, amount, self.armors)
        elif isinstance(item, Shield):
            self._add_item_to_specific_inventory(item, amount, self.shields)
        elif isinstance(item, Charm):
            self._add_item_to_specific_inventory(item, amount, self.charms)
        elif isinstance(item, Item):
            self._add_item_to_specific_inventory(item, amount, self.items)

    def has_item(self, item_name, zone_level=None):
        stackable_sections = [self.items, self.trees, self.herbs, self.ore, self.weapons,
                              self.armors, self.shields]
        for section in stackable_sections:
            for item in section:
                if item.name == item_name and (not zone_level or getattr(item, 'zone_level', None) == zone_level):
                    return True
        return False

    def total_items_count(self):
        total = (
                len(self.items) +
                len(self.trees) +
                len(self.herbs) +
                len(self.ore) +
                len(self.armors) +
                len(self.weapons) +
                len(self.shields)
        )
        return total

    def get_item_quantity(self, item_name, zone_level=None):
        # Check for materium specifically
        if item_name == "Materium":
            return self.materium

        stackable_sections = [self.items, self.trees, self.herbs, self.ore, self.potions, self.weapons,
                              self.armors, self.shields, self.charms]

        for section in stackable_sections:
            for item in section:
                if item.name == item_name and (not zone_level or getattr(item, 'zone_level', None) == zone_level):
                    return item.stack

        return 0

    def _add_item_to_specific_inventory(self, item, amount, item_list):
        # Check for the existence of a zone_level attribute. If not present, default to None.
        item_zone_level = getattr(item, 'zone_level', None)

        # Use both the name and the zone_level (if it exists) for the item check
        existing_item = next(
            (i for i in item_list if i.name == item.name and getattr(i, 'zone_level', None) == item_zone_level), None)

        if existing_item:
            existing_item.stack += amount
        else:
            if len(item_list) < self.limit:
                item.stack = amount
                item_list.append(item)
            else:
                print("Your inventory is full. Deposit items at the bank to free up space.")
                return False
        return True

    def remove_item(self, item_name, amount=1):

        # If the item to remove is a Materium
        if item_name == "Materium":
            if self.materium >= amount:
                self.materium -= amount
                return True
        # Helper function to remove or decrease the quantity of an item from a specific inventory list
        def _remove_from_list(item_list, item_name, amount):
            for idx, item in enumerate(item_list):
                if item.name == item_name:
                    if item.stack > amount:
                        item.stack -= amount
                        return True
                    else:
                        del item_list[idx]
                        return True
            return False

        if _remove_from_list(self.items, item_name, amount):
            return True
        elif _remove_from_list(self.trees, item_name, amount):
            return True
        elif _remove_from_list(self.herbs, item_name, amount):
            return True
        elif _remove_from_list(self.ore, item_name, amount):
            return True
        elif _remove_from_list(self.potions, item_name, amount):
            return True
        else:
            for idx, weapon in enumerate(self.weapons):
                if weapon.name == item_name:
                    del self.weapons[idx]
                    return True

            for idx, armor in enumerate(self.armors):
                if armor.name == item_name:
                    del self.armors[idx]
                    return True

            for idx, shield in enumerate(self.shields):
                if shield.name == item_name:
                    del self.shields[idx]
                    return True

            for idx, charm in enumerate(self.charms):
                if charm.name == item_name:
                    del self.charms[idx]
                    return True

        return False

    def sell_item(self, item_name, amount, zone_level=None):
        """Adjusts the stack of an item or removes it if the stack reaches zero, considering zone_level."""
        # First, check if the item to sell is Rusty Spork
        if item_name == "Rusty Spork":
            for item in self.items:
                if item.name == item_name:
                    item.stack -= amount
                    if item.stack <= 0:
                        self.items.remove(item)
                    return True
            return False

        # For other item types, continue with the existing logic
        for item_list in [self.weapons, self.armors, self.shields, self.charms, self.potions]:
            for item in item_list:
                # Check both name and zone_level (if provided)
                if item.name == item_name and (zone_level is None or getattr(item, 'zone_level', None) == zone_level):
                    item.stack -= amount
                    if item.stack <= 0:
                        item_list.remove(item)
                    return True
        return False