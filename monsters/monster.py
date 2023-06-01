# monster.py
import random
from resources.loot import generate_zone_loot
from discord import Embed
import asyncio
from resources.item import Item

class Monster:
    def __init__(self, name, health, max_health, strength, endurance, experience_reward, weak_against, strong_against, attack_speed, drop):
        self.name = name
        self.health = health
        self.max_health = max_health
        self.attack = strength
        self.defense = endurance
        self.experience_reward = experience_reward
        self.weak_against = weak_against
        self.strong_against = strong_against
        self.attack_speed = attack_speed
        self.drop = drop


    def is_defeated(self):
        return self.health <= 0

def generate_monster(zone_level):
    monster_types = [
        ('Rabbit', 2, 0, 0, None, None, 0, [Item('Rabbit Body')], [1]),
        ('Deer', 5, 0, 0, None, None, 0, [Item('Deer Part'), Item('Deer Skin')], [1, 1]),
        ('Buck', 10, 3, 2, 'longbow', 'warhammer', 3, [Item('Deer Parts'), Item('Deer Skins')], [2, 3]),
        ('Wolf', 20, 5, 4, 'warhammer', 'staff', 3.5, [Item('Wolf Skin')], [1]),
        ('Goblin', 25, 6, 4, 'longsword', 'longbow', 4, [Item('Onyx')], [1]),
        ('Goblin Hunter', 35, 8, 6, 'staff', 'dual_daggers', 2.5, [Item('Onyx')], [3]),
        ('Brute', 50, 10, 8, 'dual_daggers', 'warhammer', 4.5, [Item('Onyx')], [5]),
        ('Mega Brute', 70, 12, 10, 'longsword', 'staff', 3.5, [Item('Onyx')], [10]),
        ('Wisp', 100, 15, 12, 'staff', 'longbow', 2.5, [Item('Glowing Essence')], [1]),
    ]

    monster = random.choice(monster_types)
    health = monster[1] * zone_level
    strength = monster[2] * zone_level
    endurance = monster[3] * zone_level
    experience_reward = (strength + endurance) * 2
    attack_speed = monster[6]
    max_health = health
    drop_items = [Item(name=item, description=None, value=10) for item in monster[7]]
    drop_quantities = monster[8] if isinstance(monster[8], list) else [monster[8]]
    drop = list(zip(drop_items, drop_quantities))
    return Monster(monster[0], health, max_health, strength, endurance, experience_reward, monster[4], monster[5],
                   attack_speed, drop)

def create_battle_embed(user, player, monster, message=""):
    embed = Embed(title=f"{user.name} encounters a {monster.name}")  # Remove user.mention
    embed.add_field(name="Battle", value=message, inline=False)
    embed.add_field(name=f"{user.name}'s Health", value=f"{player.health}/{player.stats.max_health}", inline=True)  # Remove user.mention
    embed.add_field(name=f"{monster.name}'s Health", value=f"{monster.health}/{monster.max_health}", inline=True)
    return embed

def calculate_hit_probability(attacker_attack, defender_defense):
    base_hit_probability = 0.75  # base hit chance, can be adjusted as needed
    attack_defense_ratio = attacker_attack / (defender_defense + 1)  # add 1 to avoid division by zero
    hit_probability = min(max(base_hit_probability * attack_defense_ratio, 0.1), 1)  # clamps the probability between 0.1 and 1
    return hit_probability

async def player_attack_task(user, player, monster, attack_modifier, message):
    while not monster.is_defeated() and not player.is_defeated():
        hit_probability = calculate_hit_probability(player.stats.attack * attack_modifier, monster.defense)
        if random.random() < hit_probability:  # if the random number is less than the hit probability, the attack hits
            damage_dealt = max(int(player.stats.attack * attack_modifier) - monster.defense, 0)
            monster.health = max(monster.health - damage_dealt, 0)  # Ensure health doesn't go below 0
            update_message = f"{user.mention} dealt {damage_dealt} damage to the {monster.name}!"
        else:
            update_message = f"The {monster.name} evaded {user.mention}'s attack!"
        battle_embed = create_battle_embed(user, player, monster, update_message)
        await message.edit(embed=battle_embed)
        await asyncio.sleep(player.equipped_weapon.attack_speed if player.equipped_weapon else 1)

async def monster_attack_task(user, player, monster, message):
    while not monster.is_defeated() and not player.is_defeated():
        hit_probability = calculate_hit_probability(monster.attack, player.stats.defense)
        if random.random() < hit_probability:  # if the random number is less than the hit probability, the attack hits
            damage_dealt = max(monster.attack - player.stats.defense, 0)
            player.stats.health = max(player.stats.health - damage_dealt, 0)  # Ensure health doesn't go below 0
            update_message = f"The {monster.name} dealt {damage_dealt} damage to {user.mention}!"
        else:
            update_message = f"{user.mention} evaded the {monster.name}'s attack!"
        battle_embed = create_battle_embed(user, player, monster, update_message)
        await message.edit(embed=battle_embed)
        await asyncio.sleep(monster.attack_speed)

async def monster_battle(user, player, monster, zone_level, message):
    player_weapon_type = player.equipped_weapon.type if player.equipped_weapon else None

    if player_weapon_type == monster.weak_against:
        print(f"The {monster.name} is weak against your {player_weapon_type}!")
        attack_modifier = 1.25
    elif player_weapon_type == monster.strong_against:
        print(f"The {monster.name} is strong against your {player_weapon_type}!")
        attack_modifier = 0.75
    else:
        attack_modifier = 1

    player_attack = asyncio.create_task(player_attack_task(user, player, monster, attack_modifier, message))
    monster_attack = asyncio.create_task(monster_attack_task(user, player, monster, message))

    await asyncio.gather(player_attack, monster_attack)

    total_damage_dealt_to_player = player.stats.max_health - player.stats.health
    total_damage_dealt_to_monster = monster.max_health - monster.health

    if monster.is_defeated():
        loot, loot_messages = generate_zone_loot(zone_level, monster.drop)
        return (True, total_damage_dealt_to_player, total_damage_dealt_to_monster, loot,
                monster.experience_reward), loot_messages
    else:
        return (False, total_damage_dealt_to_player, total_damage_dealt_to_monster, None, None), None
