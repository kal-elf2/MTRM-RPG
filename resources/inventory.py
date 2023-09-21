from resources.materium import Materium
from resources.herb import Herb
from resources.potion import Potion
from resources.item import Item
from crafting.weapon import Weapon
from crafting.armor import Armor
from resources.ore import Gem, Ore
from resources.loot import Loot
from resources.tree import Tree

class Inventory:
    def __init__(self, limit=40):
        self.items = []
        self.trees = []
        self.herbs = []
        self.ore = []
        self.gems = []
        self.potions = []
        self.loot = []
        self.equipped_items = []
        self.limit = limit
        self.equipped_armor = {}
        self.equipped_weapon = None
        self.materium_count = 0
        self.gold = 0

    def to_dict(self):
        return {
            "gold": self.gold,
            "items": [item.to_dict() for item in self.items],
            "trees": [tree.to_dict() for tree in self.trees],
            "herbs": [herb.to_dict() for herb in self.herbs],
            "ore": [ore.to_dict() for ore in self.ore],
            "gems": [gem.to_dict() for gem in self.gems],
            "potions": [potion.to_dict() for potion in self.potions],
            "loot": [item.to_dict() for item in self.loot],
            "limit": self.limit,
            "equipped_items": [item.to_dict() for item in self.equipped_items],
            "equipped_armor": {k: v.to_dict() for k, v in self.equipped_armor.items()},
            "equipped_weapon": self.equipped_weapon.to_dict() if self.equipped_weapon else None,
            "materium_count": self.materium_count,
        }

    @classmethod
    def from_dict(cls, data):
        inventory = cls(limit=data["limit"] if "limit" in data else 40)
        inventory.gold = data["gold"]
        inventory.items = [Item.from_dict(item_data) for item_data in data["items"]]
        inventory.trees = [Tree.from_dict(tree_data) for tree_data in data["trees"]]
        inventory.herbs = [Herb.from_dict(herb_data) for herb_data in data["herbs"]]
        inventory.ore = [Ore.from_dict(ore_data) for ore_data in data["ore"]]
        inventory.potions = [Potion.from_dict(potion_data) for potion_data in data["potions"]]
        inventory.gems = [Gem.from_dict(gem_data) for gem_data in data["gems"]]
        inventory.loot = [Item.from_dict(item_data) for item_data in data["loot"]]
        inventory.equipped_items = [Item.from_dict(item_data) for item_data in data["equipped_items"]]
        inventory.equipped_armor = {k: Armor.from_dict(v_data) for k, v_data in data["equipped_armor"].items()}
        inventory.equipped_weapon = Weapon.from_dict(data["equipped_weapon"]) if data["equipped_weapon"] else None
        inventory.materium_count = data["materium_count"]
        return inventory

    def add_gold(self, amount):
        self.gold += amount

    def add_item_to_inventory(self, item, amount=1):
        if isinstance(item, Materium):
            self.materium_count += amount
        elif isinstance(item, Tree):
            self._add_item_to_specific_inventory(item, amount, self.trees)
        elif isinstance(item, Herb):
            self._add_item_to_specific_inventory(item, amount, self.herbs)
        elif isinstance(item, Ore):
            self._add_item_to_specific_inventory(item, amount, self.ore)
        elif isinstance(item, Potion):
            self._add_item_to_specific_inventory(item, amount, self.potions)
        elif isinstance(item, Gem):
            self._add_item_to_specific_inventory(item, amount, self.gems)
        elif isinstance(item, Loot):
            self._add_item_to_specific_inventory(item, amount, self.loot)
        elif isinstance(item, Item):
            self._add_item_to_specific_inventory(item, amount, self.items)

    def get_tree_count(self, tree_type):
        #Returns the count of a specific type of tree in the inventory.
        for tree in self.trees:
            if tree.name == tree_type:
                return tree.stack
        return 0  # Return 0 if the tree_type is not found in inventory

    def get_ore_count(self, ore_type):
        #Returns the count of a specific type of ore in the inventory.
        for ore in self.ore:
            if ore.name == ore_type:
                return ore.stack
        return 0  # Return 0 if the ore_type is not found in inventory

    def get_fish_count(self, fish_type):
        #Returns the count of a specific type of tree in the inventory.
        for fish in self.fish:
            if fish.name == fish_type:
                return fish.stack
        return 0  # Return 0 if the tree_type is not found in inventory

    def _add_item_to_specific_inventory(self, item, amount, item_list):
        existing_item = next((i for i in item_list if i.name == item.name), None)
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


    def has(self, item, amount):
        if isinstance(item, Materium):
            return self.materium_count >= amount
        else:
            return self.items.count(item) >= amount

    def remove_item(self, item, amount=1):
        if isinstance(item, Materium):
            return self._remove_materium_from_inventory(amount)

        if isinstance(item, Herb):
            return self._remove_herb_from_inventory(item, amount)

        return self._remove_generic_item_from_inventory(item, amount)

    def _remove_materium_from_inventory(self, amount):
        if self.materium_count >= amount:
            self.materium_count -= amount
            return True
        else:
            print("Item not found in inventory.")
            return False

    def _remove_herb_from_inventory(self, herb, amount):
        existing_herb = next((i for i in self.items if isinstance(i, Herb) and i.name == herb.name), None)
        if existing_herb and existing_herb.stack >= amount:
            existing_herb.stack -= amount
            if existing_herb.stack == 0:
                self.items.remove(existing_herb)
            return True
        else:
            print(f"You don't have {amount} {herb.name}(s) in your inventory.")
            return False

    def _remove_generic_item_from_inventory(self, item, amount):
        item_count = self.items.count(item)
        if item_count >= amount:
            for _ in range(amount):
                self.items.remove(item)
            return True
        else:
            print(f"You don't have {amount} {item.name}(s) in your inventory.")
            return False

    def equip_item(self, item):
        if isinstance(item, Armor) or isinstance(item, Weapon):
            if self._can_equip_item(item):
                self.equipped_items.append(item)
                self.remove_item(item)
                return True
            else:
                print(f"Cannot equip {item.name}.")
                return False
        else:
            print("You can only equip Armor or Weapon items.")
            return False

    def _can_equip_item(self, item):
        if isinstance(item, Armor):
            return not any(equipped_item.armor_type == item.armor_type for equipped_item in self.equipped_items)
        elif isinstance(item, Weapon):
            if item.weapon_type == "dual_daggers":
                return sum(1 for equipped_item in self.equipped_items if
                           isinstance(equipped_item, Weapon) and equipped_item.weapon_type == "dual_daggers") < 2
            elif item.weapon_type == "longbow":
                return not any(
                    isinstance(equipped_item, Armor) and equipped_item.armor_type == "shield" for equipped_item in
                    self.equipped_items) and not any(
                    isinstance(equipped_item, Weapon) for equipped_item in self.equipped_items)
            else:
                return not any(isinstance(equipped_item, Weapon) for equipped_item in self.equipped_items)
        return False

    def unequip_item(self, item):
        if item in self.equipped_items:
            self.equipped_items.remove(item)
            self.add_item_to_inventory(item)
            return True
        else:
            print("Item not found in equipped items.")
            return False


class Bank:
    def __init__(self):
        self.items = []

    def deposit_item(self, item):
        self.items.append(item)

    def withdraw_item(self, item):
        if item in self.items:
            self.items.remove(item)
            return item
        else:
            print("Item not found in the bank.")
            return None

