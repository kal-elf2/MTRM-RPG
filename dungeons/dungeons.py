# dungeon.py
import random

class Dungeon:
    def __init__(self, zone_level):
        self.zone_level = zone_level
        self.rooms = self.generate_rooms()

    def generate_rooms(self):
        return [self.generate_room() for _ in range(random.randint(5, 10))]

    def generate_room(self):
        room_types = ['encounter', 'loot', 'empty', 'trap']
        return random.choice(room_types)
