# monster.py
import random
from resources.loot import generate_zone_loot, loot_definitions
from monsters.battle import create_battle_embed, footer_text_for_embed
import asyncio
from resources.item import Item
import math
from probabilities import CRITICAL_HIT_CHANCE, CRITICAL_HIT_MULTIPLIER, ironhide_percent, mightstone_multiplier
from emojis import get_emoji

class Monster:
    def __init__(self, name, health, max_health, attack, stamina, experience_reward, weak_against, strong_against, attack_speed, drop):
        self.name = name
        self.health = round(health)
        self.max_health = round(max_health)
        self.attack = round(attack)
        self.defense = round(stamina)
        self.experience_reward = round(experience_reward)
        self.weak_against = weak_against
        self.strong_against = strong_against
        self.attack_speed = attack_speed
        self.drop = drop

    def is_defeated(self):
        if self.health <= 0:
            self.health = 0  # Ensures health does not go below 0
            return True
        return False

def generate_monster_by_name(name, zone_level):
    monster_types = [
        ('Rabbit', 10, 1, 1, None, None, 1.5, [Item('Rabbit Body')], [1]),
        ('Deer', 20, 2, 3, None, None, 1.6, [Item('Deer Part'), Item('Deer Skin')], [1, 1]),
        ('Buck', 30, 3, 4, 'longbow', 'warhammer', 1.7, [Item('Deer Part'), Item('Deer Skin')], [2, 3]),
        ('Wolf', 50, 6, 5, 'warhammer', 'staff', 1.8, [Item('Wolf Skin')], [1]),
        ('Goblin', 100, 10, 10, 'longsword', 'longbow', 2, [Item('Onyx')], [1]),
        ('Goblin Hunter', 200, 20, 20, 'dual_daggers', 'warhammer', 2.2, [Item('Onyx')], [5]),
        ('Mega Brute', 1500, 35, 30, 'longsword', 'staff', 2.5, [Item('Onyx')], [10]),
        ('Wisp', 2000, 45, 40, 'staff', 'longbow', 2.7, [Item('Glowing Essence')], [1]),
        ('Mother', 3000, 55, 50, 'sword', 'hammer', 3, [Item('Goblin Crown'), Item('Onyx')], [1, 20])
    ]

    monster = next((m for m in monster_types if m[0] == name), None)
    if not monster:
        raise ValueError(f"No monster found with name {name}")

    # Applying zone level scaling
    health = round(monster[1] * math.sqrt(zone_level))
    attack = round(monster[2] * math.log2(zone_level + 1))
    stamina = round(monster[3] * math.log2(zone_level + 1))
    experience_reward = round((attack + stamina) * 1.5)
    attack_speed = monster[6] - (0.05 * math.log2(zone_level + 1))  # Making it slightly faster in higher zones
    max_health = health
    drop_items = [Item(name=item.name, description=loot_definitions.get(item.name, {}).get('description'), value=loot_definitions.get(item.name, {}).get('value', 10)) for item in monster[7]]
    drop_quantities = monster[8] if isinstance(monster[8], list) else [monster[8]]
    drop = list(zip(drop_items, drop_quantities))

    return Monster(monster[0], health, max_health, attack, stamina, experience_reward, monster[4], monster[5], attack_speed, drop)


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
        'Mother'
    ]
    return monster_names

def calculate_hit_probability(attacker_attack, defender_defense, player=None):
    # Check if player is wearing the Ironhide charm
    if player and player.inventory.equipped_charm and player.inventory.equipped_charm.name == "Ironhide":
        base_hit_probability = 0.75 - ironhide_percent  # Decrease base hit chance
        min_hit_chance = 0.4 - ironhide_percent  # Decrease minimum hit chance
    else:
        base_hit_probability = 0.75  # Standard base hit chance
        min_hit_chance = 0.4  # Standard minimum hit chance

    attack_defense_ratio = attacker_attack / (defender_defense + 1)  # add 1 to avoid division by zero
    hit_probability = base_hit_probability * attack_defense_ratio
    max_hit_chance = 0.9  # maximum hit chance regardless of stats

    # Return the final hit probability, ensuring it's within the defined range
    return min(max(hit_probability, min_hit_chance), max_hit_chance)


def calculate_damage(player, attacker_attack, defender_defense, is_critical_hit=False):
    attack_defense_ratio = attacker_attack / (defender_defense + 1)

    # Cap the ratio between 0.5 and 1.5 for more balanced gameplay
    attack_defense_ratio = max(0.5, min(1.5, attack_defense_ratio))

    # Generate random damage within a range
    damage = random.uniform(
        attacker_attack * attack_defense_ratio * 0.9,  # Lower bound
        attacker_attack * attack_defense_ratio * 1.1  # Upper bound
    )

    # Round to whole number
    damage_dealt = round(damage)

    # Apply critical hit multiplier if applicable
    if is_critical_hit:
        crit_multiplier = CRITICAL_HIT_MULTIPLIER
        # Check if player is the actual player and has Mightstone equipped
        if hasattr(player,
                   'inventory') and player.inventory.equipped_charm and player.inventory.equipped_charm.name == "Mightstone":
            crit_multiplier *= mightstone_multiplier  # Increases critical hit by factor of mightstone_multiplier
        damage_dealt = round(damage_dealt * crit_multiplier)

    return damage_dealt

