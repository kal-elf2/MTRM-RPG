# monster.py
import discord
import random
from resources.loot import generate_zone_loot, loot_definitions
from monsters.battle import create_battle_embed, footer_text_for_embed
import asyncio
from resources.item import Item
import math
from probabilities import CRITICAL_HIT_CHANCE, CRITICAL_HIT_MULTIPLIER, ironhide_percent, mightstone_multiplier, unarmed_damaged_reduction
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
            self.health = 0
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

class BattleContext:
    def __init__(self, ctx, user, player, monster, message, zone_level, update_callback=None):
        self.lock = asyncio.Lock()
        self.ctx = ctx
        self.user = user
        self.player = player
        self.monster = monster
        self.message = message
        self.battle_messages = []
        self.zone_level = zone_level
        self.update_callback = update_callback
        self.is_battle_active = True

    def end_battle(self):
        self.is_battle_active = False

    def update_special_attacks(self):
        if self.update_callback:
            self.update_callback(self)

    async def add_battle_message(self, new_message):
        async with self.lock:
            if len(self.battle_messages) >= 5:
                self.battle_messages.pop(0)
            self.battle_messages.append(new_message)
            await self.update_battle_embed()

    async def update_battle_embed(self):
        battle_embed = create_battle_embed(self.user, self.player, self.monster, footer_text_for_embed(self.ctx, self.monster, self.player), self.battle_messages)
        await self.message.edit(embed=battle_embed)

async def player_attack_task(battle_context, attack_level, is_unarmed=False):

    hit_probability = calculate_hit_probability(battle_context.player.stats.attack * attack_level, battle_context.monster.defense)

    # Total attack == player's attack + weapon damage
    total_player_attack = battle_context.player.stats.attack + battle_context.player.stats.damage

    # Adjust critical hit chance if Mightstone is equipped
    crit_chance = CRITICAL_HIT_CHANCE * mightstone_multiplier if battle_context.player.inventory.equipped_charm and battle_context.player.inventory.equipped_charm.name == "Mightstone" else CRITICAL_HIT_CHANCE
    is_critical_hit = random.random() < crit_chance

    if random.random() < hit_probability:
        # Check if the player is unarmed and apply damage nerf
        if is_unarmed:
            damage_reduction_multiplier = unarmed_damaged_reduction
        else:
            damage_reduction_multiplier = 1  # No reduction

        # Calculate the damage
        damage_dealt = calculate_damage(battle_context.player, total_player_attack * attack_level, battle_context.monster.defense, is_critical_hit)
        # Apply damage reduction if unarmed
        damage_dealt = round(damage_dealt * damage_reduction_multiplier)

        battle_context.monster.health = max(battle_context.monster.health - damage_dealt, 0)

        # Prepare the update message
        if is_critical_hit:
            update_message = f"{battle_context.user.mention} dealt {damage_dealt} damage to the {battle_context.monster.name}! ***Critical hit!***"
            if battle_context.player.inventory.equipped_charm and battle_context.player.inventory.equipped_charm.name == "Mightstone":
                update_message = f"Your {get_emoji('Mightstone')}**Mightstone Charm** glows! " + update_message
        else:
            update_message = f"{battle_context.user.mention} dealt {damage_dealt} damage to the {battle_context.monster.name}!"
    else:
        update_message = f"The {battle_context.monster.name} ***evaded*** the attack of {battle_context.user.mention}!"

    # Add the update message to the battle context
    await battle_context.add_battle_message(update_message)

    # Update the battle embed and special attack buttons
    await battle_context.update_battle_embed()
    battle_context.update_special_attacks()

    # Attempt to edit the message with updated view
    try:
        await battle_context.special_attack_message.edit(view=battle_context.special_attack_options_view)
    except discord.NotFound:
        print("Failed to edit message: Message not found.")

    # Check if monster is defeated and return control to the caller
    if battle_context.monster.is_defeated():
        return

async def monster_attack_task(battle_context):
    attack_speed_modifier = calculate_attack_speed_modifier(battle_context.monster.attack)

    # Total defense == player's defense + armor
    total_player_defense = battle_context.player.stats.defense + battle_context.player.stats.armor

    while battle_context.is_battle_active and not battle_context.monster.is_defeated() and not battle_context.player.is_defeated():
        hit_probability = calculate_hit_probability(battle_context.monster.attack, battle_context.player.stats.defense, battle_context.player)

        # Determine if it's a critical hit
        is_critical_hit = random.random() < CRITICAL_HIT_CHANCE

        # Check if the attack hits
        if random.random() < hit_probability:
            damage_dealt = calculate_damage(battle_context.monster, battle_context.monster.attack, total_player_defense, is_critical_hit)
            battle_context.player.stats.damage_taken += damage_dealt
            battle_context.player.stats.health = max(battle_context.player.stats.health - damage_dealt, 0)
            update_message = f"The {battle_context.monster.name} dealt {damage_dealt} damage to {battle_context.user.mention}!"
            if is_critical_hit:
                update_message += " ***Critical hit!***"
        else:
            update_message = generate_evasion_message(battle_context.player, battle_context.monster, battle_context.user)

        # Add the update message to the battle context
        await battle_context.add_battle_message(update_message)

        if battle_context.player.is_defeated():
            break

        await asyncio.sleep(attack_speed_modifier)

def generate_evasion_message(player, monster, user):
    if player.inventory.equipped_charm and player.inventory.equipped_charm.name == "Ironhide":
        return f"{get_emoji('Ironhide')} Your **Ironhide Charm** glows!\n{user.mention} ***evaded*** the {monster.name}'s attack!"
    else:
        return f"{user.mention} ***evaded*** the {monster.name}'s attack!"

async def monster_battle(battle_context):
    # Execute the monster's attack task using the battle context
    monster_attack = asyncio.create_task(monster_attack_task(battle_context))

    # Await the completion of the monster attack task
    await monster_attack

    # Check if the battle ended prematurely
    if not battle_context.is_battle_active:
        return None  # Return None to indicate that the battle ended prematurely

    # Determine the battle outcome
    if battle_context.monster.is_defeated():
        # Handle monster defeat
        loot, loot_messages, loothaven_effect = generate_zone_loot(battle_context.player, battle_context.zone_level, battle_context.monster.drop, battle_context.monster.name)
        return (True, battle_context.monster.max_health, battle_context.player.stats.damage_taken, loot, battle_context.monster.experience_reward, loothaven_effect), loot_messages
    elif battle_context.player.is_defeated():
        # Handle player defeat
        return (False, battle_context.monster.max_health, battle_context.player.stats.damage_taken, None, None, False), None
