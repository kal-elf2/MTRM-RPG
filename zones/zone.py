# zone.py
from monsters.monster import generate_monster
from dungeons.dungeons import Dungeon

class Zone:
    def __init__(self, name, level):
        self.name = name
        self.level = level
        self.dungeon = Dungeon(level)

    def spawn_monster(self):
        return generate_monster(self.level)