def calculate_attack_speed_modifier(attack_value):
    # Cap the attack speed to a minimum and maximum value
    return max(1, min(3, 2 - attack_value * 0.05))

async def player_attack_task(ctx, user, player, monster, attack_modifier, message, battle_messages):
    attack_speed_modifier = calculate_attack_speed_modifier(player.stats.attack * attack_modifier)
    while not monster.is_defeated() and not player.is_defeated():
        hit_probability = calculate_hit_probability(player.stats.attack * attack_modifier, monster.defense)

        # Adjust critical hit chance if Mightstone is equipped
        crit_chance = CRITICAL_HIT_CHANCE * mightstone_multiplier if player.inventory.equipped_charm and player.inventory.equipped_charm.name == "Mightstone" else CRITICAL_HIT_CHANCE
        is_critical_hit = random.random() < crit_chance

        if random.random() < hit_probability:
            damage_dealt = calculate_damage(player, player.stats.attack * attack_modifier, monster.defense, is_critical_hit)
            monster.health = max(monster.health - damage_dealt, 0)

            # Determine the critical hit message
            if is_critical_hit:
                # Special message if wearing Mightstone and it's a critical hit
                if player.inventory.equipped_charm and player.inventory.equipped_charm.name == "Mightstone":
                    # Combine critical hit message with damage dealt message
                    update_message = f"Your {get_emoji('Mightstone')}**Mightstone Charm** glows! ***Critical hit!***\n{user.mention} dealt {damage_dealt} damage to the {monster.name}!"
                else:
                    update_message = f"{user.mention} dealt {damage_dealt} damage to the {monster.name}! ***Critical hit!***"
            else:
                update_message = f"{user.mention} dealt {damage_dealt} damage to the {monster.name}!"

        else:
            update_message = f"The {monster.name} ***evaded*** the attack of {user.mention}!"

        # Update the battle messages list
        if len(battle_messages) >= 5:
            battle_messages.pop(0)
        battle_messages.append(update_message)

        battle_embed = create_battle_embed(user, player, monster, footer_text_for_embed(ctx), battle_messages)
        await message.edit(embed=battle_embed)

        if monster.is_defeated():
            break

        await asyncio.sleep(attack_speed_modifier)


async def monster_attack_task(ctx, user, player, monster, message, battle_messages):
    attack_speed_modifier = calculate_attack_speed_modifier(monster.attack)
    while not monster.is_defeated() and not player.is_defeated():
        hit_probability = calculate_hit_probability(monster.attack, player.stats.defense, player)

        # Determine if it's a critical hit
        is_critical_hit = random.random() < CRITICAL_HIT_CHANCE

        # Check if the attack hits
        if random.random() < hit_probability:
            damage_dealt = calculate_damage(monster, monster.attack, player.stats.defense, is_critical_hit)
            player.stats.damage_taken += damage_dealt
            player.stats.health = max(player.stats.health - damage_dealt, 0)
            update_message = f"The {monster.name} dealt {damage_dealt} damage to {user.mention}!"
            if is_critical_hit:
                update_message += " ***Critical hit!***"
        else:
            if player.inventory.equipped_charm and player.inventory.equipped_charm.name == "Ironhide":
                update_message = f" Your {get_emoji('Ironhide')}**Ironhide Charm** is glowing!\n{user.mention} ***evaded*** the {monster.name}'s attack!"
            else:
                update_message = f"{user.mention} ***evaded*** the {monster.name}'s attack!"

        # Update the battle messages list
        if len(battle_messages) >= 5:
            battle_messages.pop(0)
        battle_messages.append(update_message)

        battle_embed = create_battle_embed(user, player, monster, footer_text_for_embed(ctx), battle_messages)
        await message.edit(embed=battle_embed)

        if player.is_defeated():
            break

        await asyncio.sleep(attack_speed_modifier)


async def monster_battle(ctx, user, player, monster, zone_level, message):
    # Initialize battle messages list
    battle_messages = []
    player_weapon_type = player.equipped_weapon.type if player.equipped_weapon else None

    if player_weapon_type == monster.weak_against:
        print(f"The {monster.name} is weak against your {player_weapon_type}!")
        attack_modifier = 1.25
    elif player_weapon_type == monster.strong_against:
        print(f"The {monster.name} is strong against your {player_weapon_type}!")
        attack_modifier = 0.75
    else:
        attack_modifier = 1

    player_attack = asyncio.create_task(
        player_attack_task(ctx, user, player, monster, attack_modifier, message, battle_messages))
    monster_attack = asyncio.create_task(monster_attack_task(ctx, user, player, monster, message, battle_messages))

    await asyncio.gather(player_attack, monster_attack)

    if monster.is_defeated():
        loot, loot_messages, loothaven_effect = generate_zone_loot(player, zone_level, monster.drop, monster.name)
        return (True, monster.max_health, player.stats.damage_taken, loot, monster.experience_reward,
                loothaven_effect), loot_messages
    else:
        return (False, monster.max_health, player.stats.damage_taken, None, None, False), None


