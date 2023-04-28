from resources.item import Item

class Weapon(Item):
    def __init__(self, name, tier, required_level, recipe, value, weapon_type, attack, description=""):
        super().__init__(name, description, value)
        self.tier = tier
        self.required_level = required_level
        self.recipe = recipe
        self.weapon_type = weapon_type
        self.attack = attack

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "tier": self.tier,
            "required_level": self.required_level,
            "recipe": self.recipe,
            "weapon_type": self.weapon_type,
            "attack": self.attack,
        })
        return data

    @classmethod
    def from_dict(cls, data):
        weapon = cls(
            name=data["name"],
            tier=data["tier"],
            required_level=data["required_level"],
            recipe=data["recipe"],
            value=data["value"],
            weapon_type=data["weapon_type"],
            attack=data["attack"],
            description=data["description"],
        )
        weapon.amount = data["amount"]
        return weapon

WEAPON_RECIPES = [
    # Longsword
    {
        "name": "Copper Slasher",
        "item_class": Weapon,
        "tier": 1,
        "required_level": 1,
        "resources": {"Oak": 3, "Copper": 2},
        "value": 15,
        "weapon_type": "longsword",
        "attack": 5,
        "damage_multiplier": 1,
        "attack_speed": 1.5

    },
    {
        "name": "Iron Crusader",
        "item_class": Weapon,
        "tier": 2,
        "required_level": 10,
        "resources": {"Maple": 3, "Iron": 2},
        "value": 30,
        "weapon_type": "longsword",
        "attack": 10,
        "damage_multiplier": 1.25,
        "attack_speed": 1.5
    },
    {
        "name": "Silver Vanquisher",
        "item_class": Weapon,
        "tier": 3,
        "required_level": 20,
        "resources": {"Willow": 3, "Silver": 2, "Emerald": 1},
        "value": 80,
        "weapon_type": "longsword",
        "attack": 17,
        "damage_multiplier": 1.5,
        "attack_speed": 1.5
    },
    {
        "name": "Golden Conqueror",
        "item_class": Weapon,
        "tier": 4,
        "required_level": 30,
        "resources": {"Yew": 3, "Gold": 2, "Ruby": 1},
        "value": 140,
        "weapon_type": "longsword",
        "attack": 28,
        "damage_multiplier": 1.75,
        "attack_speed": 1.5
    },
    {
        "name": "Platinum Destroyer",
        "item_class": Weapon,
        "tier": 5,
        "required_level": 40,
        "resources": {"Magic": 3, "Platinum": 2, "Black Opal": 1},
        "value": 220,
        "weapon_type": "longsword",
        "attack": 37,
        "damage_multiplier": 2,
        "attack_speed": 1.5
    },

    # Warhammer
    {
        "name": "Copper Maul",
        "item_class": Weapon,
        "tier": 1,
        "required_level": 1,
        "resources": {"Oak": 4, "Copper": 3},
        "value": 25,
        "weapon_type": "warhammer",
        "attack": 6,
        "damage_multiplier": 1.5,
        "attack_speed": 1
    },
    {
        "name": "Iron Devastator",
        "item_class": Weapon,
        "tier": 2,
        "required_level": 10,
        "resources": {"Maple": 4, "Iron": 3},
        "value": 50,
        "weapon_type": "warhammer",
        "attack": 12,
        "damage_multiplier": 1.875,
        "attack_speed": 1
    },
    {
        "name": "Silver Annihilator",
        "item_class": Weapon,
        "tier": 3,
        "required_level": 20,
        "resources": {"Willow": 4, "Silver": 3, "Sapphire": 1},
        "value": 130,
        "weapon_type": "warhammer",
        "attack": 20,
        "damage_multiplier": 2.25,
        "attack_speed": 1
    },
    {
        "name": "Golden Colossus",
        "item_class": Weapon,
        "tier": 4,
        "required_level": 30,
        "resources": {"Yew": 4, "Gold": 3, "Ruby": 1},
        "value": 230,
        "weapon_type": "warhammer",
        "attack": 30,
        "damage_multiplier": 2.625,
        "attack_speed": 1
    },
    {
        "name": "Platinum Titan",
        "item_class": Weapon,
        "tier": 5,
        "required_level": 40,
        "resources": {"Magic": 4, "Platinum": 3, "Black Opal": 1},
        "value": 350,
        "weapon_type": "warhammer",
        "attack": 42,
        "damage_multiplier": 3,
        "attack_speed": 1
    },

    # Dual-wielding Daggers
    {
        "name": "Copper Fangs",
        "item_class": Weapon,
        "tier": 1,
        "required_level": 1,
        "resources": {"Oak": 2, "Copper": 1},
        "value": 10,
        "weapon_type": "dual_daggers",
        "attack": 4,
        "damage_multiplier": 0.6,
        "attack_speed": 2.5
    },
    {
        "name": "Iron Talons",
        "item_class": Weapon,
        "tier": 2,
        "required_level": 10,
        "resources": {"Maple": 2, "Iron": 1},
        "value": 20,
        "weapon_type": "dual_daggers",
        "attack": 8,
        "damage_multiplier": 0.75,
        "attack_speed": 2.5
    },
    {
        "name": "Silver Reapers",
        "item_class": Weapon,
        "tier": 3,
        "required_level": 20,
        "resources": {"Willow": 2, "Silver": 1, "Emerald": 1},
        "value": 70,
        "weapon_type": "dual_daggers",
        "attack": 14,
        "damage_multiplier": 0.9,
        "attack_speed": 2.5
    },
    {
        "name": "Golden Rippers",
        "item_class": Weapon,
        "tier": 4,
        "required_level": 30,
        "resources": {"Yew": 2, "Gold": 1, "Ruby": 1},
        "value": 130,
        "weapon_type": "dual_daggers",
        "attack": 22,
        "damage_multiplier": 1.05,
        "attack_speed": 2.5
    },
    {
        "name": "Platinum Deathblades",
        "item_class": Weapon,
        "tier": 5,
        "required_level": 40,
        "resources": {"Magic": 2, "Platinum": 1, "Black Opal": 1},
        "value": 200,
        "weapon_type": "dual_daggers",
        "attack": 32,
        "damage_multiplier": 1.2,
        "attack_speed": 2.5
    },

    # Longbow
    {
        "name": "Copperwood Longbow",
        "item_class": Weapon,
        "tier": 1,
        "required_level": 1,
        "resources": {"Oak": 3, "Copper": 1},
        "value": 15,
        "weapon_type": "longbow",
        "attack": 5,
        "damage_multiplier": 0.75,
        "attack_speed": 2
    },
    {
        "name": "Ironbark Longbow",
        "item_class": Weapon,
        "tier": 2,
        "required_level": 10,
        "resources": {"Maple": 3, "Iron": 1},
        "value": 30,
        "weapon_type": "longbow",
        "attack": 10,
        "damage_multiplier": 0.9375,
        "attack_speed": 2
    },
    {
        "name": "Silverwind Longbow",
        "item_class": Weapon,
        "tier": 3,
        "required_level": 20,
        "resources": {"Willow": 3, "Silver": 1, "Sapphire": 1},
        "value": 80,
        "weapon_type": "longbow",
        "attack": 16,
        "damage_multiplier": 1.125,
        "attack_speed": 2
    },
    {
        "name": "Goldenseed Longbow",
        "item_class": Weapon,
        "tier": 4,
        "required_level": 30,
        "resources": {"Yew": 3, "Gold": 1, "Ruby": 1},
        "value": 140,
        "weapon_type": "longbow",
        "attack": 24,
        "damage_multiplier": 1.3124,
        "attack_speed": 2
    },
    {
        "name": "Platinumspirit Longbow",
        "item_class": Weapon,
        "tier": 5,
        "required_level": 40,
        "resources": {"Magic": 3, "Platinum": 1, "Black Opal": 1},
        "value": 220,
        "weapon_type": "longbow",
        "attack": 34,
        "damage_multiplier": 1.5,
        "attack_speed": 2
    },

    # Magic Staff
    {
        "name": "Copper Arcane Staff",
        "item_class": Weapon,
        "tier": 1,
        "required_level": 1,
        "resources": {"Oak": 2, "Copper": 2},
        "value": 20,
        "weapon_type": "staff",
        "attack": 5,
        "damage_multiplier": 1,
        "attack_speed": 1.5
    },
    {
        "name": "Iron Mystic Staff",
        "item_class": Weapon,
        "tier": 2,
        "required_level": 10,
        "resources": {"Maple": 2, "Iron": 2},
        "value": 40,
        "weapon_type": "staff",
        "attack": 10,
        "damage_multiplier": 1.25,
        "attack_speed": 1.5
    },
    {
        "name": "Silver Enchanted Staff",
        "item_class": Weapon,
        "tier": 3,
        "required_level": 20,
        "resources": {"Willow": 2, "Silver": 2, "Emerald": 1},
        "value": 100,
        "weapon_type": "staff",
        "attack": 17,
        "damage_multiplier": 1.5,
        "attack_speed": 1.5
    },
    {
        "name": "Golden Sorcerer's Staff",
        "item_class": Weapon,
        "tier": 4,
        "required_level": 30,
        "resources": {"Yew": 2, "Gold": 2, "Ruby": 1},
        "value": 180,
        "weapon_type": "staff",
        "attack": 26,
        "damage_multiplier": 1.75,
        "attack_speed": 1.5
    },
    {
        "name": "Platinum Archmage Staff",
        "item_class": Weapon,
        "tier": 5,
        "required_level": 40,
        "resources": {"Magic": 2, "Platinum": 2, "Black Opal": 1},
        "value": 260,
        "weapon_type": "staff",
        "attack": 37,
        "damage_multiplier": 2,
        "attack_speed": 1.5
    }]
