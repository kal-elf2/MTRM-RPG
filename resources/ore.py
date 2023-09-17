class Ore:
    def __init__(self, name, min_level):
        self.name = name
        self.min_level = min_level
        self.stack = 0

    def to_dict(self):
        return {
            "name": self.name,
            "min_level": self.min_level,
            "stack": self.stack,
        }

    @classmethod
    def from_dict(cls, data):
        ore = cls(
            name=data["name"],
            min_level=data["min_level"],
        )
        ore.stack = data["stack"]
        return ore

ORE_TYPES = [
    Ore("Iron", 1),
    Ore("Coal", 20),
    Ore("Carbon", 40),
    Ore("Mithril", 60)
]

class Gem:
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
        gem = cls(
            name=data["name"],
            rarity=data["rarity"],
            value=data["value"],
        )
        gem.stack = data["stack"]
        return gem

GEM_TYPES = [
    Gem("Sapphire", 1, 50),
    Gem("Emerald", 2, 125),
    Gem("Ruby", 3, 250),
    Gem("Diamond", 4, 600),
    Gem("Black Opal", 5, 1200),
]

