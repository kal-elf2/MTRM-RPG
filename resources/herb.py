

class Herb:
    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.stack = 0

    def to_dict(self):
        return {
            "name": self.name,
            "value": self.value,
            "stack": self.stack,
        }

    @classmethod
    def from_dict(cls, data):
        herb = cls(
            name=data["name"],
            value=data["value"],
        )
        herb.stack = data["stack"]
        return herb

HERB_TYPES = [
    Herb("Ranarr", 25), # for Stamina Potion
    Herb("Spirit Weed", 25), # for Health Potion
    Herb("Snapdragon", 350), # for Super Stamina Potion
    Herb("Bloodweed", 350), # for Super Health Potion
]

