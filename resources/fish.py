class Fish:
    def __init__(self, name, min_level):
        self.name = name
        self.min_level = min_level
        self.stack = 0  # Number of this type of fish caught

    def to_dict(self):
        return {
            "name": self.name,
            "min_level": self.min_level,
            "stack": self.stack,
        }

    @classmethod
    def from_dict(cls, data):
        fish = cls(
            name=data["name"],
            min_level=data["min_level"],
        )
        fish.stack = data["stack"]
        return fish

FISH_TYPES = [
    Fish("Herring", 1),
    Fish("Trout", 20),
    Fish("Tuna", 40),
    Fish("Swordfish", 60)
]
