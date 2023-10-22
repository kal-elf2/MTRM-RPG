import random
from discord import Embed
import asyncio
import discord
import json
import numpy as np
from discord.ext import commands
from discord.commands import Option
from resources.herb import HERB_TYPES
from resources.tree import TREE_TYPES, Tree
from resources.materium import Materium
from stats import ResurrectOptions
from exemplars.exemplars import Exemplar
from emojis import get_emoji
from utils import load_player_data, save_player_data, send_message
from monsters.monster import create_battle_embed, monster_battle, generate_monster_by_name
from monsters.battle import BattleOptions, LootOptions, footer_text_for_embed
from images.urls import generate_urls
from probabilities import herb_drop_percent, mtrm_drop_percent, attack_percent

# Woodcutting experience points for each tree type
WOODCUTTING_EXPERIENCE = {
    "Pine": 20,
    "Yew": 25,
    "Ash": 50,
    "Poplar": 100
}

tree_emoji_mapping = {
    "Pine": 'pine_emoji',
    "Yew": 'yew_emoji',
    "Ash": 'ash_emoji',
    "Poplar": 'poplar_emoji'
}

with open("level_data.json", "r") as f:
    LEVEL_DATA = json.load(f)


def generate_random_monster(tree_type):
    monster_chances = {}
    if tree_type == "Pine":
        monster_chances = {'Buck': 0.25, 'Wolf': 0.75}
    elif tree_type == "Yew":
        monster_chances = {'Buck': 0.1, 'Wolf': 0.3, 'Goblin': 0.6}
    elif tree_type == "Ash":
        monster_chances = {'Goblin': 0.6, 'Goblin Hunter': 0.2, 'Mega Brute': 0.15, 'Wisp': 0.05}
    else:
        monster_chances = {'Goblin Hunter': 0.7, 'Mega Brute': 0.2, 'Wisp': 0.1}

    monsters = list(monster_chances.keys())
    probabilities = list(monster_chances.values())

    return np.random.choice(monsters, p=probabilities)

def attempt_herb_drop(zone_level):
    base_herb_drop_rate = herb_drop_percent
    herb_drop_rate = min(base_herb_drop_rate * zone_level, 1)  # Adjust the drop rate based on zone level and cap at 1

    if random.random() < herb_drop_rate:
        # Adjust the herb types based on the zone level
        herb_types_for_zone = HERB_TYPES[:zone_level]
        # Adjust the weights based on the zone level, these are now 40%, 40%, 5%, 5%, 1%
        herb_weights = [40, 40, 5, 5][:zone_level]
        herb_dropped = random.choices(herb_types_for_zone, weights=herb_weights, k=1)[0]
        return herb_dropped
    return None

# Function to handle MTRM drop
def attempt_mtrm_drop(zone_level):
    base_mtrm_drop_rate = mtrm_drop_percent
    mtrm_drop_rate = min(base_mtrm_drop_rate * zone_level, 1)  # Adjust the drop rate based on zone level and cap at 1

    if random.random() < mtrm_drop_rate:
        mtrm_dropped = Materium()  # Create a Materium object
        return mtrm_dropped
    return None

def footer_text_for_woodcutting_embed(ctx, player_level, zone_level, tree_type):
    guild_id = ctx.guild.id
    author_id = str(ctx.user.id)
    player_data = load_player_data(guild_id)

    # Use the provided WoodcuttingCog method to calculate the success probability
    probability = WoodcuttingCog.calculate_probability(player_level, zone_level, tree_type)
    success_percentage = probability * 100  # Convert to percentage for display

    woodcutting_level = player_data[author_id]["stats"]["woodcutting_level"]

    footer_text = f"🪓 Woodcutting Level:\u00A0\u00A0{woodcutting_level}\u00A0\u00A0\u00A0\u00A0|\u00A0\u00A0\u00A0\u00A0✅ Success Rate:\u00A0\u00A0{success_percentage:.1f}%"

    return footer_text


