import random
from discord import Embed
import asyncio
import discord
import json
import numpy as np
from discord.ext import commands
from discord.commands import Option
from resources.ore import GEM_TYPES, ORE_TYPES, Ore
from resources.materium import Materium
from stats import ResurrectOptions
from exemplars.exemplars import Exemplar
from emojis import potion_yellow_emoji, rip_emoji, mtrm_emoji
from utils import load_player_data, save_player_data, send_message
from monsters.monster import create_battle_embed, monster_battle, generate_monster_by_name
from monsters.battle import BattleOptions, LootOptions
from images.urls import generate_urls
from emojis import coal_emoji, carbon_emoji, iron_emoji

# Woodcutting experience points for each tree type
MINING_EXPERIENCE = {
    "Iron": 20,
    "Coal": 25,
    "Carbon": 50
}

ORE_EMOJIS = {
    "Coal": coal_emoji,
    "Carbon": carbon_emoji,
    "Iron": iron_emoji
}

with open("level_data.json", "r") as f:
    LEVEL_DATA = json.load(f)

def generate_random_monster(ore_type):
    monster_chances = {}
    if ore_type == "Iron":
        monster_chances = {'Buck': 0.25, 'Wolf': 0.75}
    elif ore_type == "Coal":
        monster_chances = {'Buck': 0.1, 'Wolf': 0.3, 'Goblin': 0.6}
    elif ore_type == "Carbon":
        monster_chances = {'Goblin': 0.6, 'Goblin Hunter': 0.2, 'Mega Brute': 0.15, 'Wisp': 0.05}

    monsters = list(monster_chances.keys())
    probabilities = list(monster_chances.values())

    return np.random.choice(monsters, p=probabilities)

def attempt_gem_drop(zone_level):
    gem_drop_rate = 0.10  # 10% chance to drop a gem
    if random.random() < gem_drop_rate:
        # Adjust the gem types based on the zone level
        gem_types_for_zone = GEM_TYPES[:zone_level]
        # Adjust the weights based on the zone level, these are now 40%, 40%, 5%, 5%, 1%
        gem_weights = [40, 40, 10, 5, 1][:zone_level]
        gem_dropped = random.choices(gem_types_for_zone, weights=gem_weights, k=1)[0]
        return gem_dropped
    return None

# Function to handle MTRM drop
def attempt_mtrm_drop(zone_level):
    mtrm_drop_rate = 0.01  # 1% chance to drop MTRM
    if random.random() < mtrm_drop_rate:
        mtrm_dropped = Materium()  # Create a Materium object
        mtrm_dropped.stack = zone_level  # Set the stack attribute to be the zone level
        return mtrm_dropped
    return None


