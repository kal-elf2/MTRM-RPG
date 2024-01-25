from resources.inventory import Inventory
import random
import json
import discord
from emojis import get_emoji

with open("level_data.json", "r") as f:
    LEVEL_DATA = json.load(f)

class Exemplar:
    def __init__(
        self,
        name,
        stats,
        inventory=None,
    ):
        self.name = name
        self.stats = PlayerStats(
            stats["health"],
            stats["max_health"],
            stats["strength"],
            stats["stamina"],
            stats["max_stamina"],
            stats["attack"],
            stats["damage"],
            stats["defense"],
            stats["armor"],
            stats["combat_level"],
            stats["combat_experience"],
            stats["mining_level"],
            stats["mining_experience"],
            stats["woodcutting_level"],
            stats["woodcutting_experience"],
            stats["zone_level"],
            damage_taken=0

        )
        self.dice_stats = DiceStats()
        self.monster_kills = MonsterKills()
        self.inventory = inventory if inventory else Inventory()
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

    def update_total_armor(self):
        """
        Sums up the defense_modifier attributes for all equipped armor
        and shields, then stores the total in the 'armor' attribute of the player's stats.
        """
        total_defense = 0

        # Sum the defense_modifier for each equipped armor
        for armor_type, armor in self.inventory.equipped_armor.items():
            if armor:
                total_defense += armor.defense_modifier

        # Add the defense_modifier for the equipped shield, if there is one
        if self.inventory.equipped_shield:
            total_defense += self.inventory.equipped_shield.defense_modifier

        # Update the player's stats with the total defense
        self.stats.armor = total_defense

    def update_total_damage(self):
        from probabilities import weapon_specialty_bonus
        """
        Updates the 'damage' attribute of the player's stats based
        on the attack_modifier of the equipped weapon. Applies a specialty bonus
        if the equipped weapon matches the player's exemplar.
        """
        weapon_specialty = {
            "human": "Sword",
            "elf": "Bow",
            "orc": "Spear",
            "dwarf": "Hammer",
            "halfling": "Sword"
        }

        # Check if a weapon is equipped
        if self.inventory.equipped_weapon:
            specialty_bonus = 0

            # Check if equipped weapon matches player's exemplar specialty
            if weapon_specialty.get(self.name) == self.inventory.equipped_weapon.wtype:
                specialty_bonus = int(self.inventory.equipped_weapon.attack_modifier * weapon_specialty_bonus)

            # Update damage with the potential specialty bonus
            self.stats.damage = self.inventory.equipped_weapon.attack_modifier + specialty_bonus
        else:
            # If no weapon is equipped, reset the damage to its base value
            self.stats.damage = 0

    async def send_level_up_message(self, interaction, skill, new_level):
        embed = discord.Embed(color=discord.Color.blue(), title="Level Up!")
        embed.description = f"Congratulations, {interaction.user.mention}! You have reached **Level {new_level} in {skill.capitalize()}**."

        if skill == "combat":
            embed.add_field(name="⚔️ Combat Level", value=f"**{self.stats.combat_level}**   (+1)", inline=True)
            embed.add_field(name=f"{get_emoji('heart_emoji')} Health", value=f"**{self.stats.health}**   (+10)", inline=True)
            embed.add_field(name=f"{get_emoji('strength_emoji')} Strength", value=f"**{self.stats.strength}**   (+5)", inline=True)
            embed.add_field(name=f"{get_emoji('stamina_emoji')} Stamina", value=f"**{self.stats.stamina}**   (+5)",
                            inline=True)
            embed.add_field(name="🗡️ Attack", value=f"**{self.stats.attack}**   (+2)", inline=True)
            embed.add_field(name="🛡️ Defense", value=f"**{self.stats.defense}**   (+2)", inline=True)
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            increase_value = 1  # Always +1 for these skills
            if skill == "mining":
                embed.add_field(name="⛏️ Mining Level", value=f"**{new_level}**   (+{increase_value})", inline=True)
                embed.add_field(name=f"{get_emoji('strength_emoji')} Strength",
                                value=f"**{self.stats.strength}**   (+{increase_value})",
                                inline=True)
            elif skill == "woodcutting":
                embed.add_field(name="🪓 Woodcutting Level", value=f"**{new_level}**   (+{increase_value})", inline=True)
                embed.add_field(name="🗡️ Attack", value=f"**{self.stats.attack}**   (+{increase_value})", inline=True)

        return embed

    async def gain_experience(self, experience_points, experience_type, interaction=None, player=None):
        skill_exp_key = f"{experience_type}_experience"
        skill_level_key = f"{experience_type}_level"
        current_exp = getattr(self.stats, skill_exp_key)
        updated_exp = current_exp + experience_points
        setattr(self.stats, skill_exp_key, updated_exp)

        # Call the set_level method after gaining experience
        previous_level = getattr(self.stats, skill_level_key)
        updated_level, max_level = self.set_level(experience_type, updated_exp, player_object=player)

        # Send a level up message if needed
        if updated_level > previous_level:
            setattr(self.stats, skill_level_key, updated_level)

            # Reset player's health and stamina to max health upon leveling up if combat
            if experience_type == "combat":
                self.health = self.max_health
                self.stats.stamina = self.stats.max_stamina

            if interaction:
                embed = await self.send_level_up_message(interaction, experience_type, updated_level)
                return embed

        return None  # return None if there's no level-up

    def set_level(self, skill, updated_exp, player=None, player_object=None):
        new_level = 1  # Initialize to the lowest level
        for level, level_data in sorted(LEVEL_DATA.items(), key=lambda x: int(x[0])):
            if updated_exp >= level_data["total_experience"]:
                new_level = int(level) + 1
            else:
                break

        if new_level >= 100:  # Check if new level is 100
            new_level = 99
            max_level = True
        else:
            max_level = False

        if skill == "combat":
            self.stats.combat_level = new_level
            self.set_combat_stats(new_combat_level=new_level, player=player, woodcutting_level=player_object.stats.woodcutting_level, mining_level=player_object.stats.mining_level)

        elif skill == "woodcutting":
            self.stats.woodcutting_level = new_level
            self.set_combat_stats(new_combat_level=self.stats.combat_level, woodcutting_level=new_level)

        elif skill == "mining":
            self.stats.mining_level = new_level
            self.set_combat_stats(new_combat_level=self.stats.combat_level, mining_level=new_level)

        return new_level, max_level  # Also return if it's a max level or not

    @property
    def max_health(self):
        return self.stats.max_health

    def set_combat_stats(self, new_combat_level=None, player=None, woodcutting_level=None, mining_level=None):

        if player is None:
            player_name = self.name
        else:
            player_name = player.name

        if player_name == "human":
            max_health_update = 100 + (10 * (new_combat_level - 1))
            strength_update = 12 + (5 * (new_combat_level - 1))
            stamina_update = 12 + (5 * (new_combat_level - 1))
            attack_update = 6 + (2 * (new_combat_level - 1))
            defense_update = 6 + (2 * (new_combat_level - 1))

        elif player_name == "dwarf":
            max_health_update = 110 + (10 * (new_combat_level - 1))
            strength_update = 14 + (5 * (new_combat_level - 1))
            stamina_update = 10 + (5 * (new_combat_level - 1))
            attack_update = 7 + (2 * (new_combat_level - 1))
            defense_update = 5 + (2 * (new_combat_level - 1))

        elif player_name == "orc":
            max_health_update = 120 + (10 * (new_combat_level - 1))
            strength_update = 16 + (5 * (new_combat_level - 1))
            stamina_update = 8 + (5 * (new_combat_level - 1))
            attack_update = 8 + (2 * (new_combat_level - 1))
            defense_update = 4 + (2 * (new_combat_level - 1))

        elif player_name == "halfling":
            max_health_update = 90 + (10 * (new_combat_level - 1))
            strength_update = 10 + (5 * (new_combat_level - 1))
            stamina_update = 14 + (5 * (new_combat_level - 1))
            attack_update = 5 + (2 * (new_combat_level - 1))
            defense_update = 7 + (2 * (new_combat_level - 1))

        else:
            # For the Elf exemplar type
            max_health_update = 95 + (10 * (new_combat_level - 1))
            strength_update = 11 + (5 * (new_combat_level - 1))
            stamina_update = 13 + (5 * (new_combat_level - 1))
            attack_update = 6 + (2 * (new_combat_level - 1))
            defense_update = 7 + (2 * (new_combat_level - 1))

        if woodcutting_level:
            # Update attack based on woodcutting level
            attack_update += (woodcutting_level - 1)

        if mining_level:
            # Update strength based on mining level
            strength_update += (mining_level - 1)

        if player is None:
            # Update the stats
            self.stats.update_max_health(max_health_update)
            self.stats.update_strength(strength_update)
            self.stats.update_max_stamina(stamina_update)
            self.stats.update_attack(attack_update)
            self.stats.update_defense(defense_update)
        else:
            # Update the stats
            player.stats.update_max_health(max_health_update)
            player.stats.update_health(max_health_update)
            player.stats.update_strength(strength_update)
            player.stats.update_stamina(stamina_update)
            player.stats.update_max_stamina(stamina_update)
            player.stats.update_attack(attack_update)
            player.stats.update_defense(defense_update)


    def can_equip_item(self, item):
        level_requirement = item.stats['level_requirement']
        if item.type == 'weapon':
            return self.stats.strength >= level_requirement
        elif item.type == 'armor':
            return self.stats.stamina >= level_requirement
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
        base_defense = self.stats.stamina
        armor_bonus = self.equipped_armor.defense if self.equipped_armor else 0
        return base_defense + armor_bonus

    def get_potion_stack(self, potion_name):
        potion = next((p for p in self.inventory.potions if p.name == potion_name), None)
        return potion.stack if potion else 0

