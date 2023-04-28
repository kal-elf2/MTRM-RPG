from resources.inventory import Inventory, Bank
from crafting.crafting import Crafting
import threading
import random

class Exemplar:
    def __init__(
        self,
        name,
        stats,
        inventory=None,
        zone_level=1,
        level=1,
        experience=0,
        fishing_level=1,
        fishing_experience=0,
        mining_level=1,
        mining_experience=0,
        woodcutting_level=1,
        woodcutting_experience=0,
    ):
        self.name = name
        self.stats = PlayerStats(
            stats["health"],
            stats["max_health"],
            stats["strength"],
            stats["endurance"],
            stats["attack"],
            stats["defense"],
            level,
            experience
        )
        self.zone_level = zone_level
        self.attack = stats["attack"]
        self.defense = stats["defense"]
        self.fishing_level = fishing_level
        self.fishing_experience = fishing_experience
        self.mining_level = mining_level
        self.mining_experience = mining_experience
        self.woodcutting_level = woodcutting_level
        self.woodcutting_experience = woodcutting_experience
        self.inventory = inventory if inventory else Inventory()
        self.bank = Bank()
        self.crafting = Crafting()
        self.equipped_weapon = None
        self.equipped_armor = None


    @property
    def health(self):
        return self.stats.health

    @health.setter
    def health(self, value):
        self.stats.health = value

    def level_up(self, skill):
        skill_level_key = f"{skill}_level"
        skill_exp_key = f"{skill}_experience"
        while getattr(self, skill_exp_key) >= self.exp_needed_to_reach_next_level(getattr(self, skill_level_key)):
            setattr(self, skill_level_key, getattr(self, skill_level_key) + 1)
            self.increase_skill_stats(skill)

    def increase_skill_stats(self, skill):
        if skill == "fishing":
            self.stats.update_endurance(1)
        elif skill == "mining":
            self.stats.update_strength(1)
        elif skill == "woodcutting":
            self.stats.update_attack(1)

    def level_up_fishing(self):
        while self.fishing_experience >= self.exp_needed_to_reach_next_level(self.fishing_level):
            self.fishing_level += 1

    def exp_needed_to_reach_next_level(self, level=None):
        if level is None:
            level = self.stats.level
        return self.exp_needed_to_level_up(level + 1) * 100

    def exp_needed_to_level_up(self, level):
        return int(25 * (2 ** (level / 7) - 2 ** ((level - 1) / 7)))

    def increase_stats(self):
        raise NotImplementedError("Each race should have a custom increase_stats method")

    def level_up_mining(self):  # Add level_up_mining method
        while self.mining_experience >= self.exp_needed_to_reach_next_level(self.mining_level):
            self.mining_level += 1

    def level_up_woodcutting(self):  # Add level_up_woodcutting method
        while self.woodcutting_experience >= self.exp_needed_to_reach_next_level(self.woodcutting_level):
            self.woodcutting_level += 1

    def gain_experience(self, exp, skill):
        if skill == 'combat':
            self.stats.experience += exp
            while self.stats.experience >= self.exp_needed_to_reach_next_level(self.stats.level):
                self.stats.level += 1
                self.increase_stats()
        else:
            skill_key = f"{skill}_experience"
            new_exp = getattr(self, skill_key) + exp
            setattr(self, skill_key, new_exp)
            self.level_up(skill)

    def can_equip_item(self, item):
        level_requirement = item.stats['level_requirement']
        if item.type == 'weapon':
            return self.stats.strength >= level_requirement
        elif item.type == 'armor':
            return self.stats.endurance >= level_requirement
        return False

    def equip_weapon(self, weapon):
        if self.can_equip_item(weapon):
            self.equipped_weapon = weapon
            self.attack = self.attack_value()  # Update attack value
        else:
            print("You don't meet the requirements to equip this weapon.")

    def equip_armor(self, armor):
        if self.can_equip_item(armor):
            self.equipped_armor = armor
            self.defense = self.defense_value()  # Update defense value
        else:
            print("You don't meet the requirements to equip this armor.")

    def attack_value(self):
        base_attack = self.stats.strength
        weapon_bonus = self.equipped_weapon.attack if self.equipped_weapon else 0
        weapon_multiplier = self.equipped_weapon.damage_multiplier if self.equipped_weapon else 1

        # Add the race-specific weapon bonus
        race_weapon_bonus = 1
        if self.equipped_weapon:
            race_weapon_bonuses = {
                "Human": {"longsword": 1.5},
                "Dwarf": {"warhammer": 1.5},
                "Orc": {"magic_staff": 1.5},
                "Halfling": {"dual_daggers": 1.5},
                "Elf": {"longbow": 1.5}
            }
            weapon_type = self.equipped_weapon.weapon_type
            race = self.name
            race_weapon_bonus = race_weapon_bonuses.get(race, {}).get(weapon_type, 1)

        # Add a random factor to the damage calculation
        random_factor = random.uniform(0.8, 1.2)  # Random float between 0.8 and 1.2

        return (base_attack + weapon_bonus) * weapon_multiplier * race_weapon_bonus * random_factor

    def defense_value(self):
        base_defense = self.stats.endurance
        armor_bonus = self.equipped_armor.defense if self.equipped_armor else 0
        return base_defense + armor_bonus

    def craft_item(self, item_type, recipe_name):
        recipe = self.crafting.get_recipe(item_type, recipe_name)
        if recipe is None:
            print(f"Recipe not found for {item_type.capitalize()} '{recipe_name}'.")
            return None

        if self.can_craft_item(recipe):
            item = self.crafting.create_item(recipe['item_class'], recipe)
            self.inventory.add_item_to_inventory(item)
            for resource, amount in recipe['resources'].items():
                self.inventory.remove_item(resource, amount)
            print(f"You have crafted a {item.name}.")
            return item
        else:
            print("You do not have the required resources to craft this item.")
            return None

    def can_craft_item(self, recipe):
        for resource, amount in recipe['resources'].items():
            if not self.inventory.has(resource, amount):
                return False
        return True

    def use_potion(self, potion):
        if not self.inventory.remove_item(potion):
            return

        if potion.effect_stat == "health":
            self.health = self.max_health()
        else:
            original_value = getattr(self, potion.effect_stat)
            new_value = original_value + potion.effect_value
            setattr(self, potion.effect_stat, new_value)

            def revert_effect():
                setattr(self, potion.effect_stat, original_value)

            threading.Timer(potion.duration, revert_effect).start()

    def max_health(self):
        raise NotImplementedError("Each race should have a custom max_health method")

