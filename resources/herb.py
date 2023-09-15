

class Herb:
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
        herb = cls(
            name=data["name"],
            rarity=data["rarity"],
            value=data["value"],
        )
        herb.stack = data["stack"]
        return herb

HERB_TYPES = [
    Herb("Ranarr", 1, 25), # for Stamina Potion
    Herb("Spirit Weed", 2, 30), # for Health Potion
    Herb("Snapdragon", 3, 250), # for Super Stamina Potion
    Herb("Bloodweed", 4, 350), # for Super Health Potion
    Herb("Dwarf Weed", 5, 1000), # Unknown
]

