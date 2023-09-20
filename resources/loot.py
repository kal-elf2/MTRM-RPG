import random
from resources.ore import GEM_TYPES
from resources.herb import HERB_TYPES
from resources.potion import POTION_LIST
from resources.materium import Materium
from resources.item import Item


class Loot:
    def __init__(self, name, rarity, value):
        self.name = name
        self.rarity = rarity
        self.value = value
        self.stack = 0

    def to_dict(self):
        return {
            "name": self.name,
            "rarity": self.rarity,
            "value": self.value,
            "stack": self.stack,
        }

    @classmethod
    def from_dict(cls, data):
        loot = cls(
            name=data["name"],
            rarity=data["rarity"],
            value=data["value"],
        )
        loot.stack = data["stack"]
        return loot

loot_definitions = {
    'Rabbit Body': {
        'description': 'A furry rabbit body, warm to the touch. Can be used for crafting soft armors.',
        'value': 10
    },
    'Deer Parts': {
        'description': 'Various parts of a deer. Some are useful for making tools and weapons.',
        'value': 20
    },
    'Deer Skins': {
        'description': 'Tough deer skin. Can be used for crafting sturdy armors.',
        'value': 30
    },
    'Wolf Skin': {
        'description': 'A skin of a wild wolf. Known for its durability and strength.',
        'value': 50
    },
    'Onyx': {
        'description': 'A precious black gemstone. Used in crafting magical items and potent elixirs.',
        'value': 100
    },
    'Glowing Essence': {
        'description': 'An ethereal essence that glows faintly. Used in powerful magical rituals and crafting.',
        'value': 200
    }
}


loot_list = [
    [
        Loot("Copper Coin", 1, 2),
        Loot("Bronze Bracelet", 1, 5),
        Loot("Wooden Amulet", 1, 8),
        Loot("Small Gemstone", 1, 10),
        Loot("Rusty Longsword", 1, 20),
    ],
    [
        Loot("Silver Coin", 2, 10),
        Loot("Iron Ring", 2, 15),
        Loot("Glass Necklace", 2, 25),
        Loot("Polished Gemstone", 2, 30),
        Loot("Iron Longsword", 2, 40),
    ],
    [
        Loot("Gold Coin", 3, 20),
        Loot("Silver Bracelet", 3, 35),
        Loot("Golden Amulet", 3, 50),
        Loot("Cut Gemstone", 3, 60),
        Loot("Steel Longsword", 3, 75),
    ],
    [
        Loot("Platinum Coin", 4, 50),
        Loot("Golden Ring", 4, 60),
        Loot("Crystal Necklace", 4, 80),
        Loot("Flawless Gemstone", 4, 100),
        Loot("Mithril Longsword", 4, 125),
    ],
    [
        Loot("Adamant Coin", 5, 100),
        Loot("Platinum Bracelet", 5, 120),
        Loot("Enchanted Amulet", 5, 150),
        Loot("Pristine Gemstone", 5, 200),
        Loot("Adamant Longsword", 5, 200),
    ],
]

def generate_zone_loot(zone_level, monster_drop=None):
    loot_messages = []
    loot = []

    # Gold drops
    gold_dropped = random.randint(zone_level * 2, zone_level * 5)
    loot.append(('gold', gold_dropped))
    loot_messages.append(f"You found {gold_dropped} gold!")

    # Gem drops
    gem_drop_rate = 0.05  # 5% chance to drop a gem
    if random.random() < gem_drop_rate:
        gem_types_for_zone = GEM_TYPES[:zone_level]  # Adjust the gem types based on the zone level
        gem_weights = [50, 30, 15, 4, 1][:zone_level]  # Adjust the weights based on the zone level
        gem_dropped = random.choices(gem_types_for_zone, weights=gem_weights, k=1)[0]
        loot.append(('gem', gem_dropped))
        loot_messages.append(f"You found a {gem_dropped.name}!")

    # Herb drops
    herb_drop_rate = 0.10  # 10% chance to drop a herb
    if random.random() < herb_drop_rate:
        herb_types_for_zone = HERB_TYPES[:zone_level]  # Adjust the herb types based on the zone level
        herb_weights = [50, 30, 15, 4, 1][:zone_level]  # Adjust the weights based on the zone level
        herb_dropped = random.choices(herb_types_for_zone, weights=herb_weights, k=1)[0]
        loot.append(('herb', herb_dropped))
        loot_messages.append(f"You found some {herb_dropped.name}!")

    # Materium drops
    materium_drop_rate = 0.01  # 1% chance to drop Materium
    if random.random() < materium_drop_rate:
        materium_dropped = Materium()
        loot.append(('materium', materium_dropped))
        loot_messages.append("You found some Materium!")

        # Loot drops
    loot_drop_rate = 0.10  # 10% chance to drop loot
    if random.random() < loot_drop_rate:
        loot_options_for_zone = loot_list[zone_level - 1]
        loot_weights = [50, 30, 15, 4, 1]
        loot_weights = loot_weights[:len(
            loot_options_for_zone)]  # Adjust the weights based on the number of loot options for the zone
        loot_dropped = random.choices(loot_options_for_zone, weights=loot_weights, k=1)[0]
        loot.append(('loot', loot_dropped))
        loot_messages.append(f"You found a {loot_dropped.name}!")

    # Potion drops
    potion_drop_rate = 0.05 * zone_level  # Increase the chance of getting a potion as zone level increases
    if random.random() < potion_drop_rate:
        potion_weights = [50, 30, 15, 4, 1][
                         :len(POTION_LIST)]  # Adjust the weights based on the length of POTION_LIST
        potion_dropped = random.choices(POTION_LIST, weights=potion_weights, k=1)[0]
        loot.append(('potion', potion_dropped))
        loot_messages.append(f"You found a {potion_dropped.name}!")

    if monster_drop:
        for drop, quantity in monster_drop:  # Iterate over each drop item and its quantity
            if isinstance(drop, str):
                # If the 'drop' is a string, try to find it in the loot_definitions dictionary
                # If it's not found, instantiate an Item with default parameters
                item_data = loot_definitions.get(drop, {})
                item = Item(drop, description=item_data.get('description'), value=item_data.get('value', 10))
            elif isinstance(drop, Item):
                # Use the drop directly if it's already an instance of Item
                item = drop
            else:
                continue  # Ignore the drop if it's not a string or an Item

            loot.append(('items', [(item, quantity)]))
            loot_messages.append(f"You found {quantity} {item.name}!")

        # Return the loot dropped (empty list if no loot is dropped) and the loot messages
    return loot, loot_messages



