import json
import discord
from resources.inventory import Inventory
from exemplars.exemplars import Exemplar
from resources.herb import Herb
from exemplars.exemplars import PlayerStats
from resources.item import Item
from resources.ore import Gem, Ore
from resources.tree import Tree
from discord.ext import commands


class ExemplarJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Exemplar):
            return obj.__dict__
        elif isinstance(obj, Inventory):
            return obj.__dict__
        elif isinstance(obj, PlayerStats):
            return obj.__dict__
        elif isinstance(obj, Item):
            return obj.to_dict()
        elif isinstance(obj, Herb):
            return obj.to_dict()
        elif isinstance(obj, Gem):
            return obj.to_dict()
        elif isinstance(obj, Ore):
            return obj.to_dict()
        elif isinstance(obj, Tree):
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

async def send_message(ctx: commands.Context, embed):
    return await ctx.send(embed=embed)


def update_and_save_player_data(interaction: discord.Interaction, inventory, player_data, player=None):
    player_id = str(interaction.user.id)
    player_data[player_id]["inventory"] = inventory

    if player:
        player_data[player_id]["stats"] = player.stats

    save_player_data(interaction.guild.id, player_data)
