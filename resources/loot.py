import random
from resources.herb import HERB_TYPES
from resources.potion import POTION_LIST
from resources.materium import Materium
from resources.item import Item
from emojis import get_emoji
from probabilities import mtrm_drop_percent, potion_drop_percent, herb_drop_percent, loothaven_percent, spork_chance

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
    },
    'Goblin Crown': {
        'description': 'A powerful relic obtained from the Goblin Mother. Used to create powerful Charms.',
        'value': 5000
    }
}

item_emoji_mapping = {
    'Onyx': 'onyx_emoji',
    'Deer Skin': 'deer_skin_emoji',
    'Deer Parts': 'deer_part_emoji',
    'Rabbit Body': 'rabbit_body_emoji',
    'Glowing Essence': 'glowing_essence_emoji',
    'Wolf Skin': 'wolf_skin_emoji',
    'Goblin Crown': 'goblin_crown_emoji'
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
    'Mother': 30
}

def generate_zone_loot(player, zone_level, monster_drop=None, name=None):
    loot_messages = []
    loot = []

    # Check if the player has the Loothaven charm equipped
    loothaven_effect = (player.inventory.equipped_charm and player.inventory.equipped_charm.name == "Loothaven") and random.random() < loothaven_percent

    # Doubling the drop rates if Loothaven charm is active
    herb_drop_chance = herb_drop_percent * (2 if loothaven_effect else 1)
    materium_drop_chance = mtrm_drop_percent * zone_level * (2 if loothaven_effect else 1)
    potion_drop_chance = potion_drop_percent * zone_level * (2 if loothaven_effect else 1)

    # Coppers drop
    monster_multiplier = monster_difficulty_multiplier.get(name, 1)  # Get the multiplier for the monster or default to 1
    coppers_dropped = random.randint(int(zone_level * 2 * monster_multiplier), int(zone_level * 5 * monster_multiplier))
    if loothaven_effect:
        coppers_dropped *= 2  # Double the coppers if Loothaven effect is active
    loot.append(('coppers', coppers_dropped))
    coppers_message = "Coppers" if coppers_dropped > 1 else "Copper"
    loot_messages.append(f"{get_emoji('coppers_emoji')} You found **{coppers_dropped} {coppers_message}**!")

    # Herb drops
    if random.random() < herb_drop_chance:
        # Base weights
        herb_weights = [40, 40, 10, 10]

        # Increase the weights of the last two herbs based on zone_level
        increase_per_zone = 5
        herb_weights[2] += (zone_level - 1) * increase_per_zone
        herb_weights[3] += (zone_level - 1) * increase_per_zone

        # Decrease the weights of the first two herbs to maintain total weight
        total_increase = (zone_level - 1) * 2 * increase_per_zone
        herb_weights[0] -= total_increase // 2
        herb_weights[1] -= total_increase // 2

        herb_dropped = random.choices(HERB_TYPES, weights=herb_weights, k=1)[0]
        herb_count = 2 if loothaven_effect else 1
        for _ in range(herb_count):
            loot.append(('herb', herb_dropped))
        loot_messages.append(f"{get_emoji(herb_dropped.name)} You found **{herb_count} {herb_dropped.name}**!")

    # Materium drops
    if random.random() < materium_drop_chance:
        materium_dropped = Materium()
        materium_count = 2 if loothaven_effect else 1
        for _ in range(materium_count):
            loot.append(('materium', materium_dropped))
        loot_messages.append(f"{get_emoji('Materium')} You found **{materium_count} Materium**!")

    # Potion drops
    if random.random() < potion_drop_chance:
        # Base weights
        potion_weights = [40, 40, 10, 10][:len(POTION_LIST)]

        # Adjust the weights based on zone level and Loothaven charm effect
        increase_per_zone_potion = (zone_level - 1) * 5 * (2 if loothaven_effect else 1)
        potion_weights[2] += increase_per_zone_potion
        potion_weights[3] += increase_per_zone_potion

        # Decrease the weights of the first two potions to maintain total weight
        total_increase_potion = increase_per_zone_potion * 2
        potion_weights[0] -= total_increase_potion // 2
        potion_weights[1] -= total_increase_potion // 2

        potion_dropped = random.choices(POTION_LIST, weights=potion_weights, k=1)[0]
        potion_count = 2 if loothaven_effect else 1
        for _ in range(potion_count):
            loot.append(('potion', potion_dropped))
        potion_name = potion_dropped.name + "s" if potion_count > 1 else potion_dropped.name
        loot_messages.append(f"{get_emoji(potion_dropped.name)} You found **{potion_count} {potion_name}**!")

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

            # Double the quantity if Loothaven charm's effect is active
            final_quantity = quantity * 2 if loothaven_effect else quantity

            loot.append(('items', [(item, final_quantity)]))

            # Custom pluralization rules
            if final_quantity > 1:
                if item.name == "Onyx":
                    item_name_plural = "Onyx"
                elif item.name == "Rabbit Body":
                    item_name_plural = "Rabbit Bodies"
                elif item.name == "Glowing Essence":
                    item_name_plural = "Glowing Essence"
                elif item.name == "Deer Parts":
                    item_name_plural = "Deer Parts"
                else:
                    item_name_plural = item.name + "s"
            else:
                item_name_plural = item.name

            loot_messages.append(
                f"{get_emoji(item_emoji_mapping.get(item.name, ''))} You found **{final_quantity} {item_name_plural}**!")

        # Rusty Spork drop logic
        if random.random() < spork_chance:
            spork_dropped = Item("Rusty Spork", description="A rusty and useless trinket", value=100000)
            spork_count = 2 if loothaven_effect else 1
            for _ in range(spork_count):
                loot.append(('items', [(spork_dropped, 1)]))  # Each drop is 1 item, even if doubled
            spork_message = "Rusty Sporks" if spork_count > 1 else "Rusty Spork"
            loot_messages.append(f"{get_emoji('Rusty Spork')} You found **{spork_count} {spork_message}**!")

        # Return the loot dropped (empty list if no loot is dropped) and the loot messages
        return loot, loot_messages, loothaven_effect






