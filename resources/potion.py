from resources.item import Item
from resources.herb import Herb

class Potion(Item):
    def __init__(self, name, effect_stat, effect_value, value=0, description=""):
        super().__init__(name, description=description, value=value)
        self.effect_stat = effect_stat
        self.effect_value = effect_value
        self.stack = 0

    def to_dict(self):
        return {
            "name": self.name,
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
            effect_stat=self.effect_stat,
            effect_value=self.effect_value,
            value=self.value,
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
        effect_stat='health',
        effect_value=10,
        value=10,
        description="A basic potion that restores 10 health points.",
    ),
    Potion(
        name='Stamina Potion',
        effect_stat='stamina',
        effect_value=10,
        value=10,
        description="A potion that restores 10 stamina points.",
    ),
    Potion(
        name='Super Health Potion',
        effect_stat='health',
        effect_value=20,
        value=20,
        description="A potent potion that restores 20 health points.",
    ),
    Potion(
        name='Super Stamina Potion',
        effect_stat='stamina',
        effect_value=20,
        value=20,
        description="A potent potion that restores 20 stamina points.",
    ),
]

POTION_NAME_TO_INSTANCE = {potion.name: potion for potion in POTION_LIST}
