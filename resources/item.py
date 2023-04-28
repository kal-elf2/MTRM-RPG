# item.py
class Item:
    def __init__(self, name, description=None, value=None):
        self.name = name
        self.description = description
        self.value = value
        self.stack = 0  # Add the stack attribute here

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "value": self.value,
            "stack": self.stack,  # Add the stack attribute here
        }

    @classmethod
    def from_dict(cls, data):
        item = cls(
            name=data["name"],
            description=data.get("description", None),
            value=data["value"],
        )
        item.stack = data.get("stack", 0)
        return item


