from resources.inventory import Inventory, Bank
from crafting.crafting import Crafting
import threading
import random
import json

with open("level_data.json", "r") as f:
    LEVEL_DATA = json.load(f)

class Exemplar:
    def __init__(
        self,
        name,
        stats,
        inventory=None,
        zone_level=1,
    ):
        self.name = name
        self.stats = PlayerStats(
            stats["health"],
            stats["max_health"],
            stats["strength"],
            stats["endurance"],
            stats["attack"],
            stats["defense"],
            stats["combat_level"],
            stats["combat_experience"],
            stats["fishing_level"],
            stats["fishing_experience"],
            stats["mining_level"],
            stats["mining_experience"],
            stats["woodcutting_level"],
            stats["woodcutting_experience"],
        )
        self.zone_level = zone_level
        self.inventory = inventory if inventory else Inventory()
        self.bank = Bank()
        self.crafting = Crafting()
        self.equipped_weapon = None
        self.equipped_armor = None
        self.attack = 0
        self.defense = 0

    def is_defeated(self):
        return self.health <= 0

    @property
    def health(self):
        return self.stats.health

    @health.setter
    def health(self, value):
        self.stats.health = value

    def increase_skill_stats(self, skill):
        if skill == "fishing":
            self.stats.update_endurance(1)
        elif skill == "mining":
            self.stats.update_strength(1)
        elif skill == "woodcutting":
            self.stats.update_attack(1)

    @staticmethod
    async def send_level_up_message(interaction, skill, new_level):
        await interaction.followup.send(
            f"Congratulations, {interaction.user.mention}! You have reached level {new_level} in {skill}."
        )

    @staticmethod
    def exp_needed_to_level_up(level):
        return LEVEL_DATA[str(level)]["total_experience"]

    async def gain_experience(self, experience_points, experience_type, interaction=None):
        skill_exp_key = f"{experience_type}_experience"
        skill_level_key = f"{experience_type}_level"
        current_exp = getattr(self.stats, skill_exp_key)
        updated_exp = current_exp + experience_points
        setattr(self.stats, skill_exp_key, updated_exp)

        # Call the set_level method after gaining experience
        previous_level = getattr(self.stats, skill_level_key)
        updated_level = self.set_level(experience_type, updated_exp)

        # Send a level up message if needed
        if updated_level > previous_level:
            setattr(self.stats, skill_level_key, updated_level)
            if interaction is not None:
                await self.send_level_up_message(interaction, experience_type, updated_level)

    def set_level(self, skill, updated_exp):
        # Find the correct level range based on the player's total experience
        for level, level_data in LEVEL_DATA.items():
            if updated_exp <= level_data["total_experience"]:
                new_level = int(level)
                break
        else:
            new_level = len(LEVEL_DATA)

        # Handle combat level up separately
        if skill == "combat":
            self.stats.combat_level = new_level
            self.increase_combat_stats()
        else:
            self.increase_skill_stats(skill)
        return new_level

    @property
    def max_health(self):
        return self.stats.max_health

    def increase_combat_stats(self):
        pass

    def level_up_mining(self):  # Add level_up_mining method
        while self.stats.mining_experience >= self.exp_needed_to_level_up(self.stats.mining_level):
            self.stats.mining_level += 1

    def level_up_fishing(self):
        while self.stats.fishing_experience >= self.exp_needed_to_level_up(self.stats.fishing_level):
            self.stats.fishing_level += 1

    def level_up_woodcutting(self):  # Add level_up_woodcutting method
        while self.stats.woodcutting_experience >= self.exp_needed_to_level_up(self.stats.woodcutting_level):
            self.stats.woodcutting_level += 1

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


class PlayerStats:
    def __init__(
        self,
        health,
        max_health,
        strength,
        endurance,
        attack,
        defense,
        combat_level=1,
        combat_experience=0,
        fishing_level=1,
        fishing_experience=0,
        mining_level=1,
        mining_experience=0,
        woodcutting_level=1,
        woodcutting_experience=0,
    ):
        self.health = health
        self.max_health = max_health
        self.strength = strength
        self.endurance = endurance
        self.attack = attack
        self.defense = defense
        self.combat_level = combat_level
        self.combat_experience = combat_experience
        self.fishing_level = fishing_level
        self.fishing_experience = fishing_experience
        self.mining_level = mining_level
        self.mining_experience = mining_experience
        self.woodcutting_level = woodcutting_level
        self.woodcutting_experience = woodcutting_experience

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
            "combat_level": 1,
            "combat_experience": 0,
            "fishing_level": 1,
            "fishing_experience": 0,
            "mining_level": 1,
            "mining_experience": 0,
            "woodcutting_level": 1,
            "woodcutting_experience": 0
        }
        super().__init__("Human", stats=human_stats)

    def increase_combat_stats(self):
        self.stats.update_health(10)
        self.stats.update_max_health(10)
        self.stats.update_strength(5)
        self.stats.update_endurance(5)
        self.stats.update_attack(2)
        self.stats.update_defense(2)