class DiceStats:
    def __init__(self, total_games=0, games_won=0, games_lost = 0, coppers_won=0):
        self.total_games = total_games
        self.games_won = games_won
        self.games_lost = games_lost
        self.coppers_won = coppers_won

    def to_dict(self):
        return {
            "total_games": self.total_games,
            "games_won": self.games_won,
            "games_lost": self.games_lost,
            "coppers_won": self.coppers_won
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            total_games=data.get("total_games", 0),
            games_won=data.get("games_won", 0),
            games_lost=data.get("games_lost", 0),
            coppers_won=data.get("coppers_won", 0)
        )

class MonsterKills:
    def __init__(self):
        self.monster_kills = {name: 0 for name in [
            'Rabbit',
            'Deer',
            'Buck',
            'Wolf',
            'Goblin',
            'Goblin Hunter',
            'Mega Brute',
            'Wisp',
            'Mother'
        ]}

    def to_dict(self):
        return self.monster_kills

    @classmethod
    def from_dict(cls, data):
        monster_kills = cls()
        for name in monster_kills.monster_kills:
            monster_kills.monster_kills[name] = data.get(name, 0)
        return monster_kills


class PlayerStats:
    def __init__(
        self,
        health,
        max_health,
        strength,
        stamina,
        max_stamina,
        attack,
        damage,
        defense,
        armor,
        combat_level=1,
        combat_experience=0,
        mining_level=1,
        mining_experience=0,
        woodcutting_level=1,
        woodcutting_experience=0,
        zone_level = 1,
        damage_taken =0

    ):
        self.health = health
        self.max_health = max_health
        self.strength = strength
        self.stamina = stamina
        self.max_stamina = max_stamina
        self.attack = attack
        self.damage = damage
        self.defense = defense
        self.armor = armor
        self.combat_level = combat_level
        self.combat_experience = combat_experience
        self.mining_level = mining_level
        self.mining_experience = mining_experience
        self.woodcutting_level = woodcutting_level
        self.woodcutting_experience = woodcutting_experience
        self.zone_level = zone_level
        self.damage_taken = damage_taken

    def update_health(self, update):
        self.health = update

    def update_max_health(self, update):
        self.max_health = update

    def update_strength(self, update):
        self.strength = update

    def update_stamina(self, update):
        self.stamina = update

    def update_max_stamina(self, update):
        self.max_stamina = update

    def update_attack(self, update):
        self.attack = update

    def update_defense(self, update):
        self.defense = update

