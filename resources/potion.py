from resources.item import Item
from resources.herb import Herb

class Potion(Item):
    def __init__(self, name, rarity, effect_stat, effect_value, value=0, duration=60, description=""):
        super().__init__(name, description=description, value=value)
        self.rarity = rarity
        self.effect_stat = effect_stat
        self.effect_value = effect_value
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
            value=self.value,
            duration=self.duration,
            description=self.description
        )

HERB_TYPES = [
    Herb("Ranarr", 25),
    Herb("Spirit Weed", 25),
    Herb("Bloodweed", 350),
    Herb("Snapdragon", 350)
]

POTION_LIST = [
    Potion(
        name='Health Potion',
        rarity=1,
        effect_stat='health',
        effect_value=10,
        value=10,
        description="A basic potion that restores 10 health points. Commonly found and easy to craft.",
    ),
    Potion(
        name='Strength Potion',
        rarity=2,
        effect_stat='strength',
        effect_value=5,
        value=20,
        description="A potion that increases your strength by 5 points for a short duration. Requires rarer herbs and more materium to craft.",
    ),
    Potion(
        name='Stamina Potion',
        rarity=3,
        effect_stat='stamina',
        effect_value=10,
        value=30,
        description="A powerful potion that boosts your stamina by 10 points for a limited time. Made from rare herbs and a higher amount of materium.",
    ),
    Potion(
        name='Attack Potion',
        rarity=4,
        effect_stat='attack',
        effect_value=15,
        value=40,
        description="An advanced potion that increases your attack power by 15 points for a short period. Crafted using very rare herbs and a significant amount of materium.",
    ),
    Potion(
        name='Defense Potion',
        rarity=5,
        effect_stat='defense',
        effect_value=20,
        value=50,
        description="An extremely potent potion that boosts your defense by 20 points for a limited time. Requires the rarest herbs and a large quantity of materium to craft.",
    ),
]

POTION_NAME_TO_INSTANCE = {potion.name: potion for potion in POTION_LIST}



