import random
from resources.herb import HERB_TYPES
from resources.potion import POTION_LIST
from resources.materium import Materium
from resources.item import Item
from emojis import get_emoji
from probabilities import mtrm_drop_percent, potion_drop_percent, herb_drop_percent

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
        'description': 'A furry rabbit body, warm to the touch. Can be used for citadel soft armors.',
        'value': 10
    },
    'Deer Parts': {
        'description': 'Various parts of a deer. Some are useful for making tools and weapons.',
        'value': 20
    },
    'Deer Skin': {
        'description': 'Tough deer skin. Can be used for citadel sturdy armors.',
        'value': 30
    },
    'Wolf Skin': {
        'description': 'A skin of a wild wolf. Known for its durability and strength.',
        'value': 50
    },
    'Onyx': {
        'description': 'A precious black gemstone. Used in citadel magical items and potent elixirs.',
        'value': 100
    },
    'Glowing Essence': {
        'description': 'An ethereal essence that glows faintly. Used in powerful magical rituals and citadel.',
        'value': 200
    }
}

item_emoji_mapping = {
    'Onyx': 'onyx_emoji',
    'Deer Skin': 'deer_skin_emoji',
    'Deer Parts': 'deer_parts_emoji',
    'Rabbit Body': 'rabbit_body_emoji',
    'Glowing Essence': 'glowing_essence_emoji',
    'Wolf Skin': 'wolf_skin_emoji'
}

monster_difficulty_multiplier = {
    'Rabbit': 0.5,
    'Deer': 1,
    'Buck': 1.5,
    'Wolf': 2,
    'Goblin': 5,
    'Goblin Hunter': 10,
    'Mega Brute': 20,
    'Wisp': 20,
}

def generate_zone_loot(zone_level, monster_drop=None, name=None):
    loot_messages = []
    loot = []

    monster_multiplier = monster_difficulty_multiplier.get(name, 1)  # Get the multiplier for the monster or default to 1
    coppers_dropped = random.randint(int(zone_level * 2 * monster_multiplier), int(zone_level * 5 * monster_multiplier))
    loot.append(('coppers', coppers_dropped))

    if coppers_dropped == 1:
        loot_messages.append(f"{get_emoji('coppers_emoji')} You found {coppers_dropped} Copper!")
    else:
        loot_messages.append(f"{get_emoji('coppers_emoji')} You found {coppers_dropped} Coppers!")

    # Herb drops
    if random.random() < herb_drop_percent:
        herb_types_for_zone = HERB_TYPES
        herb_weights = [40, 40, 5, 5]
        herb_dropped = random.choices(herb_types_for_zone, weights=herb_weights, k=1)[0]
        loot.append(('herb', herb_dropped))
        loot_messages.append(f"🌿 You found some {herb_dropped.name}!")

    # Materium drops
    materium_drop_rate = mtrm_drop_percent * zone_level  # Increase the chance of getting a drop as zone level increases
    if random.random() < materium_drop_rate:
        materium_dropped = Materium()
        loot.append(('materium', materium_dropped))
        loot_messages.append(f"{get_emoji('mtrm_emoji')} You found some Materium!")

    # Potion drops
    potion_drop_rate = potion_drop_percent * zone_level  # Increase the chance of getting a drop as zone level increases
    if random.random() < potion_drop_rate:
        potion_weights = [50, 30, 15, 4, 1][
                         :len(POTION_LIST)]  # Adjust the weights based on the length of POTION_LIST
        potion_dropped = random.choices(POTION_LIST, weights=potion_weights, k=1)[0]
        loot.append(('potion', potion_dropped))
        loot_messages.append(f"⚗️ You found a {potion_dropped.name}!")

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
            loot_messages.append(f"{get_emoji(item_emoji_mapping.get(item.name, ''))}  You found {quantity} {item.name}!")

        # Return the loot dropped (empty list if no loot is dropped) and the loot messages
    return loot, loot_messages



