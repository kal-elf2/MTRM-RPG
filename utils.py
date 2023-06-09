import json
from resources.inventory import Inventory
from exemplars.exemplars import Exemplar
from resources.fish import Herb
from exemplars.exemplars import PlayerStats, Bank
from crafting.crafting import Crafting
from resources.item import Item
from resources.ore import Gem

class ExemplarJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Exemplar):
            return obj.__dict__
        elif isinstance(obj, Inventory):
            return obj.__dict__
        elif isinstance(obj, Herb):
            return obj.to_dict()
        elif isinstance(obj, PlayerStats):
            return obj.__dict__
        elif isinstance(obj, Bank):
            return obj.__dict__
        elif isinstance(obj, Crafting):
            return obj.__dict__
        elif isinstance(obj, Item):
            return obj.to_dict()
        elif isinstance(obj, Gem):
            return obj.to_dict()
        else:
            return super().default(obj)

def load_player_data(guild_id):
    with open(f'server/player_data_{guild_id}.json', 'r') as f:
        player_data = json.load(f)

    for player_id, player_info in player_data.items():
        player_info["inventory"] = Inventory.from_dict(player_info["inventory"])

    return player_data


def save_player_data(guild_id, player_data):
    with open(f'server/player_data_{guild_id}.json', "w") as c:
        json.dump(player_data, c, indent=4, cls=ExemplarJSONEncoder)
