# monster.py
import random
from resources.loot import generate_zone_loot, loot_definitions
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

def generate_monster_by_name(name, zone_level):
    monster_types = [
        ('Rabbit', 2, 1, 1, None, None, 0, [Item('Rabbit Body')], [1]),
        ('Deer', 5, 3, 2, None, None, 0, [Item('Deer Parts'), Item('Deer Skins')], [1, 1]),
        ('Buck', 10, 4, 3, 'longbow', 'warhammer', 2, [Item('Deer Parts'), Item('Deer Skins')], [2, 3]),
        ('Wolf', 20, 6, 5, 'warhammer', 'staff', 2.5, [Item('Wolf Skin')], [1]),
        ('Goblin', 35, 10, 8, 'longsword', 'longbow', 3, [Item('Onyx')], [1]),
        ('Goblin Hunter', 70, 20, 16, 'dual_daggers', 'warhammer', 3.5, [Item('Onyx')], [5]),
        ('Mega Brute', 200, 30, 26, 'longsword', 'staff', 3, [Item('Onyx')], [10]),
        ('Wisp', 260, 35, 31, 'staff', 'longbow', 2, [Item('Glowing Essence')], [1]),
    ]

    monster = next((m for m in monster_types if m[0] == name), None)
    if not monster:
        raise ValueError(f"No monster found with name {name}")

    health = monster[1] * zone_level
    strength = monster[2] * zone_level
    endurance = monster[3] * zone_level
    experience_reward = (strength + endurance) * 2
    attack_speed = monster[6]
    max_health = health
    drop_items = [Item(name=item.name, description=loot_definitions.get(item.name, {}).get('description'), value=loot_definitions.get(item.name, {}).get('value', 10)) for item in monster[7]]
    drop_quantities = monster[8] if isinstance(monster[8], list) else [monster[8]]
    drop = list(zip(drop_items, drop_quantities))

    return Monster(monster[0], health, max_health, strength, endurance, experience_reward, monster[4], monster[5],
                   attack_speed, drop)

def generate_monster_list():
    monster_names = [
        'Rabbit',
        'Deer',
        'Buck',
        'Wolf',
        'Goblin',
        'Goblin Hunter',
        'Mega Brute',
        'Wisp',
    ]
    return monster_names

def create_health_bar(current, max_health):
    bar_length = 12  # Fixed bar length
    health_percentage = current / max_health
    filled_length = round(bar_length * health_percentage)

    # Calculate how many '▣' symbols to display
    filled_symbols = '◼' * filled_length

    # Calculate how many '-' symbols to display
    empty_symbols = '◻' * (bar_length - filled_length)
    return filled_symbols + empty_symbols

def create_battle_embed(user, player, monster, message=""):
    player_health_bar = create_health_bar(player.health, player.stats.max_health)
    monster_health_bar = create_health_bar(monster.health, monster.max_health)

    # Replace spaces with '%20' for URL compatibility
    monster_name_url = monster.name.replace(" ", "%20")
    # Construct image URL
    image_url = f"https://raw.githubusercontent.com/kal-elf2/MTRM-RPG/master/images/{monster_name_url}.png"

    embed = Embed(title=f"{user.name} encounters a {monster.name}")  # Remove user.mention
    embed.add_field(name="Battle", value=message, inline=False)
    embed.add_field(name=f"{user.name}'s Health", value=f"{player.health}/{player.stats.max_health}\n{player_health_bar}", inline=True)  # Remove user.mention
    embed.add_field(name=f"{monster.name}'s Health", value=f"{monster.health}/{monster.max_health}\n{monster_health_bar}", inline=True)

    # Add image to embed
    embed.set_image(url=image_url)

    return embed

def calculate_hit_probability(attacker_attack, defender_defense):
    base_hit_probability = 0.75  # base hit chance, can be adjusted as needed
    attack_defense_ratio = attacker_attack / (defender_defense + 1)  # add 1 to avoid division by zero
    hit_probability = base_hit_probability * attack_defense_ratio
    min_hit_chance = 0.4  # minimum hit chance regardless of stats
    max_hit_chance = 0.9  # maximum hit chance regardless of stats
    return min(max(hit_probability, min_hit_chance), max_hit_chance)

def calculate_damage(attacker_attack, defender_defense, defender_health):
    attack_defense_ratio = attacker_attack / (defender_defense + 1)  # add 1 to avoid division by zero
    damage_dealt = random.uniform(max(attacker_attack * attack_defense_ratio / 2, 0), attacker_attack * attack_defense_ratio * 1.5)
    damage_dealt = max(int(damage_dealt) - defender_defense, 0)
    min_damage = int(defender_health * 0.05)  # minimum damage is 5% of the defender's health
    max_damage = int(defender_health * 0.2)  # damage cannot exceed 20% of the defender's health
    return max(min(damage_dealt, max_damage), min_damage)

async def player_attack_task(user, player, monster, attack_modifier, message):
    while not monster.is_defeated() and not player.is_defeated():
        hit_probability = calculate_hit_probability(player.stats.attack * attack_modifier, monster.defense)
        if random.random() < hit_probability:  # if the random number is less than the hit probability, the attack hits
            damage_dealt = calculate_damage(player.stats.attack * attack_modifier, monster.defense, monster.max_health)
            monster.health = max(monster.health - damage_dealt, 0)  # Ensure health doesn't go below 0
            update_message = f"{user.mention} dealt {damage_dealt} damage to the {monster.name}!"
        else:
            update_message = f"The {monster.name} evaded {user.mention}'s attack!"
        battle_embed = create_battle_embed(user, player, monster, update_message)
        await message.edit(embed=battle_embed)
        if monster.is_defeated():
            break
        await asyncio.sleep(player.equipped_weapon.attack_speed if player.equipped_weapon else 1)

async def monster_attack_task(user, player, monster, message):
    while not monster.is_defeated() and not player.is_defeated():
        hit_probability = calculate_hit_probability(monster.attack, player.stats.defense)
        if random.random() < hit_probability:  # if the random number is less than the hit probability, the attack hits
            damage_dealt = calculate_damage(monster.attack, player.stats.defense, player.stats.max_health)
            player.stats.health = max(player.stats.health - damage_dealt, 0)  # Ensure health doesn't go below 0
            update_message = f"The {monster.name} dealt {damage_dealt} damage to {user.mention}!"
        else:
            update_message = f"{user.mention} evaded the {monster.name}'s attack!"
        battle_embed = create_battle_embed(user, player, monster, update_message)
        await message.edit(embed=battle_embed)
        if player.is_defeated():
            break
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

