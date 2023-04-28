class Ore:
    def __init__(self, name, rarity, base_mining_time, value):
        self.name = name
        self.rarity = rarity
        self.base_mining_time = base_mining_time
        self.value = value

ORE_TYPES = [
    Ore("Copper", 1, 15, 5),
    Ore("Iron", 2, 20, 10),
    Ore("Silver", 3, 30, 15),
    Ore("Gold", 4, 45, 20),
    Ore("Platinum", 5, 60, 25),
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

