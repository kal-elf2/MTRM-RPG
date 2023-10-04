class Ore:
    def __init__(self, name):
        self.name = name
        self.stack = 0

    def to_dict(self):
        return {
            "name": self.name,
            "stack": self.stack,
        }

    @classmethod
    def from_dict(cls, data):
        ore = cls(
            name=data["name"],
        )
        ore.stack = data["stack"]
        return ore

ORE_TYPES = [
    Ore("Iron Ore"),
    Ore("Coal"),
    Ore("Carbon")
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

