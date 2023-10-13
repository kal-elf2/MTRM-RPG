from resources.item import Item
from resources.herb import Herb
from resources.materium import Materium

class Potion(Item):
    def __init__(self, name, rarity, effect_stat, effect_value, required_level, resources, value=0, duration=60, description=""):
        super().__init__(name, description=description, value=value)
        self.rarity = rarity
        self.effect_stat = effect_stat
        self.effect_value = effect_value
        self.required_level = required_level
        self.resources = resources
        self.duration = duration
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
        potion = POTION_NAME_TO_INSTANCE[data["name"]].copy()
        potion.stack = data["stack"]
        return potion

    def copy(self):
        return Potion(
            name=self.name,
            rarity=self.rarity,
            effect_stat=self.effect_stat,
            effect_value=self.effect_value,
            required_level=self.required_level,
            resources=self.resources,
            value=self.value,
            duration=self.duration,
            description=self.description
        )

HERB_TYPES = [
    Herb("Ranarr", 1, 3),
    Herb("Spirit Weed", 2, 6),
    Herb("Bloodweed", 3, 12),
    Herb("Snapdragon", 4, 24),
    Herb("Dwarf Weed", 5, 48),
]

POTION_LIST = [
    Potion(
        name='Health Potion',
        rarity=1,
        effect_stat='health',
        effect_value=10,
        required_level=10,
        resources={HERB_TYPES[0]: 1, Materium: 2},
        value=10,
        description="A basic potion that restores 10 health points. Commonly found and easy to craft.",
    ),
    Potion(
        name='Strength Potion',
        rarity=2,
        effect_stat='strength',
        effect_value=5,
        required_level=20,
        resources={HERB_TYPES[1]: 1, Materium: 3},
        value=20,
        description="A potion that increases your strength by 5 points for a short duration. Requires rarer herbs and more materium to craft.",
    ),
    Potion(
        name='Endurance Potion',
        rarity=3,
        effect_stat='endurance',
        effect_value=10,
        required_level=30,
        resources={HERB_TYPES[2]: 1, Materium: 4},
        value=30,
        description="A powerful potion that boosts your endurance by 10 points for a limited time. Made from rare herbs and a higher amount of materium.",
    ),
    Potion(
        name='Attack Potion',
        rarity=4,
        effect_stat='attack',
        effect_value=15,
        required_level=40,
        resources={HERB_TYPES[3]: 1, Materium: 5},
        value=40,
        description="An advanced potion that increases your attack power by 15 points for a short period. Crafted using very rare herbs and a significant amount of materium.",
    ),
    Potion(
        name='Defense Potion',
        rarity=5,
        effect_stat='defense',
        effect_value=20,
        required_level=50,
        resources={HERB_TYPES[4]: 1, Materium: 6},
        value=50,
        description="An extremely potent potion that boosts your defense by 20 points for a limited time. Requires the rarest herbs and a large quantity of materium to craft.",
    ),
]

POTION_NAME_TO_INSTANCE = {potion.name: potion for potion in POTION_LIST}



