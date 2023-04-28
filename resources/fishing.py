import random
import time
from gathering import Gathering
from materium import Materium
from resources.fish import FISH_TYPES, HERB_TYPES

class Fishing(Gathering):
    def __init__(self):
        super().__init__(endurance_cost=5)

    def catch_fish(self, player, fish_type):
        attempt_interval = 5  # 5 seconds between fishing attempts

        while True:
            if self.perform_action(player):
                catch_rate = self.calculate_catch_rate(player.fishing_level, fish_type)

                print(f"Attempting to catch a {fish_type.name}...")

                if self.is_fish_caught(catch_rate):
                    endurance_cost = self.calculate_endurance_cost(player)
                    if player.endurance >= endurance_cost:
                        player.endurance -= endurance_cost
                        print(f"Congratulations! You caught a {fish_type.name}!")
                        player.inventory.add_item(fish_type)  # Update player inventory with the caught fish

                        # Check if Materium is caught
                        self.fish_materium(player)  # Update player inventory with Materium if found

                        # Check if Herb is caught
                        self.fish_herb(player, fish_type)  # Update player inventory with Herb if found

                    else:
                        print("You don't have enough endurance to catch this fish.")
                else:
                    print(f"Unfortunately, you failed to catch a {fish_type.name}. Keep trying!")

            print("Press Q to quit or any other key to continue fishing:")
            user_input = input().lower()
            if user_input == 'q' or player.inventory.is_full():
                break

            time.sleep(attempt_interval)

    def fish_materium(self, player):
        materium_chance = self.calculate_materium_chance(player.fishing_level)
        if random.random() < materium_chance:
            print("Amazing! You found Materium while fishing!")
            materium = Materium()  # Create a new Materium object
            player.inventory.add_item(materium)  # Update player inventory with the Materium
        return None

    @staticmethod
    def calculate_materium_chance(skill_level):
        base_chance = 0.001  # Base chance of getting a Materium
        skill_level_factor = 0.0001 * skill_level  # Increase the chance based on the fishing level
        return base_chance + skill_level_factor

    def calculate_catch_rate(self, fishing_level, fish_type):
        base_catch_rate = 0.33  # Base catch rate for a level 1 fish at fishing level 1
        level_difference = fishing_level - fish_type.rarity
        catch_rate = base_catch_rate * (1 + level_difference * 0.1)
        return max(min(catch_rate, 1), 0)  # Clamp catch rate between 0 and 1

    def is_fish_caught(self, catch_rate):
        return random.random() < catch_rate

    def display_catch_rates(self, player):
        print("\nCatch rates for each fish type:")
        for fish_type in FISH_TYPES:
            catch_rate = self.calculate_catch_rate(player.fishing_level, fish_type)
            print(f"{fish_type.name}: {catch_rate * 100:.2f}%")

    def start_fishing(self, player):
        self.display_catch_rates(player)

        # Ask the player which fish they want to catch
        fish_choice = int(input("Choose a fish type to catch (1-5): ")) - 1
        fish_type = FISH_TYPES[fish_choice]

        if fish_choice < 0 or fish_choice >= len(FISH_TYPES):
            print("Invalid fish choice. Try again.")
            return

        self.catch_fish(player, fish_type)

    def fish_herb(self, player, fish_type):
        herb_chance = self.calculate_herb_chance(player.fishing_level, fish_type)
        if random.random() < herb_chance:
            herb = self.get_herb_by_rarity(fish_type.rarity)
            print(f"Great! You found a {herb.name} while fishing!")
            player.inventory.add_item(herb)  # Update player inventory with the herb
        return None

    @staticmethod
    def calculate_herb_chance(skill_level, fish_type):
        base_chance = 0.05  # Base chance of getting a herb
        fish_level_factor = fish_type.rarity * 0.01  # Increase the chance based on the fish rarity
        skill_level_factor = 0.01 * skill_level  # Increase the chance based on the fishing level
        return base_chance + fish_level_factor + skill_level_factor

    @staticmethod
    def get_herb_by_rarity(rarity):
        herbs = [herb for herb in HERB_TYPES if herb.rarity == rarity]
        return random.choice(herbs)

    def calculate_endurance_cost(self, player):
        base_endurance_cost = 5
        endurance_cost = base_endurance_cost - 0.1 * player.strength - 0.1 * player.fishing_level
        return max(endurance_cost, 1)  # The endurance cost should not be less than 1.