class Human(Exemplar):
    def __init__(self):
        human_stats = {
            "zone_level": 1,
            "health": 100,
            "max_health": 100,
            "strength": 12,
            "stamina": 12,
            "max_stamina": 12,
            "attack": 6,
            "damage": 0,
            "defense": 6,
            "armor": 0,
            "combat_level": 1,
            "combat_experience": 0,
            "mining_level": 1,
            "mining_experience": 0,
            "woodcutting_level": 1,
            "woodcutting_experience": 0
        }
        super().__init__("Human", stats=human_stats)

class Dwarf(Exemplar):
    def __init__(self):
        dwarf_stats = {
            "zone_level": 1,
            "health": 110,
            "max_health": 110,
            "strength": 14,
            "stamina": 10,
            "max_stamina": 10,
            "attack": 7,
            "damage": 0,
            "defense": 5,
            "armor": 0,
            "combat_level": 1,
            "combat_experience": 0,
            "mining_level": 1,
            "mining_experience": 0,
            "woodcutting_level": 1,
            "woodcutting_experience": 0
        }
        super().__init__("Dwarf", stats=dwarf_stats)

class Orc(Exemplar):
    def __init__(self):
        orc_stats = {
            "zone_level": 1,
            "health": 120,
            "max_health": 120,
            "strength": 16,
            "stamina": 8,
            "max_stamina": 8,
            "attack": 8,
            "damage": 0,
            "defense": 4,
            "armor": 0,
            "combat_level": 1,
            "combat_experience": 0,
            "mining_level": 1,
            "mining_experience": 0,
            "woodcutting_level": 1,
            "woodcutting_experience": 0
        }
        super().__init__("Orc", stats=orc_stats)

class Halfling(Exemplar):
    def __init__(self):
        halfling_stats = {
            "zone_level": 1,
            "health": 90,
            "max_health": 90,
            "strength": 10,
            "stamina": 14,
            "max_stamina": 14,
            "attack": 5,
            "damage": 0,
            "defense": 7,
            "armor": 0,
            "combat_level": 1,
            "combat_experience": 0,
            "mining_level": 1,
            "mining_experience": 0,
            "woodcutting_level": 1,
            "woodcutting_experience": 0
        }
        super().__init__("Halfling", stats=halfling_stats)

class Elf(Exemplar):
    def __init__(self):
        elf_stats = {
            "zone_level": 1,
            "health": 95,
            "max_health": 95,
            "strength": 11,
            "stamina": 13,
            "max_stamina": 13,
            "attack": 6,
            "damage": 0,
            "defense": 7,
            "armor": 0,
            "combat_level": 1,
            "combat_experience": 0,
            "mining_level": 1,
            "mining_experience": 0,
            "woodcutting_level": 1,
            "woodcutting_experience": 0
        }
        super().__init__("Elf", stats=elf_stats)

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