# View class for Harvest button
class HarvestButton(discord.ui.View):
    def __init__(self, ctx, player, tree_type, player_data, guild_id, author_id, embed):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.player = player
        self.tree_type = tree_type
        self.chop_messages = []
        self.player_data = player_data
        self.guild_id = guild_id
        self.author_id = author_id
        self.embed = embed

    @discord.ui.button(label="Harvest", custom_id="harvest", style=discord.ButtonStyle.blurple)
    async def harvest(self, button, interaction):
        # Check if the player has space in the inventory or if the item is already in the inventory
        if self.player.inventory.total_items_count() >= self.player.inventory.limit and not self.player.inventory.has_item(
                self.tree_type):
            await interaction.response.send_message(f"Inventory is full. Please make some room before chopping {self.tree_type}.",
                                            ephemeral=True)
            # Re-enable the button after 3 seconds
            await asyncio.sleep(2.5)
            button.disabled = False
            return

        # Disable the button immediately
        button.disabled = True
        await interaction.response.edit_message(embed=self.embed, view=self)

        stamina = self.player.stats.stamina
        player_level = self.player.stats.woodcutting_level

        if stamina <= 0:
            await interaction.followup.send("You are too tired to chop any wood.", ephemeral=True)
            # Re-enable the button after 3 seconds
            await asyncio.sleep(2.5)
            button.disabled = False
            return

        selected_tree = next((tree for tree in TREE_TYPES if tree.name == self.tree_type), None)
        if not selected_tree:
            await interaction.followup.send(f"Invalid tree type selected.", ephemeral=True)
            return

        # Calculate probability using the zone level and the tree type
        success_prob = WoodcuttingCog.calculate_probability(player_level, self.player.stats.zone_level, self.tree_type)

        success = random.random() < success_prob

        zone_level = self.player.stats.zone_level

        message = ""
        if success:
            tree_emoji = get_emoji(tree_emoji_mapping.get(self.tree_type, "🪵"))
            message = f"{tree_emoji} **Successfully chopped 1 {self.tree_type}!**"

            # Update inventory and decrement stamina
            chopped_tree = Tree(name=self.tree_type)
            self.player.inventory.add_item_to_inventory(chopped_tree, amount=1)
            self.player.stats.stamina -= 1

            # Gain woodcutting experience
            exp_gain = WOODCUTTING_EXPERIENCE[self.tree_type]
            level_up_message = await self.player.gain_experience(exp_gain, "woodcutting", interaction)

            # Attempt herb drop
            herb_dropped = attempt_herb_drop(zone_level)
            if herb_dropped:
                self.player.inventory.add_item_to_inventory(herb_dropped, amount=1)
                message += f"\n🌿 You also **found some {herb_dropped.name}!**"

            # Attempt MTRM drop
            mtrm_dropped = attempt_mtrm_drop(zone_level)
            if mtrm_dropped:
                self.player.inventory.add_item_to_inventory(mtrm_dropped, amount=1)
                message += f"\n{get_emoji('mtrm_emoji')} You also **found some Materium!**"

            self.player_data[self.author_id]["stats"][
                "woodcutting_experience"] = self.player.stats.woodcutting_experience
            self.player_data[self.author_id]["stats"]["woodcutting_level"] = self.player.stats.woodcutting_level
            self.player_data[self.author_id]["stats"]["stamina"] = self.player.stats.stamina
            save_player_data(self.guild_id, self.player_data)

            # Clear previous fields and add new ones
            self.embed.clear_fields()
            stamina_str = f"{get_emoji('stamina_emoji')}  {self.player.stats.stamina}/{self.player.stats.max_stamina}"
            # Get the new wood count
            wood_count = self.player.inventory.get_item_quantity(self.tree_type)
            wood_str = str(wood_count)

            # Calculate current woodcutting level and experience for the next level
            current_woodcutting_level = self.player.stats.woodcutting_level
            next_level = current_woodcutting_level + 1
            current_experience = self.player.stats.woodcutting_experience

            # Add updated fields to embed
            self.embed.add_field(name="Stamina", value=stamina_str, inline=True)
            self.embed.add_field(name=f"{self.tree_type}", value=f"{tree_emoji}  {wood_str}", inline=True)

            # Check if the player is at max level and add the XP field last
            if next_level >= 100:
                self.embed.add_field(name="Max Level", value=f"📊  {current_experience}", inline=True)
            else:
                next_level_experience_needed = LEVEL_DATA.get(str(current_woodcutting_level), {}).get(
                    "total_experience")
                self.embed.add_field(name=f"XP to Level {next_level}",
                                     value=f"📊  {current_experience} / {next_level_experience_needed}", inline=True)

            #Set footer to show Woodcutting level and Probability
            footer = footer_text_for_woodcutting_embed(interaction, current_woodcutting_level, zone_level,
                                                       self.tree_type)
            self.embed.set_footer(text=footer)

            # Update the chop messages list
            if len(self.chop_messages) >= 5:
                self.chop_messages.pop(0)
            self.chop_messages.append(message)

            # Prepare updated embed
            updated_description = "\n".join(self.chop_messages)
            self.embed.description = updated_description

            # Re-enable the button after 3 seconds
            await asyncio.sleep(1.75)
            button.disabled = False

            await interaction.message.edit(embed=self.embed, view=self)

            if level_up_message:  # Assuming level_up_message is an embed object
                self.player_data[self.author_id]["stats"]["attack"] = self.player.stats.attack + (
                        self.player.stats.woodcutting_level - 1)
                save_player_data(self.guild_id, self.player_data)

                await interaction.followup.send(embed=level_up_message)


        else:
            message = f"You failed to chop {self.tree_type} wood."

            # Calculate current woodcutting level and experience for the next level
            current_woodcutting_level = self.player.stats.woodcutting_level

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

            footer = footer_text_for_woodcutting_embed(interaction, current_woodcutting_level, zone_level,
                                                       self.tree_type)
            self.embed.set_footer(text=footer)

            await interaction.message.edit(embed=self.embed, view=self)

        # Monster encounter set in probabilities.py
        if np.random.rand() <= attack_percent and self.player_data[self.author_id]["in_battle"] == False:
            self.player_data[self.author_id]["in_battle"] = True
            save_player_data(self.guild_id, self.player_data)

            monster_name = generate_random_monster(self.tree_type)
            monster = generate_monster_by_name(monster_name, self.player.stats.zone_level)

            battle_embed = await send_message(interaction.channel,
                                              create_battle_embed(interaction.user, self.player, monster, footer_text_for_embed(self.ctx), messages=""))

            # Store the message object that is sent
            battle_options_msg = await self.ctx.send(view=BattleOptions(self.ctx))

            await interaction.followup.send(f"**❗ LOOK OUT {interaction.user.mention} ❗** \n You got **attacked by a {monster.name}** while harvesting {self.tree_type}.", ephemeral = True)

            battle_outcome, loot_messages = await monster_battle(self.ctx, interaction.user, self.player, monster, self.player.stats.zone_level, battle_embed)

            if battle_outcome[0]:

                experience_gained = monster.experience_reward
                await self.player.gain_experience(experience_gained, 'combat', interaction)
                self.player_data[self.author_id]["stats"]["combat_level"] = self.player.stats.combat_level
                self.player_data[self.author_id]["stats"]["combat_experience"] = self.player.stats.combat_experience
                self.player.stats.damage_taken = 0
                self.player_data[self.author_id]["stats"].update(self.player.stats.__dict__)

                if self.player.stats.health <= 0:
                    self.player.stats.health = self.player.stats.max_health

                # Save the player data after common actions
                save_player_data(self.guild_id, self.player_data)

                # Clear the previous BattleOptions view
                await battle_options_msg.delete()
                loot_view = LootOptions(interaction, self.player, monster, battle_embed, self.player_data, self.author_id, battle_outcome,
                                        loot_messages, self.guild_id, interaction, experience_gained)

                await battle_embed.edit(
                    embed=create_battle_embed(interaction.user, self.player, monster, footer_text_for_embed(self.ctx),
                                              f"You have **DEFEATED** the {monster.name}!\n\n"
                                              f"You dealt **{battle_outcome[1]} damage** to the monster and took **{battle_outcome[2]} damage**. "
                                              f"You gained {experience_gained} combat XP.\n"
                                              f"\n"),
                    view=loot_view
                )

            else:
                # The player is defeated
                self.player.stats.health = 0  # Set player's health to 0
                self.player_data[self.author_id]["stats"]["health"] = 0

                # Create a new embed with the defeat message
                new_embed = create_battle_embed(interaction.user, self.player, monster, footer_text= "", messages=

                                                f"☠️ You have been **DEFEATED** by the **{monster.name}**!\n"
                                                f"{get_emoji('rip_emoji')} *Your spirit lingers, seeking renewal.* {get_emoji('rip_emoji')}\n\n"
                                                f"__**Options for Revival:**__\n"
                                                f"1. Use {get_emoji('mtrm_emoji')} to revive without penalty.\n"
                                                f"2. Resurrect with 2.5% penalty to all skills.")

                # Clear the previous BattleOptions view
                await battle_options_msg.delete()

                # Add the "dead.png" image to the embed
                new_embed.set_image(
                    url=generate_urls("cemetery", "dead"))
                # Update the message with the new embed and view
                await battle_embed.edit(embed=new_embed, view=ResurrectOptions(interaction, self.player_data, self.author_id, new_embed))

            # Clear the in_battle flag after the battle ends
            self.player_data[self.author_id]["in_battle"] = False
            save_player_data(self.guild_id, self.player_data)

    @discord.ui.button(custom_id="stamina", style=discord.ButtonStyle.blurple, emoji=f'{get_emoji("potion_stamina")}')
    async def stamina_potion(self, button, interaction):
        pass

    @discord.ui.button(custom_id="super_stamina", style=discord.ButtonStyle.blurple, emoji=f'{get_emoji("potion_super_stamina")}')
    async def super_stamina_potion(self, button, interaction):
        pass

class WoodcuttingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def calculate_probability(player_level, zone_level, tree_type):
        base_min_levels = {
            "Pine": 0,
            "Yew": 5,
            "Ash": 10,
            "Poplar": 15
        }

        # Calculate the adjusted min level for the specific tree in the current zone
        tree_zone_min_level = base_min_levels[tree_type] + (zone_level - 1) * 20

        # Check if player's level is lower than tree's minimum level
        if player_level < tree_zone_min_level:
            return 0

        # Calculate the level difference
        level_difference = min(player_level - tree_zone_min_level, 20)

        # Determine the success probability
        probability = 0.25 + level_difference * 0.0375
        return min(1, probability)  # Ensure it doesn't exceed 100%

    @commands.slash_command(description="Chop some wood!")
    async def chop(self, ctx,
                   tree_type: Option(str, "Type of tree to chop", choices=['Pine', 'Yew', 'Ash', 'Poplar'],
                                     required=True)):
        guild_id = ctx.guild.id
        author_id = str(ctx.author.id)
        player_data = load_player_data(guild_id)

        player = Exemplar(player_data[author_id]["exemplar"],
                          player_data[author_id]["stats"],
                          player_data[author_id]["inventory"])

        base_min_levels = {
            "Pine": 0,
            "Yew": 5,
            "Ash": 10,
            "Poplar": 15
        }

        tree_min_level = base_min_levels[tree_type] + (player.stats.zone_level - 1) * 20

        tree_emoji = get_emoji(tree_emoji_mapping.get(tree_type, "🪵"))  # Default to empty string if not found

        # Check if player meets the level requirement
        if player.stats.woodcutting_level < tree_min_level:
            await ctx.respond(
                f"You need to be at least Woodcutting Level {tree_min_level} to chop {tree_type} in this zone.",
                ephemeral=True)
            return

        # Rarity and Color Mapping
        rarity_mapping = {
            1: "Common",
            2: "Uncommon",
            3: "Rare",
            4: "Epic",
            5: "Legendary"
        }

        color_mapping = {
            "Common": 0x969696,
            "Uncommon": 0x15ce00,
            "Rare": 0x0096f1,
            "Epic": 0x9900ff,
            "Legendary": 0xfebd0d
        }

        rarity = rarity_mapping.get(player.stats.zone_level)
        embed_color = color_mapping.get(rarity)

        # Start Embed
        embed = Embed(title=f"{rarity} {tree_type} Tree", color=embed_color)
        embed.set_image(url=generate_urls("trees", f'{tree_type}'))

        # Add the initial stamina and wood inventory here
        stamina_str = f"{get_emoji('stamina_emoji')}  {player.stats.stamina}/{player.stats.max_stamina}"

        # Use the get_item_quantity method to get the wood count
        wood_count = player.inventory.get_item_quantity(tree_type)
        wood_str = str(wood_count)

        # Add the initial fields to the embed
        embed.add_field(name="Stamina", value=stamina_str, inline=True)
        embed.add_field(name=f"{tree_type}", value=f"{tree_emoji}  {wood_str}", inline=True)

        # Calculate current woodcutting level and experience for the next level
        current_woodcutting_level = player.stats.woodcutting_level
        next_level = current_woodcutting_level + 1
        current_experience = player.stats.woodcutting_experience

        # Check if the player is at max level and add the XP field last
        if next_level >= 100:
            embed.add_field(name="Max Level", value=f"📊  {current_experience}", inline=True)
        else:
            next_level_experience_needed = LEVEL_DATA.get(str(current_woodcutting_level), {}).get("total_experience")
            embed.add_field(name=f"XP to Level {next_level}",
                            value=f"📊  {current_experience} / {next_level_experience_needed}", inline=True)

        # Set footer to show Woodcutting level and Probability
        footer = footer_text_for_woodcutting_embed(ctx, current_woodcutting_level, player.stats.zone_level, tree_type)
        embed.set_footer(text=footer)

        # Create the view and send the response
        view = HarvestButton(ctx, player, tree_type, player_data, guild_id, author_id, embed)

        await ctx.respond(embed=embed, view=view)


def setup(bot):
    bot.add_cog(WoodcuttingCog(bot))

