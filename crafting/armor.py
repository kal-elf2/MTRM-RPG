from resources.item import Item

class Armor(Item):
    def __init__(self, name, tier, required_level, recipe, value, armor_type, defense, description=""):
        super().__init__(name, description, value)
        self.tier = tier
        self.required_level = required_level
        self.recipe = recipe
        self.armor_type = armor_type
        self.defense = defense

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "tier": self.tier,
            "required_level": self.required_level,
            "recipe": self.recipe,
            "armor_type": self.armor_type,
            "defense": self.defense,
        })
        return data

    @classmethod
    def from_dict(cls, data):
        armor = cls(
            name=data["name"],
            tier=data["tier"],
            required_level=data["required_level"],
            recipe=data["recipe"],
            value=data["value"],
            armor_type=data["armor_type"],
            defense=data["defense"],
            description=data["description"],
        )
        armor.amount = data["amount"]
        return armor

ARMOR_RECIPES = [
    # Helmet
    {
        "name": "Copper Cap",
        "item_class": Armor,
        "tier": 1,
        "required_level": 1,
        "resources": {"Copper": 3},
        "value": 15,
        "armor_type": "helmet",
        "defense": 2
    },
    {
        "name": "Iron Helmet",
        "item_class": Armor,
        "tier": 2,
        "required_level": 10,
        "resources": {"Iron": 3},
        "value": 30,
        "armor_type": "helmet",
        "defense": 4
    },
    {
        "name": "Silver Helm of Clarity",
        "item_class": Armor,
        "tier": 3,
        "required_level": 20,
        "resources": {"Silver": 3, "Sapphire": 1},
        "value": 80,
        "armor_type": "helmet",
        "defense": 6
    },
    {
        "name": "Golden Helm of Might",
        "item_class": Armor,
        "tier": 4,
        "required_level": 30,
        "resources": {"Gold": 3, "Ruby": 1},
        "value": 140,
        "armor_type": "helmet",
        "defense": 8
    },
    {
        "name": "Platinum Helm of the Ancients",
        "item_class": Armor,
        "tier": 5,
        "required_level": 40,
        "resources": {"Platinum": 3, "Black Opal": 1},
        "value": 220,
        "armor_type": "helmet",
        "defense": 10
    },
    # Chestplate
    {
        "name": "Copper Chestplate",
        "item_class": Armor,
        "tier": 1,
        "required_level": 1,
        "resources": {"Copper": 5},
        "value": 25,
        "armor_type": "chestplate",
        "defense": 4
    },
    {
        "name": "Iron Cuirass",
        "item_class": Armor,
        "tier": 2,
        "required_level": 10,
        "resources": {"Iron": 5},
        "value": 50,
        "armor_type": "chestplate",
        "defense": 8
    },
    {
        "name": "Silver Breastplate of Purity",
        "item_class": Armor,
        "tier": 3,
        "required_level": 20,
        "resources": {"Silver": 5, "Sapphire": 1},
        "value": 130,
        "armor_type": "chestplate",
        "defense": 12
    },
    {
        "name": "Golden Armor of Valor",
        "item_class": Armor,
        "tier": 4,
        "required_level": 30,
        "resources": {"Gold": 5, "Ruby": 1},
        "value": 230,
        "armor_type": "chestplate",
        "defense": 16
    },
    {
        "name": "Platinum Plate of the Immortal",
        "item_class": Armor,
        "tier": 5,
        "required_level": 40,
        "resources": {"Platinum": 5, "Black Opal": 1},
        "value": 350,
        "armor_type": "chestplate",
        "defense": 20
    },

    # Legs
    {
        "name": "Copper Greaves",
        "item_class": Armor,
        "tier": 1,
        "required_level": 1,
        "resources": {"Copper": 4},
        "value": 20,
        "armor_type": "legs",
        "defense": 3
    },
    {
        "name": "Iron Leggings",
        "item_class": Armor,
        "tier": 2,
        "required_level": 10,
        "resources": {"Iron": 4},
        "value": 40,
        "armor_type": "legs",
        "defense": 6
    },
    {
        "name": "Silver Chausses of Wisdom",
        "item_class": Armor,
        "tier": 3,
        "required_level": 20,
        "resources": {"Silver": 4, "Emerald": 1},
        "value": 110,
        "armor_type": "legs",
        "defense": 9
    },
    {
        "name": "Golden Legplates of Courage",
        "item_class": Armor,
        "tier": 4,
        "required_level": 30,
        "resources": {"Gold": 4, "Ruby": 1},
        "value": 190,
        "armor_type": "legs",
        "defense": 12
    },
    {
        "name": "Platinum Cuisses of Eternity",
        "item_class": Armor,
        "tier": 5,
        "required_level": 40,
        "resources": {"Platinum": 4, "Black Opal": 1},
        "value": 300,
        "armor_type": "legs",
        "defense": 15
    },

    # Kiteshield
    {
        "name": "Copper Kiteshield",
        "item_class": Armor,
        "tier": 1,
        "required_level": 1,
        "resources": {"Copper": 4},
        "value": 20,
        "armor_type": "shield",
        "defense": 3
    },
    {
        "name": "Iron Aegis",
        "item_class": Armor,
        "tier": 2,
        "required_level": 10,
        "resources": {"Iron": 4},
        "value": 40,
        "armor_type": "shield",
        "defense": 6
    },
    {
        "name": "Silver Bulwark of Serenity",
        "item_class": Armor,
        "tier": 3,
        "required_level": 20,
        "resources": {"Silver": 4, "Sapphire": 1},
        "value": 110,
        "armor_type": "shield",
        "defense": 10
    },
    {
        "name": "Golden Bastion of Honor",
        "item_class": Armor,
        "tier": 4,
        "required_level": 30,
        "resources": {"Gold": 4, "Ruby": 1},
        "value": 190,
        "armor_type": "shield",
        "defense": 14
    },
    {
        "name": "Platinum Fortress of Destiny",
        "item_class": Armor,
        "tier": 5,
        "required_level": 40,
        "resources": {"Platinum": 4, "Black Opal": 1},
        "value": 300,
        "armor_type": "shield",
        "defense": 18
    }]

