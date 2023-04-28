class Fish:
    def __init__(self, name, rarity, base_catch_time, healing):
        self.name = name
        self.rarity = rarity
        self.base_catch_time = base_catch_time
        self.healing = healing

    def catch_time(self, player_fishing_level):
        catch_time = self.base_catch_time - (player_fishing_level - 1) * 0.5
        return max(catch_time, 1)  # The catch time should not be less than 1 second.

FISH_TYPES = [
    Fish("Sardine", 1, 10, 5),
    Fish("Herring", 2, 15, 10),
    Fish("Trout", 3, 20, 15),
    Fish("Salmon", 4, 25, 20),
    Fish("Tuna", 5, 30, 25),
]

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

