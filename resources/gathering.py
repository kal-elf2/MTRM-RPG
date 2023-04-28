class Gathering:
    def __init__(self, endurance_cost):
        self.endurance_cost = endurance_cost

    def perform_action(self, player):
        if player.endurance >= self.endurance_cost:
            player.endurance -= self.endurance_cost
            return True
        return False
