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
import random
from images.urls import generate_urls


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

def load_player_data(guild_id, player_id):
    with open(f'server/player_data_{guild_id}.json', 'r') as f:
        all_player_data = json.load(f)

    # Convert player_id to string to ensure consistent dictionary key handling
    player_id_str = str(player_id)
    if player_id_str in all_player_data:
        player_data = all_player_data[player_id_str]
        player_data["inventory"] = Inventory.from_dict(player_data["inventory"])
        return player_data
    else:
        return None  # Player data not found

def load_all_player_data(guild_id):
    with open(f'server/player_data_{guild_id}.json', 'r') as f:
        all_player_data = json.load(f)

    for player_id, player_info in all_player_data.items():
        # Ensure that the inventory is properly converted from dict to Inventory objects
        player_info["inventory"] = Inventory.from_dict(player_info["inventory"])

    return all_player_data

def save_player_data(guild_id, player_id, updated_player_data):
    with open(f'server/player_data_{guild_id}.json', 'r') as f:
        all_player_data = json.load(f)

    # Update the specific player's data
    all_player_data[str(player_id)] = updated_player_data

    with open(f'server/player_data_{guild_id}.json', 'w') as f:
        json.dump(all_player_data, f, indent=4, cls=ExemplarJSONEncoder)


async def send_message(ctx: commands.Context, embed):
    return await ctx.send(embed=embed)

def update_and_save_player_data(interaction: discord.Interaction, inventory, player_data, player=None):
    player_id = str(interaction.user.id)
    player_data["inventory"] = inventory

    if player:
        player_data["stats"] = player.stats

    save_player_data(interaction.guild.id, player_id, player_data)

class CommonResponses:
    @staticmethod
    async def nero_unauthorized_user_response(interaction):

        nero_embed = discord.Embed(
            title="Captain Nero",
            description=get_nero_warning(interaction),
            color=discord.Color.dark_gold()
        )
        nero_embed.set_thumbnail(url=generate_urls("nero", "gun"))
        await interaction.response.send_message(embed=nero_embed, ephemeral=True)

    @staticmethod
    async def unauthorized_user_response(interaction):
        await interaction.response.send_message(
            "Apologies, but this action isn't yours to make.",
            ephemeral=True
        )

    @staticmethod
    async def ongoing_battle_response(interaction):

        battle_warning = get_nero_battle_warnings(interaction)
        nero_embed = discord.Embed(
            title="Captain Nero",
            description=battle_warning,
            color=discord.Color.dark_gold()
        )
        nero_embed.set_thumbnail(url=generate_urls("nero", "gun"))
        await interaction.response.send_message(embed=nero_embed, ephemeral=True)

    @staticmethod
    async def exit_citadel_response(interaction):

        citadel_exit_warning = leave_citadel_message(interaction)
        nero_embed = discord.Embed(
            title="Captain Nero",
            description=citadel_exit_warning,
            color=discord.Color.dark_gold()
        )
        nero_embed.set_thumbnail(url=generate_urls("nero", "confused"))
        await interaction.response.send_message(embed=nero_embed, ephemeral=True)

# User pressing wrong buttons
def get_nero_warning(interaction):
    warnings = [
        f"Arr, who be ye, {interaction.user.mention}, meddlin' with buttons that ain't yers? Keep yer hands off, or ye'll be walkin' the plank!",
        f"Ahoy, {interaction.user.mention}! These buttons ain't for landlubbers. Touch 'em again, and I'll make ye swab the deck!",
        f"Ye best be careful where ye be clickin', {interaction.user.mention}. These buttons be cursed, says I!",
        f"Avast ye, {interaction.user.mention}! Only the brave or the foolish tamper with what isn't theirs. Choose wisely!",
        f"Hoist the Jolly Roger, {interaction.user.mention}! Ye're trespassin' on dangerous waters, matey. Steer clear of what ye don't own!",
        f"Shiver me timbers, {interaction.user.mention}! You're clickin' where ye shouldn't. Keep yer mitts to yerself, or I'll feed ye to the sharks!",
        f"Blimey, {interaction.user.mention}! Ye've got the nerve of a bilge rat. Touch those buttons again, and ye'll be tastin' the cat o' nine tails!",
        f"Yo-ho-ho! Look at this sneaky sea dog, {interaction.user.mention}, tryin' to press me buttons. Do that again, and it's Davy Jones' Locker for ye!",
        f"By Blackbeard's beard, {interaction.user.mention}! Ye've got the gall of a sea serpent. Do that again, and I'll maroon ye on a deserted isle!",
        f"Arr, are ye tryin' to hornswaggle me, {interaction.user.mention}? Keep yer grubby hooks off me buttons, or I'll turn ye into chum for the fishes!"
    ]
    return random.choice(warnings)

# In a battle and tries other action that is not permitted
def get_nero_battle_warnings(interaction):
    warnings = [
        f"Avast, {interaction.user.mention}! Ye be locked in a fierce battle... **No strayin' from the fight now!**",
        f"Arr, {interaction.user.mention}! Can't ye see we're busy crossin' swords? **Keep yer focus on the battle!**",
        f"Shiver me timbers, {interaction.user.mention}! This be no time for wanderin'... **The enemy awaits, to arms!**",
        f"Blimey, {interaction.user.mention}! The deck's alive with the clash of combat... **Hold yer course, fight on!**",
        f"Yo-ho-ho, {interaction.user.mention}! Engaged in battle, we are... **Ye can't be leavin' now, stand firm!**",
    ]
    return random.choice(warnings)

# Attempts other action while in the citadel
def leave_citadel_message(interaction):
    messages = [
        f"Ye be tethered to the citadel, {interaction.user.mention}. **Hit the Exit** afore ye venture forth!",
        f"Arr, {interaction.user.mention}, the citadel's doors be closin'. **Seek the Exit** to taste freedom!",
        f"Avast, {interaction.user.mention}! The citadel holds ye yet. **Find the Exit** to continue yer journey!",
        f"Shiver me timbers, {interaction.user.mention}! Ye canna leave without **passin' through the Exit**. Off ye go!",
        f"Hoist the mainsail, {interaction.user.mention}, but not within these walls. **The Exit awaits yer departure**!",
    ]

    return random.choice(messages)
