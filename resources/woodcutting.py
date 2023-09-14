import random
from discord import Embed
import asyncio
import discord
from discord.ext import commands
from discord.commands import Option
from resources.herb import HERB_TYPES
from resources.tree import TREE_TYPES, Tree
from exemplars.exemplars import Exemplar
from emojis import potion_yellow_emoji
from utils import load_player_data, save_player_data

# Woodcutting experience points for each tree type
WOODCUTTING_EXPERIENCE = {
    "Pine": 20,
    "Yew": 40,
    "Ash": 80
}

# View class for Harvest button
class HarvestButton(discord.ui.View):
    def __init__(self, interaction, player, tree_type, player_data, guild_id, author_id, embed):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.player = player
        self.tree_type = tree_type
        self.chop_messages = []
        self.player_data = player_data
        self.guild_id = guild_id
        self.author_id = author_id
        self.embed = embed

    @discord.ui.button(label="Harvest", custom_id="harvest", style=discord.ButtonStyle.blurple)
    async def harvest(self, button, interaction):

        # Disable the button immediately
        button.disabled = True
        await interaction.response.edit_message(embed=self.embed, view=self)

        endurance = self.player.stats.endurance
        player_level = self.player.stats.woodcutting_level

        if endurance <= 0:
            await interaction.followup.send("You are too tired to chop any wood.", ephemeral=True)
            # Re-enable the button after 3 seconds
            await asyncio.sleep(2.5)
            button.disabled = False
            return

        selected_tree = next((tree for tree in TREE_TYPES if tree.name == self.tree_type), None)
        if not selected_tree:
            await interaction.followup.send(f"Invalid tree type selected.", ephemeral=True)
            return

        success_prob = WoodcuttingCog.calculate_probability(player_level, selected_tree.min_level)

        if success_prob < 0.05:
            await interaction.followup.send(
                f"You are *unlikely to be successful* in chopping {self.tree_type} at your current level.\n Try again at **Woodcutting Level {selected_tree.min_level}**.",
                ephemeral=True)
            return

        success = random.random() < success_prob

        message = ""
        if success:
            message = f"Successfully chopped **1 {self.tree_type} wood**!"
            # Update inventory and decrement endurance
            chopped_tree = Tree(name=self.tree_type, min_level=selected_tree.min_level)
            self.player.inventory.add_item_to_inventory(chopped_tree, amount=1)

            self.player.stats.endurance -= 1

            # Gain woodcutting experience
            exp_gain = WOODCUTTING_EXPERIENCE[self.tree_type]
            level_up_message = await self.player.gain_experience(exp_gain, "woodcutting", interaction)

            self.player_data[self.author_id]["stats"]["woodcutting_experience"] = self.player.stats.woodcutting_experience
            self.player_data[self.author_id]["stats"]["woodcutting_level"] = self.player.stats.woodcutting_level
            self.player_data[self.author_id]["stats"]["endurance"] = self.player.stats.endurance
            save_player_data(self.guild_id, self.player_data)

            # Update the chop messages list
            if len(self.chop_messages) >= 5:
                self.chop_messages.pop(0)
            self.chop_messages.append(message)

            # Re-enable the button after 3 seconds
            await asyncio.sleep(2.25)
            button.disabled = False

            # Prepare updated embed
            updated_description = "\n".join(self.chop_messages)
            self.embed.description = updated_description

            await interaction.message.edit(embed=self.embed, view=self)

            if level_up_message:
                # Add 1 level to attack on top of current attack level
                self.player_data[self.author_id]["stats"]["attack"] = self.player.stats.attack + (
                            self.player.stats.woodcutting_level - 1)
                save_player_data(self.guild_id, self.player_data)
                # If level_up_message is not None, then the player has leveled up
                await interaction.followup.send(level_up_message)

        else:
            message = f"Failed to chop {self.tree_type} wood."

            # Update the chop messages list
            if len(self.chop_messages) >= 5:
                self.chop_messages.pop(0)
            self.chop_messages.append(message)

            # Re-enable the button after 3 seconds
            await asyncio.sleep(2.5)
            button.disabled = False

            # Prepare updated embed
            updated_description = "\n".join(self.chop_messages)
            self.embed.description = updated_description

            await interaction.message.edit(embed=self.embed, view=self)

    @discord.ui.button(custom_id="stamina", style=discord.ButtonStyle.blurple, emoji=f'{potion_yellow_emoji}')
    async def stamina_potion(self, button, interaction):
        pass


class WoodcuttingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def calculate_probability(player_level, min_level):
        if player_level < min_level:
            return 0
        elif min_level == 1:  # Pine Tree
            return min(1, 0.33 + (player_level - 1) * 0.04)
        elif min_level == 20:  # Yew Tree
            return max(0.01, min(1, (player_level - 20) * 0.05))
        elif min_level == 40:  # Ash Tree
            return max(0.01, min(1, (player_level - 40) * 0.05))

    @commands.slash_command(description="Chop some wood!")
    async def chop(self, ctx,
                   tree_type: Option(str, "Type of tree to chop", choices=['Pine', 'Yew', 'Ash'], required=True)):
        guild_id = ctx.guild.id
        author_id = str(ctx.author.id)
        player_data = load_player_data(guild_id)

        player = Exemplar(player_data[author_id]["exemplar"],
                          player_data[author_id]["stats"],
                          player_data[author_id]["inventory"])

        embed = Embed(title=f"{tree_type} Tree")
        embed.set_image(url=f"https://raw.githubusercontent.com/kal-elf2/MTRM-RPG/master/images/{tree_type}.png")
        view = HarvestButton(ctx, player, tree_type, player_data, guild_id, author_id, embed)
        await ctx.respond(embed=embed, view=view)


def setup(bot):
    bot.add_cog(WoodcuttingCog(bot))