class Dwarf(Exemplar):
    def __init__(self):
        dwarf_stats = {
            "health": 110,
            "max_health": 110,
            "strength": 14,
            "endurance": 10,
            "attack": 7,
            "defense": 5,
            "combat_level": 1,
            "combat_experience": 0,
            "fishing_level": 1,
            "fishing_experience": 0,
            "mining_level": 1,
            "mining_experience": 0,
            "woodcutting_level": 1,
            "woodcutting_experience": 0
        }
        super().__init__("Dwarf", stats=dwarf_stats)

    def increase_combat_stats(self):
        self.stats.update_health(12)
        self.stats.update_max_health(12)
        self.stats.update_strength(6)
        self.stats.update_endurance(4)
        self.stats.update_attack(1)
        self.stats.update_defense(3)

class Orc(Exemplar):
    def __init__(self):
        orc_stats = {
            "health": 120,
            "max_health": 120,
            "strength": 16,
            "endurance": 8,
            "attack": 8,
            "defense": 4,
            "combat_level": 1,
            "combat_experience": 0,
            "fishing_level": 1,
            "fishing_experience": 0,
            "mining_level": 1,
            "mining_experience": 0,
            "woodcutting_level": 1,
            "woodcutting_experience": 0
        }
        super().__init__("Orc", stats=orc_stats)

    def increase_combat_stats(self):
        self.stats.update_health(15)
        self.stats.update_max_health(15)
        self.stats.update_strength(7)
        self.stats.update_endurance(3)
        self.stats.update_attack(3)
        self.stats.update_defense(1)

class Halfling(Exemplar):
    def __init__(self):
        halfling_stats = {
            "health": 90,
            "max_health": 90,
            "strength": 10,
            "endurance": 14,
            "attack": 5,
            "defense": 7,
            "combat_level": 1,
            "combat_experience": 0,
            "fishing_level": 1,
            "fishing_experience": 0,
            "mining_level": 1,
            "mining_experience": 0,
            "woodcutting_level": 1,
            "woodcutting_experience": 0
        }
        super().__init__("Halfling", stats=halfling_stats)

    def increase_combat_stats(self):
        self.stats.update_health(8)
        self.stats.update_max_health(8)
        self.stats.update_strength(4)
        self.stats.update_endurance(6)
        self.stats.update_attack(2)
        self.stats.update_defense(2)

class Elf(Exemplar):
    def __init__(self):
        elf_stats = {
            "health": 95,
            "max_health": 95,
            "strength": 11,
            "endurance": 13,
            "attack": 6,
            "defense": 7,
            "combat_level": 1,
            "combat_experience": 0,
            "fishing_level": 1,
            "fishing_experience": 0,
            "mining_level": 1,
            "mining_experience": 0,
            "woodcutting_level": 1,
            "woodcutting_experience": 0
        }
        super().__init__("Elf", stats=elf_stats)

    def increase_combat_stats(self):
        self.stats.update_health(9)
        self.stats.update_max_health(9)
        self.stats.update_strength(4)
        self.stats.update_endurance(7)
        self.stats.update_attack(3)
        self.stats.update_defense(2)


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


# class Player:
#     def __init__(self):
#         pass
#
#     def exp_needed_to_level_up(self, level):
#         return int(75 * 2 ** ((level - 2) / 7))
#
#     def exp_needed_to_reach_total(self, level):
#         return sum(self.exp_needed_to_level_up(i) for i in range(1, level))
#
#     def level_up(self, skill):
#         skill_level_key = f"{skill}_level"
#         skill_exp_key = f"{skill}_experience"
#         while getattr(self, skill_exp_key) >= self.exp_needed_to_level_up(getattr(self, skill_level_key)):
#             setattr(self, skill_level_key, getattr(self, skill_level_key) + 1)
#             self.increase_skill_stats(skill)
#
# player = Player()
#
# print("Level | Experience Needed to Reach Level | Total Experience")
# print("------+-----------------------------------+----------------")
#
# for level in range(1, 101):
#     exp_needed = player.exp_needed_to_level_up(level)
#     total_exp = player.exp_needed_to_reach_total(level)
#     print(f"{level:>5} | {exp_needed:>33} | {total_exp:>14}")


