class Tree:
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
        trees = cls(
            name=data["name"],
        )
        trees.stack = data["stack"]
        return trees

TREE_TYPES = [
    Tree("Pine"),
    Tree("Yew"),
    Tree("Ash"),
    Tree("Poplar")
]
