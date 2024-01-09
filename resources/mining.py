import random
from discord import Embed
import asyncio
import discord
import json
import numpy as np
from discord.ext import commands
from discord.commands import Option
from resources.ore import ORE_TYPES, Ore
from resources.herb import HERB_TYPES
from resources.materium import Materium
from stats import ResurrectOptions
from exemplars.exemplars import Exemplar
from utils import load_player_data, save_player_data, send_message
from monsters.monster import create_battle_embed, monster_battle, generate_monster_by_name, footer_text_for_embed
from monsters.battle import BattleOptions, LootOptions
from images.urls import generate_urls
from emojis import get_emoji
from probabilities import herb_drop_percent, mtrm_drop_percent, attack_percent, stonebreaker_percent

# Mining experience points for each ore type
MINING_EXPERIENCE = {
    "Iron Ore": 20,
    "Coal": 25,
    "Carbon": 50
}

ore_emoji_mapping = {
    "Coal": 'coal_emoji',
    "Carbon": 'carbon_emoji',
    "Iron Ore": 'iron_emoji'
}

with open("level_data.json", "r") as f:
    LEVEL_DATA = json.load(f)

def generate_random_monster(ore_type):
    monster_chances = {}
    if ore_type == "Iron Ore":
        monster_chances = {'Buck': 0.25, 'Wolf': 0.75}
    elif ore_type == "Coal":
        monster_chances = {'Buck': 0.1, 'Wolf': 0.3, 'Goblin': 0.6}
    elif ore_type == "Carbon":
        monster_chances = {'Goblin': 0.6, 'Goblin Hunter': 0.2, 'Mega Brute': 0.15, 'Wisp': 0.05}

    monsters = list(monster_chances.keys())
    probabilities = list(monster_chances.values())

    return np.random.choice(monsters, p=probabilities)

def attempt_herb_drop(zone_level):
    if random.random() < herb_drop_percent:
        # Base weights
        weights = [40, 40, 10, 10]

        # Increase the weights of the last two herbs based on zone_level
        increase_per_zone = 5
        weights[2] += (zone_level - 1) * increase_per_zone
        weights[3] += (zone_level - 1) * increase_per_zone

        # Decrease the weights of the first two herbs to maintain total weight
        total_increase = (zone_level - 1) * 2 * increase_per_zone
        weights[0] -= total_increase // 2
        weights[1] -= total_increase // 2

        herb_dropped = random.choices(HERB_TYPES, weights=weights, k=1)[0]
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

