# zone.py
from dungeons.dungeons import Dungeon

class Zone:
    def __init__(self, name, level):
        self.name = name
        self.level = level
        self.dungeon = Dungeon(level)


