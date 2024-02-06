class Item:
    def __init__(self, name, description=None, value=None):
        self.name = name
        self.description = description
        self.value = value
        self.stack = 0

    def __str__(self):
        return self.name

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "value": self.value,
            "stack": self.stack,
        }

    @classmethod
    def from_dict(cls, data):
        item = cls(
            name=data["name"],
            description=data.get("description"),
            value=data.get("value"),
        )
        item.stack = data.get("stack", 0)
        return item