# View class for Harvest button
class MineButton(discord.ui.View):
    def __init__(self, ctx, player, ore_type, player_data, guild_id, author_id, embed):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.player = player
        self.ore_type = ore_type
        self.mine_messages = []
        self.player_data = player_data
        self.guild_id = guild_id
        self.author_id = author_id
        self.embed = embed

    @discord.ui.button(label="Mine", custom_id="mine", style=discord.ButtonStyle.blurple)
    async def mine(self, button, interaction):

        # Disable the button immediately
        button.disabled = True
        await interaction.response.edit_message(embed=self.embed, view=self)

        endurance = self.player.stats.endurance
        player_level = self.player.stats.mining_level

        if endurance <= 0:
            await interaction.followup.send("You are too tired to mine any ore.", ephemeral=True)
            # Re-enable the button after 3 seconds
            await asyncio.sleep(2.5)
            button.disabled = False
            return

        selected_ore = next((ore for ore in ORE_TYPES if ore.name == self.ore_type), None)
        if not selected_ore:
            await interaction.followup.send(f"Invalid ore type selected.", ephemeral=True)
            return

        success_prob = MiningCog.calculate_probability(player_level, self.player.stats.zone_level, self.ore_type)

        success = random.random() < success_prob

        ore_emoji = ORE_EMOJIS.get(self.ore_type, "🪨")  # Default to a rock emoji if no specific emoji is found.

        message = ""
        if success:
            message = f"**Successfully mined 1 {self.ore_type}! {ore_emoji}**"

            # Update inventory and decrement endurance
            mined_ore = Ore(name=self.ore_type)
            self.player.inventory.add_item_to_inventory(mined_ore, amount=1)
            self.player.stats.endurance -= 1

            # Gain mining experience
            exp_gain = MINING_EXPERIENCE[self.ore_type]
            level_up_message = await self.player.gain_experience(exp_gain, "mining", interaction)

            # Attempt gem drop
            zone_level = self.player.stats.zone_level
            gem_dropped = attempt_gem_drop(zone_level)
            if gem_dropped:
                self.player.inventory.add_item_to_inventory(gem_dropped, amount=1)
                message += f"\nYou also **found a {gem_dropped.name}!** 💎"

            # Attempt MTRM drop
            mtrm_dropped = attempt_mtrm_drop(zone_level)
            if mtrm_dropped:
                self.player.inventory.add_item_to_inventory(mtrm_dropped, amount=1)
                message += f"\nYou also **found some Materium!** {mtrm_emoji}"

            self.player_data[self.author_id]["stats"][
                "mining_experience"] = self.player.stats.mining_experience
            self.player_data[self.author_id]["stats"]["mining_level"] = self.player.stats.mining_level
            self.player_data[self.author_id]["stats"]["endurance"] = self.player.stats.endurance
            save_player_data(self.guild_id, self.player_data)

            # Clear previous fields and add new ones
            self.embed.clear_fields()
            # Include the yellow potion emoji for the stamina/endurance string
            stamina_str = f"{potion_yellow_emoji}  {self.player.stats.endurance}/{self.player.stats.max_endurance}"
            # Get the new ore count
            ore_count = self.player.inventory.get_ore_count(self.ore_type)
            ore_str = str(ore_count)

            # Calculate current mining level and experience for the next level
            current_mining_level = self.player.stats.mining_level
            next_level = current_mining_level + 1
            current_experience = self.player.stats.mining_experience

            # Add updated fields to embed
            self.embed.add_field(name="Endurance", value=stamina_str, inline=True)
            self.embed.add_field(name=f"{self.ore_type}", value=f"{ore_str} {ore_emoji}", inline=True)

            # Check if the player is at max level and add the XP field last
            if next_level >= 100:
                self.embed.add_field(name="Max Level", value=f"📊  {current_experience}", inline=True)
            else:
                next_level_experience_needed = LEVEL_DATA.get(str(current_mining_level), {}).get(
                    "total_experience")
                self.embed.add_field(name=f"XP to Level {next_level}",
                                     value=f"📊  {current_experience} / {next_level_experience_needed}", inline=True)

            # Update the mine messages list
            if len(self.mine_messages) >= 5:
                self.mine_messages.pop(0)
            self.mine_messages.append(message)

            # Prepare updated embed
            updated_description = "\n".join(self.mine_messages)
            self.embed.description = updated_description

            # Re-enable the button after 3 seconds
            await asyncio.sleep(1.75)
            button.disabled = False

            await interaction.message.edit(embed=self.embed, view=self)

            if level_up_message:
                self.player_data[self.author_id]["stats"]["strength"] = self.player.stats.strength + (
                        self.player.stats.mining_level - 1)
                save_player_data(self.guild_id, self.player_data)

                await interaction.followup.send(embed=level_up_message)

        else:
            message = f"Failed to mine {self.ore_type} ore."

            # Update the mine messages list
            if len(self.mine_messages) >= 5:
                self.mine_messages.pop(0)
            self.mine_messages.append(message)

            # Re-enable the button after 3 seconds
            await asyncio.sleep(2.25)
            button.disabled = False

            # Prepare updated embed
            updated_description = "\n".join(self.mine_messages)
            self.embed.description = updated_description

            await interaction.message.edit(embed=self.embed, view=self)

        # 10% chance of a monster encounter
        if np.random.rand() <= 0.10 and self.player_data[self.author_id]["in_battle"] == False:
            self.player_data[self.author_id]["in_battle"] = True
            save_player_data(self.guild_id, self.player_data)

            monster_name = generate_random_monster(self.ore_type)
            monster = generate_monster_by_name(monster_name, self.player.stats.zone_level)

            battle_embed = await send_message(interaction.channel,
                                              create_battle_embed(interaction.user, self.player, monster, messages=""))

            # Store the message object that is sent
            battle_options_msg = await self.ctx.send(view=BattleOptions(self.ctx))

            await interaction.followup.send(f"**❗ LOOK OUT {interaction.user.mention} ❗** \n You got **attacked by a {monster.name}** while mining {self.ore_type}.", ephemeral = True)

            battle_outcome, loot_messages = await monster_battle(interaction.user, self.player, monster, self.player.stats.zone_level, battle_embed)

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
                    embed=create_battle_embed(interaction.user, self.player, monster,
                                              f"You have **DEFEATED** the {monster.name}!\n\n"
                                              f"You dealt **{battle_outcome[1]} damage** to the monster and took **{battle_outcome[2]} damage**. "
                                              f"You gained {experience_gained} combat XP.\n"
                                              f"\n"),
                    view=loot_view
                )

            else:

                button.disabled = True
                # The player is defeated
                self.player.stats.health = 0  # Set player's health to 0
                self.player_data[self.author_id]["stats"]["health"] = 0

                # Create a new embed with the defeat message
                new_embed = create_battle_embed(interaction.user, self.player, monster,

                                                f"☠️ You have been **DEFEATED** by the **{monster.name}**! 💀\n"
                                                f"{rip_emoji} *Your spirit lingers, seeking renewal.* {rip_emoji}\n\n"
                                                f"__**Options for Revival:**__\n"
                                                f"1. Use {mtrm_emoji} to revive without penalty.\n"
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

    @discord.ui.button(custom_id="stamina", style=discord.ButtonStyle.blurple, emoji=f'{potion_yellow_emoji}')
    async def stamina_potion(self, button, interaction):
        pass

class MiningCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def calculate_probability(player_level, zone_level, ore_type):
        base_min_levels = {
            "Iron": 1,
            "Coal": 7,
            "Carbon": 14
        }

        # Calculate the adjusted min level for the specific ore in the current zone
        ore_zone_min_level = base_min_levels[ore_type] + (zone_level - 1) * 20

        # Check if player's level is lower than ore's minimum level
        if player_level < ore_zone_min_level:
            return 0

        # Calculate the level difference
        level_difference = player_level - ore_zone_min_level

        # Determine the success probability
        # Starts at 25% and increases by 3.75% for each level difference until it reaches 100% in 20 levels
        probability = 0.25 + min(level_difference, 20) * 0.0375
        return min(1, probability)  # Ensure it doesn't exceed 100%

    @commands.slash_command(description="Mine some Ore!")
    async def mine(self, ctx,
                   ore_type: Option(str, "Type of tree to chop", choices=['Iron', 'Coal', 'Carbon'],
                                     required=True)):
        guild_id = ctx.guild.id
        author_id = str(ctx.author.id)
        player_data = load_player_data(guild_id)

        player = Exemplar(player_data[author_id]["exemplar"],
                          player_data[author_id]["stats"],
                          player_data[author_id]["inventory"])

        # Determine minimum level based on player's zone level
        base_min_level = {
            "Iron": 1,
            "Coal": 7,
            "Carbon": 14
        }

        ore_emoji = ORE_EMOJIS.get(ore_type, "🪨")  # Default to a rock emoji if no specific emoji is found.

        ore_min_level = base_min_level.get(ore_type) + (player.stats.zone_level - 1) * 20

        # Check if player meets the level requirement
        if player.stats.mining_level < ore_min_level:
            await ctx.respond(
                f"You need to be at least Mining Level {ore_min_level} to mine {ore_type} in this zone.",
                ephemeral=True)
            return

        # Start Embed
        embed = Embed(title=f"{ore_type} Ore")
        embed.set_image(url=generate_urls("ore", f'{ore_type}'))

        # Add the initial stamina and ore inventory here
        stamina_str = f"{potion_yellow_emoji}  {player.stats.endurance}/{player.stats.max_endurance}"

        # Use the get_tree_count method to get the wood count
        ore_count = player.inventory.get_ore_count(ore_type)
        ore_str = str(ore_count)

        # Add updated fields to embed
        embed.add_field(name="Endurance", value=stamina_str, inline=True)
        embed.add_field(name=ore_type, value=f"{ore_str} {ore_emoji}", inline=True)

        # Calculate current mining level and experience for the next level
        current_mining_level = player.stats.mining_level
        next_level = current_mining_level + 1
        current_experience = player.stats.mining_experience

        # Check if the player is at max level and add the XP field last
        if next_level >= 100:
            embed.add_field(name="Max Level", value=f"📊  {current_experience}", inline=True)
        else:
            next_level_experience_needed = LEVEL_DATA.get(str(current_mining_level), {}).get("total_experience")
            embed.add_field(name=f"XP to Level {next_level}",
                            value=f"📊  {current_experience} / {next_level_experience_needed}", inline=True)

        # Create the view and send the response
        view = MineButton(ctx, player, ore_type, player_data, guild_id, author_id, embed)

        await ctx.respond(embed=embed, view=view)

def setup(bot):
    bot.add_cog(MiningCog(bot))

