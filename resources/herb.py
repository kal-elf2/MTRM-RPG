

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
    Herb("Ranarr", 1, 3),
    Herb("Spirit Weed", 2, 6),
    Herb("Bloodweed", 3, 12),
    Herb("Snapdragon", 4, 24),
    Herb("Dwarf Weed", 5, 48),
]

