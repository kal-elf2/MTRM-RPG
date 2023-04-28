# tree.py
class Tree:
    def __init__(self, name, rarity, endurance_cost, experience_reward):
        self.name = name
        self.rarity = rarity
        self.endurance_cost = endurance_cost
        self.experience_reward = experience_reward

# tree.py
TREE_TYPES = [
    Tree("Oak", 1, 3, 5),
    Tree("Maple", 2, 5, 10),
    Tree("Willow", 3, 7, 15),
    Tree("Yew", 4, 10, 20),
    Tree("Magic", 5, 15, 25),
]