def footer_text_for_mining_embed(ctx, player, player_level, zone_level, ore_type):
    guild_id = ctx.guild.id
    author_id = str(ctx.user.id)
    player_data = load_player_data(guild_id)

    # Use the provided MiningCog method to calculate the success probability
    probability = MiningCog.calculate_probability(player, player_level, zone_level, ore_type)
    success_percentage = probability * 100  # Convert to percentage for display

    mining_level = player_data[author_id]["stats"]["mining_level"]

    # Check if the player has the Stonebreaker charm equipped
    if player.inventory.equipped_charm and player.inventory.equipped_charm.name == "Stonebreaker":
        # Check if the success rate is already 100% before charm boost
        if success_percentage >= 100:
            footer_text = f"⛏️ Mining Level:\u00A0\u00A0{mining_level}\u00A0\u00A0\u00A0\u00A0|\u00A0\u00A0\u00A0\u00A0✅ Success Rate: 100% (Max)"
        else:
            adjusted_percentage = min(success_percentage + stonebreaker_percent * 100, 100)
            charm_boost = round(adjusted_percentage - success_percentage)
            footer_text = f"⛏️ Mining Level:\u00A0\u00A0{mining_level}\u00A0\u00A0\u00A0\u00A0|\u00A0\u00A0\u00A0\u00A0✅ Success Rate:\u00A0\u00A0{success_percentage:.1f}% (+{charm_boost}%)"
    else:
        footer_text = f"⛏️ Mining Level:\u00A0\u00A0{mining_level}\u00A0\u00A0\u00A0\u00A0|\u00A0\u00A0\u00A0\u00A0✅ Success Rate:\u00A0\u00A0{success_percentage:.1f}%"

    return footer_text




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

        # Check if the player has space in the inventory or if the item is already in the inventory
        if self.player.inventory.total_items_count() >= self.player.inventory.limit and not self.player.inventory.has_item(
                self.ore_type):
            await interaction.response.send_message(
                f"Inventory is full. Please make some room before mining {self.ore_type}.",
                ephemeral=True)
            # Re-enable the button after 2.5 seconds
            await asyncio.sleep(2.5)
            button.disabled = False
            return

        # Disable the button immediately
        button.disabled = True
        await interaction.response.edit_message(embed=self.embed, view=self)

        stamina = self.player.stats.stamina
        player_level = self.player.stats.mining_level

        if stamina <= 0:
            await interaction.followup.send("You are too tired to mine any ore.", ephemeral=True)
            # Re-enable the button after 2.5 seconds
            await asyncio.sleep(2.5)
            button.disabled = False
            return

        selected_ore = next((ore for ore in ORE_TYPES if ore.name == self.ore_type), None)
        if not selected_ore:
            await interaction.followup.send(f"Invalid ore type selected.", ephemeral=True)
            return

        success_prob = MiningCog.calculate_probability(self.player, player_level, self.player.stats.zone_level, self.ore_type)

        success = random.random() < success_prob

        zone_level = self.player.stats.zone_level

        message = ""
        if success:
            ore_emoji = get_emoji(ore_emoji_mapping.get(self.ore_type, "🪨"))
            message = f"{ore_emoji} **Successfully mined 1 {self.ore_type}!**"

            # Update inventory and decrement stamina
            mined_ore = Ore(name=self.ore_type)
            self.player.inventory.add_item_to_inventory(mined_ore, amount=1)
            self.player.stats.stamina -= 1

            # Gain mining experience
            exp_gain = MINING_EXPERIENCE[self.ore_type]
            level_up_message = await self.player.gain_experience(exp_gain, "mining", interaction)

            # Attempt herb drop
            herb_dropped = attempt_herb_drop(zone_level)
            if herb_dropped:
                self.player.inventory.add_item_to_inventory(herb_dropped, amount=1)
                message += f"\n{get_emoji(herb_dropped.name)} You also **found some {herb_dropped.name}!**"

            # Attempt MTRM drop
            mtrm_dropped = attempt_mtrm_drop(zone_level)
            if mtrm_dropped:
                self.player.inventory.add_item_to_inventory(mtrm_dropped, amount=1)
                message += f"\n{get_emoji('Materium')} You also **found some Materium!**"

            self.player_data[self.author_id]["stats"][
                "mining_experience"] = self.player.stats.mining_experience
            self.player_data[self.author_id]["stats"]["mining_level"] = self.player.stats.mining_level
            self.player_data[self.author_id]["stats"]["stamina"] = self.player.stats.stamina
            save_player_data(self.guild_id, self.player_data)

            # Clear previous fields and add new ones
            self.embed.clear_fields()
            stamina_str = f"{get_emoji('stamina_emoji')}  {self.player.stats.stamina}/{self.player.stats.max_stamina}"
            # Get the new ore count
            ore_count = self.player.inventory.get_item_quantity(self.ore_type)
            ore_str = str(ore_count)

            # Calculate current mining level and experience for the next level
            current_mining_level = self.player.stats.mining_level
            next_level = current_mining_level + 1
            current_experience = self.player.stats.mining_experience

            # Add updated fields to embed
            self.embed.add_field(name="Stamina", value=stamina_str, inline=True)
            self.embed.add_field(name=f"{self.ore_type}", value=f"{ore_str} {ore_emoji}", inline=True)

            # Check if the player is at max level and add the XP field last
            if next_level >= 100:
                self.embed.add_field(name="Max Level", value=f"📊  {current_experience}", inline=True)
            else:
                next_level_experience_needed = LEVEL_DATA.get(str(current_mining_level), {}).get(
                    "total_experience")
                self.embed.add_field(name=f"XP to Level {next_level}",
                                     value=f"📊  {current_experience} / {next_level_experience_needed}", inline=True)

            # Set footer to show Woodcutting level and Probability
            footer = footer_text_for_mining_embed(interaction, self.player, current_mining_level, zone_level,
                                                       self.ore_type)
            self.embed.set_footer(text=footer)

            # Update the mine messages list
            if len(self.mine_messages) >= 5:
                self.mine_messages.pop(0)
            self.mine_messages.append(message)

            # Prepare updated embed
            updated_description = "\n".join(self.mine_messages)
            self.embed.description = updated_description

            # Re-enable the button after 1.75 seconds
            await asyncio.sleep(1.75)
            button.disabled = False

            await interaction.message.edit(embed=self.embed, view=self)

            if level_up_message:
                self.player_data[self.author_id]["stats"]["strength"] = self.player.stats.strength + (
                        self.player.stats.mining_level - 1)
                save_player_data(self.guild_id, self.player_data)

                await interaction.followup.send(embed=level_up_message)

        else:
            message = f"You failed to mine {self.ore_type} ore."

            # Calculate current woodcutting level and experience for the next level
            current_mining_level = self.player.stats.mining_level

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

            # Set footer to show Woodcutting level and Probability
            footer = footer_text_for_mining_embed(interaction, self.player, current_mining_level, zone_level,
                                                  self.ore_type)
            self.embed.set_footer(text=footer)

            await interaction.message.edit(embed=self.embed, view=self)

        # Monster encounter set in probabilities.py
        if np.random.rand() <= attack_percent and not self.player_data[self.author_id]["in_battle"]:
            self.player_data[self.author_id]["in_battle"] = True
            save_player_data(self.guild_id, self.player_data)

            monster_name = generate_random_monster(self.ore_type)
            monster = generate_monster_by_name(monster_name, self.player.stats.zone_level)

            battle_embed = await send_message(interaction.channel,
                                              create_battle_embed(interaction.user, self.player, monster,
                                                                  footer_text_for_embed(self.ctx, monster, self.player)))

            from monsters.monster import BattleContext
            from monsters.battle import SpecialAttackOptions

            def update_special_attack_buttons(context):
                if context.special_attack_options_view:
                    context.special_attack_options_view.update_button_states()

            battle_context = BattleContext(self.ctx, interaction.user, self.player, monster, battle_embed,
                                           self.player.stats.zone_level,
                                           update_special_attack_buttons)

            special_attack_options_view = SpecialAttackOptions(battle_context, None, None)
            battle_context.special_attack_options_view = special_attack_options_view

            special_attack_message = await self.ctx.send(view=special_attack_options_view)
            battle_context.special_attack_message = special_attack_message

            battle_options_msg = await self.ctx.send(
                view=BattleOptions(self.ctx, self.player, battle_context, special_attack_options_view))
            battle_context.battle_options_msg = battle_options_msg

            special_attack_options_view.battle_options_msg = battle_options_msg
            special_attack_options_view.special_attack_message = special_attack_message

            battle_result = await monster_battle(battle_context)

            if battle_result is None:
                # Save the player's current stats
                self.player_data[self.author_id]["stats"].update(self.player.stats.__dict__)
                save_player_data(self.guild_id, self.player_data)

            else:
                # Unpack the battle outcome and loot messages
                battle_outcome, loot_messages = battle_result
                if battle_outcome[0]:

                    experience_gained = monster.experience_reward
                    loothaven_effect = battle_outcome[5]  # Get the Loothaven effect status
                    await self.player.gain_experience(experience_gained, 'combat', interaction)
                    self.player_data[self.author_id]["stats"]["stamina"] = self.player.stats.stamina
                    self.player_data[self.author_id]["stats"]["combat_level"] = self.player.stats.combat_level
                    self.player_data[self.author_id]["stats"]["combat_experience"] = self.player.stats.combat_experience
                    self.player.stats.damage_taken = 0
                    self.player_data[self.author_id]["stats"].update(self.player.stats.__dict__)

                    if self.player.stats.health <= 0:
                        self.player.stats.health = self.player.stats.max_health

                    # Save the player data after common actions
                    save_player_data(self.guild_id, self.player_data)

                    # Clear the previous views
                    await battle_context.special_attack_message.delete()
                    await battle_options_msg.delete()

                    loot_view = LootOptions(interaction, self.player, monster, battle_embed, self.player_data, self.author_id, battle_outcome,
                                            loot_messages, self.guild_id, interaction, experience_gained, loothaven_effect)

                    await battle_embed.edit(
                        embed=create_battle_embed(interaction.user, self.player, monster, footer_text_for_embed(self.ctx, monster, self.player),
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
                    new_embed = create_battle_embed(interaction.user, self.player, monster, footer_text= "", messages=

                                                    f"☠️ You have been **DEFEATED** by the **{monster.name}**!\n"
                                                    f"{get_emoji('rip_emoji')} *Your spirit lingers, seeking renewal.* {get_emoji('rip_emoji')}\n\n"
                                                    f"__**Options for Revival:**__\n"
                                                    f"1. Use {get_emoji('Materium')} to revive without penalty.\n"
                                                    f"2. Resurrect with 2.5% penalty to all skills."
                                                    f"**Lose all items in inventory** (Keep coppers, MTRM, potions, and charms)")

                    # Clear the previous views
                    await battle_context.special_attack_message.delete()
                    await battle_options_msg.delete()

                    # Add the "dead.png" image to the embed
                    new_embed.set_image(
                        url=generate_urls("cemetery", "dead"))
                    # Update the message with the new embed and view
                    await battle_embed.edit(embed=new_embed, view=ResurrectOptions(interaction, self.player_data, self.author_id))

            # Clear the in_battle flag after the battle ends
            self.player_data[self.author_id]["in_battle"] = False
            save_player_data(self.guild_id, self.player_data)

    @discord.ui.button(custom_id="stamina", style=discord.ButtonStyle.blurple, emoji=f'{get_emoji("Stamina Potion")}')
    async def stamina_potion(self, button, interaction):
        pass

    @discord.ui.button(custom_id="super_stamina", style=discord.ButtonStyle.blurple, emoji=f'{get_emoji("Super Stamina Potion")}')
    async def super_stamina_potion(self, button, interaction):
        pass

class MiningCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def calculate_probability(player, player_level, zone_level, ore_type):
        base_min_levels = {
            "Iron Ore": 0,
            "Coal": 7,
            "Carbon": 14
        }

        # Calculate the adjusted min level for the specific ore in the current zone
        ore_zone_min_level = base_min_levels[ore_type] + (zone_level - 1) * 20

        # Check if player's level is lower than ore's minimum level
        if player_level < ore_zone_min_level:
            return 0

        # Calculate the level difference
        level_difference = min(player_level - ore_zone_min_level, 20)

        # Determine the success probability
        probability = 0.25 + level_difference * 0.0375

        # Check if the player has the Stonebreaker charm equipped
        if player.inventory.equipped_charm and player.inventory.equipped_charm.name == "Stonebreaker":
            probability += stonebreaker_percent  # Increase probability by if Stonebreaker is equipped

        return min(1, probability)  # Ensure it doesn't exceed 100%

    @commands.slash_command(description="Mine some Ore!")
    async def mine(self, ctx,
                   ore_type: Option(str, "Type of ore to mine", choices=['Iron Ore', 'Coal', 'Carbon'],
                                     required=True)):
        guild_id = ctx.guild.id
        author_id = str(ctx.author.id)
        player_data = load_player_data(guild_id)

        # Check if player data exists for the user
        if author_id not in player_data:
            embed = Embed(title="Captain Ner0",
                          description="Arr! What be this? No record of yer adventures? Start a new game with `/newgame` before I make ye walk the plank.",
                          color=discord.Color.dark_gold())
            embed.set_thumbnail(url=generate_urls("nero", "confused"))
            await ctx.respond(embed=embed, ephemeral=True)
            return

        player = Exemplar(player_data[author_id]["exemplar"],
                          player_data[author_id]["stats"],
                          player_data[author_id]["inventory"])

        # Check the player's health before starting a battle
        if player.stats.health <= 0:
            embed = Embed(title="Captain Ner0",
                          description="Ahoy! Ye can't do that ye bloody ghost! Ye must travel to the 🪦 `/cemetery` to reenter the realm of the living.",
                          color=discord.Color.dark_gold())
            embed.set_thumbnail(url=generate_urls("nero", "confused"))
            await ctx.respond(embed=embed, ephemeral=True)
            return

        base_min_levels = {
            "Iron Ore": 0,
            "Coal": 7,
            "Carbon": 14
        }

        ore_min_level = base_min_levels[ore_type] + (player.stats.zone_level - 1) * 20

        ore_emoji = get_emoji(ore_emoji_mapping.get(ore_type, "🪨"))  # Default to empty string if not found

        # Check if player meets the level requirement
        if player.stats.mining_level < ore_min_level:
            await ctx.respond(
                f"You need to be at least Mining Level {ore_min_level} to mine {ore_type} in this zone.",
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
        embed = Embed(title=f"{rarity} {ore_type}", color=embed_color)
        embed.set_image(url=generate_urls("ore", f'{ore_type}'))

        # Add the initial stamina and ore inventory here
        stamina_str = f"{get_emoji('stamina_emoji')}  {player.stats.stamina}/{player.stats.max_stamina}"

        # Use the get_ore_count method to get the wood count
        ore_count = player.inventory.get_item_quantity(ore_type)
        ore_str = str(ore_count)

        # Add updated fields to embed
        embed.add_field(name="Stamina", value=stamina_str, inline=True)
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

        # Set footer to show Woodcutting level and Probability
        footer = footer_text_for_mining_embed(ctx, player, current_mining_level, player.stats.zone_level, ore_type)
        embed.set_footer(text=footer)

        # Create the view and send the response
        view = MineButton(ctx, player, ore_type, player_data, guild_id, author_id, embed)

        await ctx.respond(embed=embed, view=view)

def setup(bot):
    bot.add_cog(MiningCog(bot))

