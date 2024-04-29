# This dictionary stores the default settings for game mechanics.
# Each setting has a comment indicating its original value and purpose.

default_settings = {
    # Base percentages for various drop rates
    "mtrm_drop_percent": 0.01,  # 1% chance, loot drop
    "herb_drop_percent": 0.15,  # 15% chance, loot drop
    "potion_drop_percent": 0.10,  # 10% chance, loot drop
    "spork_chance": 0.001,  # 0.1% chance, rare item drop
    "spork_value": 100000,  # value of spork item

    # Attack probabilities
    "attack_percent": 0.075,  # 7.5% chance, monster attack
    "brute_percent": 0.05,  # 5% chance, citadel exit brute attack

    # Charms probabilities
    "stonebreaker_percent": 0.15,  # 15% chance, specific charm effect
    "woodcleaver_percent": 0.15,  # 15% chance, specific charm effect
    "loothaven_percent": 0.15,  # 15% chance, specific charm effect
    "ironhide_percent": 0.15,  # 15% chance, specific charm effect
    "ironhide_multiplier": 2,  # double run multiplier
    "mightstone_multiplier": 2,  # double multiplier

    # Other settings
    "buyback_cost": 5000,  # max cost per zone, Nero's death buyback
    "weapon_specialty_bonus": 0.05,  # 5% bonus to damage for weapon specialty
    "death_penalty": 0.05,  # 5% stat reduction upon death
    "CRITICAL_HIT_CHANCE": 0.10,  # 10% chance of a critical hit
    "CRITICAL_HIT_MULTIPLIER": 1.5,  # 1.5 times the damage for a critical hit
    "base_run_chance": 0.25,  # base chance to run away
    "base_zone_supply_requirement": 10,  # base supply requirement * zone level
    "tent_health": 25,  # HP per heal from tent
    "unarmed_damaged_reduction": 0.05  # 95% damage reduction when unarmed
}
# get_server_setting(guild_id, '')