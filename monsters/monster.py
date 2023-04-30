# monster.py
import random
from resources.loot import generate_zone_loot
from discord import Embed
import asyncio

class Monster:
    def __init__(self, name, health, max_health, strength, endurance, experience_reward, weak_against, strong_against, attack_speed):
        self.name = name
        self.health = health
        self.max_health = max_health
        self.attack = strength
        self.defense = endurance
        self.experience_reward = experience_reward
        self.weak_against = weak_against
        self.strong_against = strong_against
        self.attack_speed = attack_speed

    def is_defeated(self):
        return self.health <= 0

def generate_monster(zone_level):
    monster_types = [
        ('Goblin', 10, 3, 3, 'dual_daggers', 'warhammer', 3),
        ('Skeleton', 15, 4, 4, 'warhammer', 'staff', 3.5),
        ('Zombie', 20, 5, 5, 'longsword', 'longbow', 4),
        ('Wolf', 25, 6, 6, 'longbow', 'dual_daggers', 2.5),
        ('Ogre', 30, 7, 7, 'staff', 'longsword', 4.5),
        ('Troll', 35, 8, 8, 'dual_daggers', 'longbow', 3.5),
        ('Giant Spider', 40, 9, 9, 'longbow', 'warhammer', 2.5),
        ('Wyvern', 45, 10, 10, 'staff', 'dual_daggers', 3),
        ('Golem', 50, 11, 11, 'warhammer', 'staff', 5),
        ('Dragon', 55, 12, 12, 'longsword', 'warhammer', 6)
    ]

    monster = random.choice(monster_types)
    health = monster[1] * zone_level
    strength = monster[2] * zone_level
    endurance = monster[3] * zone_level
    experience_reward = (strength + endurance) * 2
    attack_speed = monster[6]
    max_health = monster[1] * zone_level

    return Monster(monster[0], health, max_health, strength, endurance, experience_reward, monster[4], monster[5], attack_speed)
def create_battle_embed(user, player, monster, message=""):
    embed = Embed(title=f"{user.name} encounters a {monster.name}")  # Remove user.mention
    embed.add_field(name="Battle", value=message, inline=False)
    embed.add_field(name=f"{user.name}'s Health", value=f"{player.health}/{player.stats.max_health}", inline=True)  # Remove user.mention
    embed.add_field(name=f"{monster.name}'s Health", value=f"{monster.health}/{monster.max_health}", inline=True)
    return embed

async def player_attack_task(user, player, monster, attack_modifier, message):
    while not monster.is_defeated() and player.stats.health > 0:
        damage_dealt = int(player.stats.attack * attack_modifier) - monster.defense
        if damage_dealt > 0:
            monster.health = max(monster.health - damage_dealt, 0)  # Ensure health doesn't go below 0
            update_message = f"{user.mention} dealt {damage_dealt} damage to the {monster.name}!"
        else:
            update_message = f"The {monster.name} evaded {user.mention}'s attack!"
        battle_embed = create_battle_embed(user, player, monster, update_message)
        await message.edit(embed=battle_embed)
        await asyncio.sleep(player.equipped_weapon.attack_speed if player.equipped_weapon else 1)

async def monster_attack_task(user, player, monster, message):
    while not monster.is_defeated() and player.stats.health > 0:
        damage_dealt = monster.attack - player.stats.defense
        if damage_dealt > 0:
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
        loot, loot_messages = generate_zone_loot(zone_level)
        return (True, total_damage_dealt_to_player, total_damage_dealt_to_monster, loot,
                monster.experience_reward), loot_messages
    else:
        return (False, total_damage_dealt_to_player, total_damage_dealt_to_monster, None, None), None