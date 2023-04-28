import random
import time
from gathering import Gathering
from tree import TREE_TYPES
from materium import Materium
from resources.fish import HERB_TYPES

class Woodcutting(Gathering):
    def __init__(self, endurance_cost=3):
        super().__init__(endurance_cost)

    def cut_tree(self, player, tree_type):
        attempt_interval = 3  # 3 seconds between woodcutting attempts
        herb_tier = TREE_TYPES.index(tree_type)  # Get the index of the tree_type in the TREE_TYPES list

        while True:
            if self.perform_action(player):
                woodcutting_rate = self.calculate_woodcutting_rate(player.woodcutting_level, tree_type)

                print(f"Attempting to cut down {tree_type.name} tree...")

                if self.is_tree_cut(woodcutting_rate):
                    endurance_cost = self.calculate_endurance_cost(player)
                    if player.endurance >= endurance_cost:
                        player.endurance -= endurance_cost
                        print(f"Congratulations! You cut down a {tree_type.name} tree!")
                        player.inventory.add_item(tree_type)  # Update player inventory with the cut log

                        # Check if Materium is found while woodcutting
                        self.woodcut_materium(player)  # Update player inventory with Materium if found

                        # Check if Herb is found while woodcutting
                        self.woodcut_herb(player, herb_tier)  # Update player inventory with Herb if found

                    else:
                        print("You don't have enough endurance to cut down this tree.")
                else:
                    print(f"Unfortunately, you failed to cut down {tree_type.name} tree. Keep trying!")

            print("Press Q to quit or any other key to continue woodcutting:")
            user_input = input().lower()
            if user_input == 'q' or player.inventory.is_full():
                break

            time.sleep(attempt_interval)

    def woodcut_herb(self, player, herb_tier):
        herb_chance = self.calculate_herb_chance(player.woodcutting_level)
        if random.random() < herb_chance:
            herb = HERB_TYPES[herb_tier]
            print(f"Congratulations! You found a {herb.name} while woodcutting!")
            player.inventory.add_item(herb)  # Add Herb to the player's inventory


    def woodcut_materium(self, player):
        materium_chance = self.calculate_materium_chance(player.woodcutting_level)
        if random.random() < materium_chance:
            print("Congratulations! You found a Materium while woodcutting!")
            player.inventory.add_item(Materium())  # Add Materium to the player's inventory

    @staticmethod
    def calculate_materium_chance(skill_level):
        base_chance = 0.001  # Base chance of getting a Materium
        skill_level_factor = 0.0001 * skill_level  # Increase the chance based on the woodcutting level
        return base_chance + skill_level_factor

    def calculate_woodcutting_rate(self, woodcutting_level, tree_type):
        base_woodcutting_rate = 0.33
        level_difference = woodcutting_level - tree_type.rarity
        woodcutting_rate = base_woodcutting_rate * (1 + level_difference * 0.1)
        return max(min(woodcutting_rate, 1), 0)

    def is_tree_cut(self, woodcutting_rate):
        return random.random() < woodcutting_rate

    def display_woodcutting_rates(self, player):
        print("\nWoodcutting rates for each tree type:")
        for tree_type in TREE_TYPES:
            woodcutting_rate = self.calculate_woodcutting_rate(player.woodcutting_level, tree_type)
            print(f"{tree_type.name}: {woodcutting_rate * 100:.2f}%")

    def start_woodcutting(self, player):
        self.display_woodcutting_rates(player)

        # Ask the player which tree they want to cut
        tree_choice = int(input("Choose a tree type to cut (1-5): ")) - 1
        tree_type = TREE_TYPES[tree_choice]

        if tree_choice < 0 or tree_choice >= len(TREE_TYPES):
            print("Invalid tree choice. Try again.")
            return

        self.cut_tree(player, tree_type)

    @staticmethod
    def calculate_herb_chance(skill_level):
        base_chance = 0.01  # Base chance of getting a Herb
        skill_level_factor = 0.0005 * skill_level  # Increase the chance based on the woodcutting level
        return base_chance + skill_level_factor

    def calculate_endurance_cost(self, player):
        base_endurance_cost = 5
        endurance_cost = base_endurance_cost - 0.1 * player.strength - 0.1 * player.woodcutting_level
        return max(endurance_cost, 1)  # The endurance cost should not be less than 1.

