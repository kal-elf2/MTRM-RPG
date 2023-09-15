class Tree:
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
        trees = cls(
            name=data["name"],
            min_level=data["min_level"],
        )
        trees.stack = data["stack"]
        return trees

TREE_TYPES = [
    Tree("Pine", 1),
    Tree("Yew", 20),
    Tree("Ash", 40),
    Tree("Poplar", 60)
]
