import random
import time
from gathering import Gathering
from ore import ORE_TYPES, GEM_TYPES
from materium import Materium

class Mining(Gathering):
    def __init__(self):
        super().__init__(endurance_cost=5)

    def mine_ore(self, player, ore_type):
        attempt_interval = 5  # 5 seconds between mining attempts

        while True:
            if self.perform_action(player):
                mining_rate = self.calculate_mining_rate(player.mining_level, ore_type)

                print(f"Attempting to mine {ore_type.name}...")

                if self.is_ore_mined(mining_rate):
                    endurance_cost = self.calculate_endurance_cost(player)
                    if player.endurance >= endurance_cost:
                        player.endurance -= endurance_cost
                        print(f"Congratulations! You mined a {ore_type.name}!")
                        player.inventory.add_item(ore_type)  # Update player inventory with the mined ore

                        # Check if a gem is mined
                        gem = self.mine_gem(player)
                        if gem:
                            print(f"Wow! You also found a {gem.name} while mining!")
                            player.inventory.add_item(gem)  # Update player inventory with the mined gem

                        # Check if Materium is mined
                        self.mine_materium(player)  # Update player inventory with Materium if found

                    else:
                        print("You don't have enough endurance to mine this ore.")
                else:
                    print(f"Unfortunately, you failed to mine {ore_type.name}. Keep trying!")

            print("Press Q to quit or any other key to continue mining:")
            user_input = input().lower()
            if user_input == 'q' or player.inventory.is_full():
                break

            time.sleep(attempt_interval)

    def calculate_mining_rate(self, mining_level, ore_type):
        base_mining_rate = 0.33  # Base mining rate for a level 1 ore at mining level 1
        level_difference = mining_level - ore_type.rarity
        mining_rate = base_mining_rate * (1 + level_difference * 0.1)
        return max(min(mining_rate, 1), 0)  # Clamp mining rate between 0 and 1

    def is_ore_mined(self, mining_rate):
        return random.random() < mining_rate

    def display_mining_rates(self, player):
        print("\nMining rates for each ore type:")
        for ore_type in ORE_TYPES:
            mining_rate = self.calculate_mining_rate(player.mining_level, ore_type)
            print(f"{ore_type.name}: {mining_rate * 100:.2f}%")

    def start_mining(self, player):
        self.display_mining_rates(player)

        # Ask the player which ore they want to mine
        ore_choice = int(input("Choose an ore type to mine (1-5): ")) - 1
        ore_type = ORE_TYPES[ore_choice]

        if ore_choice < 0 or ore_choice >= len(ORE_TYPES):
            print("Invalid ore choice. Try again.")
            return

        self.mine_ore(player, ore_type)

    @staticmethod
    def calculate_gem_chance(player):
        base_chance = 0.01  # Base chance of getting a gem
        mining_level_factor = 0.001 * player.mining_level  # Increase the chance based on the mining level
        return base_chance + mining_level_factor

    @staticmethod
    def calculate_materium_chance(skill_level):
        base_chance = 0.001  # Base chance of getting a Materium
        skill_level_factor = 0.0001 * skill_level  # Increase the chance based on the mining level
        return base_chance + skill_level_factor

    def mine_materium(self, player):
        materium_chance = self.calculate_materium_chance(player.mining_level)
        if random.random() < materium_chance:
            print("Amazing! You found Materium while mining!")
            materium = Materium()  # Create a new Materium object
            player.inventory.add_item(materium)  # Update player inventory with the Materium
        return None

    def mine_gem(self, player):
        gem_chance = self.calculate_gem_chance(player)
        if random.random() < gem_chance:
            gem = random.choice(GEM_TYPES)
            return gem
        return None

    def calculate_endurance_cost(self, player):
        base_endurance_cost = 5
        endurance_cost = base_endurance_cost - 0.1 * player.strength - 0.1 * player.mining_level
        return max(endurance_cost, 1)  # The endurance cost should not be less than 1.