class PlayerStats:
    def __init__(self, health, max_health, strength, endurance, attack, defense, level=1, experience=0):
        self.health = health
        self.max_health = max_health
        self.strength = strength
        self.endurance = endurance
        self.attack = attack
        self.defense = defense
        self.level = level
        self.experience = experience

    def update_health(self, delta):
        self.health = min(self.max_health, max(0, self.health + delta))

    def update_max_health(self, delta):
        self.max_health += delta

    def update_strength(self, delta):
        self.strength += delta

    def update_endurance(self, delta):
        self.endurance += delta

    def update_attack(self, delta):
        self.attack += delta

    def update_defense(self, delta):
        self.defense += delta


class Human(Exemplar):
    def __init__(self):
        human_stats = {
            "health": 100,
            "max_health": 100,
            "strength": 12,
            "endurance": 12,
            "attack": 6,
            "defense": 6,
        }
        super().__init__("Human", stats=human_stats)

    def increase_stats(self):
        self.stats.update_health(10)
        self.stats.update_strength(5)
        self.stats.update_endurance(5)

    def max_health(self):
        return self.stats.health + 10 * (self.stats.level - 1)
class Dwarf(Exemplar):
    def __init__(self):
        dwarf_stats = {
            "health": 110,
            "max_health": 110,
            "strength": 14,
            "endurance": 10,
            "attack": 7,
            "defense": 5,
        }
        super().__init__("Dwarf", stats=dwarf_stats)

    def increase_stats(self):
        self.stats.update_health(12)
        self.stats.update_strength(6)
        self.stats.update_endurance(4)

    def max_health(self):
        return self.stats.health + 12 * (self.stats.level - 1)
class Orc(Exemplar):
    def __init__(self):
        orc_stats = {
            "health": 120,
            "max_health": 120,
            "strength": 16,
            "endurance": 8,
            "attack": 8,
            "defense": 4,
        }
        super().__init__("Orc", stats=orc_stats)

    def max_health(self):
        return self.stats.health + 15 * (self.stats.level - 1)

    def increase_stats(self):
        self.stats.update_health(15)
        self.stats.update_strength(7)
        self.stats.update_endurance(3)
class Halfling(Exemplar):
    def __init__(self):
        halfling_stats = {
            "health": 90,
            "max_health": 90,
            "strength": 10,
            "endurance": 14,
            "attack": 5,
            "defense": 7,
        }
        super().__init__("Halfling", stats=halfling_stats)

    def max_health(self):
        return self.stats.health + 8 * (self.stats.level - 1)

    def increase_stats(self):
        self.stats.update_health(8)
        self.stats.update_strength(4)
        self.stats.update_endurance(6)

class Elf(Exemplar):
    def __init__(self):
        elf_stats = {
            "health": 95,
            "max_health": 95,
            "strength": 11,
            "endurance": 13,
            "attack": 6,
            "defense": 7,
        }
        super().__init__("Elf", stats=elf_stats)

    def increase_stats(self):
        self.stats.update_health(9)
        self.stats.update_strength(4)
        self.stats.update_endurance(7)

    def max_health(self):
        return self.stats.health + 9 * (self.stats.level - 1)

def create_exemplar(exemplar_name):
    exemplar_classes = {
        "human": Human,
        "dwarf": Dwarf,
        "orc": Orc,
        "halfling": Halfling,
        "elf": Elf
    }

    if exemplar_name not in exemplar_classes:
        return None

    exemplar_instance = exemplar_classes[exemplar_name.lower()]()
    return exemplar_instance

def exp_needed_to_level_up(level):
    return int(25 * (2 ** (level / 7) - 2 ** ((level - 1) / 7)))

def exp_needed_to_reach_total(level):
    return sum(exp_needed_to_level_up(i) for i in range(1, level)) * 100

