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
            "effect_stat": self.effect_stat,
            "effect_value": self.effect_value,
            "value": self.value,
            "description": self.description,
            "stack": self.stack,
        }

    @classmethod
    def from_dict(cls, data):
        potion = cls(
            name=data["name"],
            effect_stat=data["effect_stat"],
            effect_value=data["effect_value"],
            value=data.get("value", 0),
            description=data.get("description", "")
        )
        potion.stack = data.get("stack", 0)
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
        effect_value=50,
        value=10,
        description="Restores 50 health",
    ),
    Potion(
        name='Stamina Potion',
        effect_stat='stamina',
        effect_value=50,
        value=10,
        description="Restores 50 stamina",
    ),
    Potion(
        name='Super Health Potion',
        effect_stat='health',
        effect_value=250,
        value=20,
        description="Restores 250 health",
    ),
    Potion(
        name='Super Stamina Potion',
        effect_stat='stamina',
        effect_value=20,
        value=20,
        description="Restores 250 stamina",
    ),
]

POTION_NAME_TO_INSTANCE = {potion.name: potion for potion in POTION_LIST}
