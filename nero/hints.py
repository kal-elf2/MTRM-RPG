import discord
import random
from images.urls import generate_urls

#spork,
# run when no stamina 50%,
# harder monsters attack you in higher zones,
# when you go to the next zone (inventory),
# attack % (married to a witch)
# deposit to ship, death doesn't matter
#Sell your items in the shop at the jolly roger
# you need Combat, Woodcutting, and Mining to be at level {} in this zone
# can't take anything with you so craft/sell as much as you can
# generosity will be rewarded

class HintsManager:
    def __init__(self):
        self.base_hints = [
            {"text": "Base Hint 1", "type": "nero", "detail": "gun"},
            {"text": "Base Hint 2", "type": "nero", "detail": "gun"},
            {"text": "Base Hint 3", "type": "nero", "detail": "gun"},
            {"text": "Base Hint 4", "type": "nero", "detail": "gun"},
            {"text": "Base Hint 5", "type": "nero", "detail": "gun"},
            {"text": "Base Hint 6", "type": "nero", "detail": "gun"},
            {"text": "Base Hint 7", "type": "nero", "detail": "gun"},
            {"text": "Base Hint 8", "type": "nero", "detail": "gun"},
            {"text": "Base Hint 9", "type": "nero", "detail": "gun"},
            {"text": "Base Hint 10", "type": "nero", "detail": "gun"},
            {"text": "Base Hint 11", "type": "nero", "detail": "gun"},
            {"text": "Base Hint 12", "type": "nero", "detail": "gun"},
        ]
        self.invites = [
            {"text": "Ahoy, mateys! This be but a taste of the grand saga! The true adventure unfolds in Mirandus that be created by Gala Games, where treasures vast and mysteries deep await ye! Hoist yer sails and join the Mirandus Discord! Treasures beyond yer wildest dreams be there, ripe for the takin'! https://discord.gg/gogalagames", "type": "Icons", "detail": "Mirandus", "is_invite": True},
            {"text": "Looking for a crew to conquer the seas? Join Everglen, the finest guild in all of Mirandus! Together, we'll claim the riches that await! https://discord.gg/94uFkRq88m", "type": "Icons", "detail": "Everglen", "is_invite": True},
        ]
        self.hint_sequence = self._generate_hint_sequence()

    def _generate_hint_sequence(self):
        # Randomly select 4 hints at a time and insert an invitation after every 4 hints
        random_hints = random.sample(self.base_hints, len(self.base_hints))
        mixed_hints = []
        while random_hints:
            for _ in range(4):
                if random_hints:
                    mixed_hints.append(random_hints.pop(0))
            if self.invites:
                # Alternating between invites
                mixed_hints.append(self.invites[0])
                self.invites.append(self.invites.pop(0))  # Move the used invite to the end of the list
        return mixed_hints

    def get_next_hint(self):
        if not self.hint_sequence:
            self.hint_sequence = self._generate_hint_sequence()
        return self.hint_sequence.pop(0)

hints_manager = HintsManager()


class HintButton(discord.ui.Button):
    def __init__(self, player):
        super().__init__(style=discord.ButtonStyle.blurple, label="\u200b", emoji=discord.PartialEmoji(name='➡️'))
        self.player = player

    async def callback(self, interaction: discord.Interaction):
        next_hint = hints_manager.get_next_hint()
        new_embed = discord.Embed(title="Tales of the Tavern", description=next_hint["text"], color=discord.Color.dark_gold())
        # Set an image for invites and a thumbnail for regular hints
        if next_hint.get("is_invite"):
            new_embed.set_image(url=generate_urls(next_hint["type"], next_hint["detail"]))
        else:
            new_embed.set_thumbnail(url=generate_urls(next_hint["type"], next_hint["detail"]))
        await interaction.response.edit_message(embed=new_embed, view=self.view)

class HintsView(discord.ui.View):
    def __init__(self, player):
        super().__init__()
        self.add_item(HintButton(player))

def create_nero_embed(player):
    description = "Of course ye want hints, **yer an ELF**! Can't trust an elf to figure things out on their own, eh?" if player.name.lower() == "elf" else "Arr, askin' for hints, are ye? Didn't reckon ye for the type. Sounds like a tactic plucked from an elf's playbook!"
    nero_embed = discord.Embed(
        title="Captain Nero",
        description=description,
        color=discord.Color.dark_gold()
    )
    nero_embed.set_thumbnail(url=generate_urls("nero", "gun"))
    view = HintsView(player)
    return nero_embed, view
