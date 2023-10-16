from resources.item import Item

class Materium(Item):
    def __init__(self):
        super().__init__(
            name="Materium",
            description="A rare and valuable resource obtained while mining.",
            value=1000,
        )
        self.stack = 0

    def copy(self):
        return Materium()
