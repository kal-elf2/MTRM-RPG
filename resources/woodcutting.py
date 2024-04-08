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
from emojis import get_emoji
from utils import load_player_data, save_player_data, send_message, CommonResponses, refresh_player_from_data
from monsters.monster import create_battle_embed, monster_battle, generate_monster_by_name
from monsters.battle import BattleOptions, LootOptions, footer_text_for_embed
from images.urls import generate_urls
from probabilities import herb_drop_percent, mtrm_drop_percent, attack_percent, woodcleaver_percent

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

def attempt_mtrm_drop(zone_level):
    base_mtrm_drop_rate = mtrm_drop_percent
    mtrm_drop_rate = min(base_mtrm_drop_rate * zone_level, 1)  # Adjust the drop rate based on zone level and cap at 1

    if random.random() < mtrm_drop_rate:
        mtrm_dropped = Materium()
        return mtrm_dropped
    return None

def footer_text_for_woodcutting_embed(ctx, player, player_level, zone_level, tree_type):
    guild_id = ctx.guild.id
    author_id = str(ctx.user.id)
    player_data = load_player_data(guild_id, author_id)

    # Use the provided WoodcuttingCog method to calculate the success probability
    probability = WoodcuttingCog.calculate_probability(player, player_level, zone_level, tree_type)
    success_percentage = probability * 100  # Convert to percentage for display

    woodcutting_level = player_data["stats"]["woodcutting_level"]

    # Check if the player has the Woodcleaver charm equipped
    if player.inventory.equipped_charm and player.inventory.equipped_charm.name == "Woodcleaver":
        # Check if the success rate is already 100% before charm boost
        if success_percentage >= 100:
            footer_text = f"🪓 Woodcut Level:\u00A0\u00A0{woodcutting_level}\u00A0\u00A0|\u00A0\u00A0✅ Success Rate: 100% (Max)"
        else:
            adjusted_percentage = min(success_percentage + woodcleaver_percent * 100, 100)
            charm_boost = round(adjusted_percentage - success_percentage)
            footer_text = f"🪓 Woodcut Level:\u00A0\u00A0{woodcutting_level}\u00A0\u00A0|\u00A0\u00A0✅ Success Rate:\u00A0\u00A0{success_percentage:.1f}% (+{charm_boost}%)"
    else:
        footer_text = f"🪓 Woodcut Level:\u00A0\u00A0{woodcutting_level}\u00A0\u00A0|\u00A0\u00A0✅ Success Rate:\u00A0\u00A0{success_percentage:.1f}%"

    return footer_text

# View class for Harvest button
class HarvestButton(discord.ui.View, CommonResponses):
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

        # Initialize stamina potion buttons
        self.stamina_button = self.create_potion_button("Stamina Potion")
        self.super_stamina_button = self.create_potion_button("Super Stamina Potion")

        # Add buttons to the view
        self.add_item(self.stamina_button)
        self.add_item(self.super_stamina_button)

    def create_potion_button(self, potion_name):
        stack_count = self.player.get_potion_stack(potion_name)
        emoji_str = get_emoji(potion_name)
        emoji_id = int(emoji_str.split(':')[2].strip('>'))
        emoji = discord.PartialEmoji(name=potion_name, id=emoji_id)
        button_label = f" {stack_count:,}" if stack_count else ""
        button = discord.ui.Button(
            label=button_label,
            custom_id=potion_name.lower().replace(" ", "_"),
            style=discord.ButtonStyle.blurple,
            emoji=emoji,
            disabled=self.is_potion_disabled(potion_name)
        )
        button.callback = getattr(self, f"{potion_name.lower().replace(' ', '_')}_callback")
        return button

    def is_potion_disabled(self, potion_name):
        potion = next((item for item in self.player.inventory.potions if item.name == potion_name), None)
        return potion is None or potion.stack <= 0

    async def stamina_potion_callback(self, interaction):
        # Check authorization
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player object from the latest player data
        self.player, self.player_data = await refresh_player_from_data(interaction)

        await self.use_potion("Stamina Potion", interaction, self.stamina_button)

    async def super_stamina_potion_callback(self, interaction):
        # Check authorization
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player object from the latest player data
        self.player, self.player_data = await refresh_player_from_data(interaction)

        await self.use_potion("Super Stamina Potion", interaction, self.super_stamina_button)

    async def use_potion(self, potion_name, interaction, button):
        # Defer the interaction first
        await interaction.response.defer()

        # Use the potion and check if it was used successfully
        potion_used = self.use_potion_logic(self.player, potion_name)

        if potion_used:

            # Update player_data with the new stamina value
            self.player_data["stats"]["stamina"] = self.player.stats.stamina

            # Save any changes to player data
            save_player_data(self.guild_id, self.author_id, self.player_data)

            # Update the button label to show new stack count
            self.update_potion_button_label(button, potion_name)

            # Check if the potion is now disabled
            button.disabled = self.is_potion_disabled(potion_name)

            potion = next((p for p in self.player.inventory.potions if p.name == potion_name), None)
            emoji_str = get_emoji(potion_name)
            potion_message = f"{emoji_str} **{potion_name} restores {potion.effect_value} {potion.effect_stat}**"
            self.update_chop_messages(potion_message)

            # Update the embed with the new stamina value
            self.update_embed_stamina()

            # Edit the message with the updated embed and view
            await interaction.message.edit(embed=self.embed, view=self)

    @staticmethod
    def use_potion_logic(player, potion_name):
        potion = next((p for p in player.inventory.potions if p.name == potion_name), None)
        if potion and potion.stack > 0:
            # Apply the potion effect
            player.stats.stamina = min(player.stats.stamina + potion.effect_value, player.stats.max_stamina)

            # Decrement the potion stack
            potion.stack -= 1
            return True
        return False

    def update_potion_button_label(self, button, potion_name):
        stack_count = self.player.get_potion_stack(potion_name)
        button.label = f"{stack_count:,}" if stack_count else ""

    def refresh_button_states(self):
        # Iterate over potion buttons and update their state
        for button in [self.stamina_button, self.super_stamina_button]:
            potion_name = button.custom_id.replace("_", " ").title()
            button.disabled = self.is_potion_disabled(potion_name)

    def update_embed_stamina(self):
        # Find and update the embed field for stamina
        for field in self.embed.fields:
            if field.name == "Stamina":
                field.value = f"{get_emoji('stamina_emoji')} {self.player.stats.stamina}/{self.player.stats.max_stamina}"
                break
        else:
            # Add the stamina field if it's not found
            self.embed.add_field(name="Stamina",
                                 value=f"{get_emoji('stamina_emoji')} {self.player.stats.stamina}/{self.player.stats.max_stamina}",
                                 inline=True)

    def update_chop_messages(self, new_message):
        # Add the new message to the chop messages list
        if len(self.chop_messages) >= 5:
            self.chop_messages.pop(0)
        self.chop_messages.append(new_message)

        # Update the embed's description
        updated_description = "\n".join(self.chop_messages)
        self.embed.description = updated_description

    @discord.ui.button(label="Chop", custom_id="harvest", style=discord.ButtonStyle.blurple)
    async def harvest(self, button, interaction):
        # Check if the user who interacted is the same as the one who initiated the view
        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player object from the latest player data
        self.player, self.player_data = await refresh_player_from_data(interaction)

        # Check for battle flag and return if battling
        if self.player_data["location"] == "battle":
            await self.ongoing_battle_response(interaction)
            return

        # Update potion button labels to reflect the current inventory state (potions looted during battle)
        self.update_potion_button_label(self.stamina_button, "Stamina Potion")
        self.update_potion_button_label(self.super_stamina_button, "Super Stamina Potion")

        # Refresh the state of the potion buttons to enable/disable them as appropriate
        self.refresh_button_states()

        # Check if the player has space in the inventory or if the item is already in the inventory
        if self.player.inventory.total_items_count() >= self.player.inventory.limit and not self.player.inventory.has_item(
                self.tree_type):
            await interaction.response.send_message(f"Inventory is full. Please make some room before chopping {self.tree_type}.",
                                            ephemeral=True)
            # Re-enable the button after 2.5 seconds
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
            # Re-enable the button after 2.5 seconds
            await asyncio.sleep(2.5)
            button.disabled = False
            return

        selected_tree = next((tree for tree in TREE_TYPES if tree.name == self.tree_type), None)
        if not selected_tree:
            await interaction.followup.send(f"Invalid tree type selected.", ephemeral=True)
            return

        # Calculate probability using the zone level and the tree type
        success_prob = WoodcuttingCog.calculate_probability(self.player, player_level, self.player.stats.zone_level, self.tree_type)
        success = random.random() < success_prob

        zone_level = self.player.stats.zone_level
        current_level = self.player.stats.woodcutting_level

        # Define the maximum level for each zone
        zone_max_levels = {
            1: 20,
            2: 40,
            3: 60,
            4: 80,
        }

        # Determine the XP gain based on whether the player has reached the zone's level cap
        exp_gain = 0
        if zone_level in zone_max_levels:
            if current_level < zone_max_levels[zone_level]:
                exp_gain = WOODCUTTING_EXPERIENCE[self.tree_type]
        else:
            # If the player is in zone 5 or any zone without a defined max level, they can gain XP indefinitely
            exp_gain = WOODCUTTING_EXPERIENCE[self.tree_type]

        message = ""
        if success:
            tree_emoji = get_emoji(tree_emoji_mapping.get(self.tree_type, "🪵"))
            message = f"{tree_emoji} **Successfully chopped 1 {self.tree_type}!**"

            # Update inventory and decrement stamina
            chopped_tree = Tree(name=self.tree_type)
            self.player.inventory.add_item_to_inventory(chopped_tree, amount=1)
            self.player.stats.stamina -= 1

            # Gain woodcutting experience, passing 0 if the player has reached the cap
            messages = await self.player.gain_experience(exp_gain, "woodcutting", interaction)
            # Ensure messages is iterable if it's None
            messages = messages or []

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

            self.player_data["stats"][
                "woodcutting_experience"] = self.player.stats.woodcutting_experience
            self.player_data["stats"]["woodcutting_level"] = self.player.stats.woodcutting_level
            self.player_data["stats"]["stamina"] = self.player.stats.stamina
            self.player_data["stats"]["attack"] = self.player.stats.attack
            save_player_data(self.guild_id, self.author_id, self.player_data)

            # Clear previous fields and add new ones
            self.embed.clear_fields()
            stamina_str = f"{get_emoji('stamina_emoji')}  {self.player.stats.stamina}/{self.player.stats.max_stamina}"
            # Get the new wood count
            wood_count = self.player.inventory.get_item_quantity(self.tree_type)
            wood_str = "{:,}".format(wood_count)

            # Calculate current woodcutting level and experience for the next level
            current_woodcutting_level = self.player.stats.woodcutting_level
            next_level = current_woodcutting_level + 1
            current_experience = self.player.stats.woodcutting_experience

            # Add updated fields to embed
            self.embed.add_field(name="Stamina", value=stamina_str, inline=True)
            self.embed.add_field(name=f"{self.tree_type}", value=f"{tree_emoji}  {wood_str}", inline=True)

            # Check if the player is at max level and add the XP field last
            if next_level >= 100:
                formatted_current_experience = "{:,}".format(current_experience)
                self.embed.add_field(name="Max Level", value=f"📊  {formatted_current_experience}", inline=True)
            else:
                next_level_experience_needed = LEVEL_DATA.get(str(current_woodcutting_level), {}).get(
                    "total_experience")
                xp_remaining = next_level_experience_needed - current_experience
                formatted_xp_remaining = "{:,}".format(xp_remaining)
                self.embed.add_field(name=f"XP to Level {next_level}",
                                     value=f"📊 {formatted_xp_remaining}",
                                     inline=True)

            #Set footer to show Woodcutting level and Probability
            footer = footer_text_for_woodcutting_embed(interaction, self.player, current_woodcutting_level, zone_level,
                                                       self.tree_type)
            self.embed.set_footer(text=footer)

            # Update the chop messages list
            if len(self.chop_messages) >= 5:
                self.chop_messages.pop(0)
            self.chop_messages.append(message)

            # Prepare updated embed
            updated_description = "\n".join(self.chop_messages)
            self.embed.description = updated_description

            # Re-enable the button after 1.75 seconds
            await asyncio.sleep(1.75)
            button.disabled = False

            await interaction.message.edit(embed=self.embed, view=self)

            for msg_embed in messages:
                await interaction.followup.send(embed=msg_embed, ephemeral=False)

        else:
            message = f"You failed to chop {self.tree_type} wood."

            # Get the new wood count
            wood_count = self.player.inventory.get_item_quantity(self.tree_type)
            wood_str = "{:,}".format(wood_count)
            tree_emoji = get_emoji(tree_emoji_mapping.get(self.tree_type, "🪵"))

            # Clear previous fields and add updated stamina field
            self.embed.clear_fields()
            stamina_str = f"{get_emoji('stamina_emoji')}  {self.player.stats.stamina}/{self.player.stats.max_stamina}"
            self.embed.add_field(name="Stamina", value=stamina_str, inline=True)
            self.embed.add_field(name=f"{self.tree_type}", value=f"{tree_emoji}  {wood_str}", inline=True)

            # Calculate current woodcutting level and experience for the next level
            current_woodcutting_level = self.player.stats.woodcutting_level
            next_level = current_woodcutting_level + 1
            current_experience = self.player.stats.woodcutting_experience

            # Check if the player is at max level and add the XP field last
            if next_level >= 100:
                formatted_current_experience = "{:,}".format(current_experience)
                self.embed.add_field(name="Max Level", value=f"📊  {formatted_current_experience}", inline=True)
            else:
                next_level_experience_needed = LEVEL_DATA.get(str(current_woodcutting_level), {}).get(
                    "total_experience")
                xp_remaining = next_level_experience_needed - current_experience
                formatted_xp_remaining = "{:,}".format(xp_remaining)
                self.embed.add_field(name=f"XP to Level {next_level}",
                                     value=f"📊 {formatted_xp_remaining}",
                                     inline=True)

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

            footer = footer_text_for_woodcutting_embed(interaction, self.player, current_woodcutting_level, zone_level,
                                                       self.tree_type)
            self.embed.set_footer(text=footer)

            await interaction.message.edit(embed=self.embed, view=self)

        # Monster encounter set in probabilities.py
        if np.random.rand() <= attack_percent and self.player_data["location"] != "battle":

            # Refresh player object from the latest player data
            self.player, self.player_data = await refresh_player_from_data(interaction)

            self.player_data["location"] = "battle"
            save_player_data(self.guild_id, self.author_id, self.player_data)

            monster_name = generate_random_monster(self.tree_type)
            monster = generate_monster_by_name(monster_name, self.player.stats.zone_level)

            # Send the warning message in the channel mentioning the user
            warning_message = f"LOOK OUT {interaction.user.mention}!"
            await interaction.followup.send(warning_message)

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
                view=BattleOptions(self.ctx, self.player, self.player_data, battle_context, special_attack_options_view))
            battle_context.battle_options_msg = battle_options_msg

            special_attack_options_view.battle_options_msg = battle_options_msg
            special_attack_options_view.special_attack_message = special_attack_message

            battle_result = await monster_battle(battle_context)

            if battle_result is None:
                # Save the player's current stats
                self.player_data["stats"].update(self.player.stats.__dict__)
                save_player_data(self.guild_id, self.author_id, self.player_data)

            else:
                # Unpack the battle outcome and loot messages
                battle_outcome, loot_messages = battle_result
                if battle_outcome[0]:

                    # Check if the player is at or above the level cap for their current zone
                    if zone_level in zone_max_levels and self.player.stats.combat_level >= zone_max_levels[zone_level]:
                        # Player is at or has exceeded the level cap for their zone; set XP gain to 0
                        experience_gained = 0
                    else:
                        # Player is below the level cap; award XP from the monster
                        experience_gained = monster.experience_reward

                    loothaven_effect = battle_outcome[5]  # Get the Loothaven effect status
                    messages = await self.player.gain_experience(experience_gained, 'combat', interaction, self.player)
                    # Ensure messages is iterable if it's None
                    messages = messages or []
                    for msg_embed in messages:
                        await interaction.followup.send(embed=msg_embed, ephemeral=False)

                    self.player_data["stats"]["stamina"] = self.player.stats.stamina
                    self.player_data["stats"]["combat_level"] = self.player.stats.combat_level
                    self.player_data["stats"]["combat_experience"] = self.player.stats.combat_experience
                    self.player.stats.damage_taken = 0
                    self.player_data["stats"].update(self.player.stats.__dict__)

                    if self.player.stats.health <= 0:
                        self.player.stats.health = self.player.stats.max_health

                    # Increment the count of the defeated monster
                    self.player_data["monster_kills"][monster.name] += 1

                    # Save the player data after common actions
                    save_player_data(self.guild_id, self.author_id, self.player_data)

                    # Clear the previous views
                    await battle_context.special_attack_message.delete()
                    await battle_options_msg.delete()

                    loot_view = LootOptions(interaction, self.player, monster, battle_embed, self.player_data, self.author_id, battle_outcome,
                                            loot_messages, self.guild_id, interaction, experience_gained, loothaven_effect, battle_context.rusty_spork_dropped, add_repeat_button=False)

                    # Send max XP cap message if experience gained is 0
                    max_cap_message = ""
                    if experience_gained == 0:
                        max_cap_message = f"\n**(Max XP cap reached for Zone {self.player.stats.zone_level})**"

                    await battle_embed.edit(
                        embed=create_battle_embed(interaction.user, self.player, monster, footer_text_for_embed(self.ctx, monster, self.player),
                                                  f"You have **DEFEATED** the {monster.name}!\n\n"
                                                  f"You dealt **{battle_outcome[1]} damage** to the monster and took **{battle_outcome[2]} damage**. "
                                                  f"You gained {experience_gained} combat XP. {max_cap_message}\n"
                                                  f"\n"),
                        view=loot_view
                    )

                else:
                    # The player is defeated
                    self.player.stats.health = 0  # Set player's health to 0
                    self.player_data["stats"]["health"] = 0

                    # Create a new embed with the defeat message
                    new_embed = create_battle_embed(interaction.user, self.player, monster, footer_text= "", messages=

                                                    f"☠️ You have been **DEFEATED** by the **{monster.name}**!\n"
                                                    f"{get_emoji('rip_emoji')} *Your spirit lingers, seeking renewal.* {get_emoji('rip_emoji')}\n\n"
                                                    f"__**Options for Revival:**__\n"
                                                    f"1. Use {get_emoji('Materium')} to revive without penalty.\n"
                                                    f"2. Resurrect with 2.5% penalty to all skills."
                                                    f"**Lose all items in inventory** (Keep equipped items, coppers, MTRM, potions, and charms)")

                    # Clear the previous views
                    await battle_context.special_attack_message.delete()
                    await battle_options_msg.delete()

                    # Add the "dead.png" image to the embed
                    new_embed.set_image(
                        url=generate_urls("cemetery", "dead"))
                    # Update the message with the new embed and view
                    await battle_embed.edit(embed=new_embed, view=ResurrectOptions(interaction, self.player_data, self.author_id))

            # Clear the battle flag after the battle ends
            self.player_data["location"] = None
            save_player_data(self.guild_id, self.author_id, self.player_data)

class WoodcuttingCog(commands.Cog, CommonResponses):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def calculate_probability(player, player_level, zone_level, tree_type):
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

        # Check if the player has the Stonebreaker charm equipped
        if player.inventory.equipped_charm and player.inventory.equipped_charm.name == "Woodcleaver":
            probability += woodcleaver_percent  # Increase probability by if Woodcleaver is equipped

        return min(1, probability)  # Ensure it doesn't exceed 100%

    @commands.slash_command(description="Chop some wood!")
    async def chop(self, ctx,
                   tree_type: Option(str, "Type of tree to chop", choices=['Pine', 'Yew', 'Ash', 'Poplar'],
                                     required=True)):

        # Refresh player object from the latest player data
        player, player_data = await refresh_player_from_data(ctx)


        # Check if player data exists for the user
        if not player_data:
            embed = Embed(title="Captain Ner0",
                          description="Arr! What be this? No record of yer adventures? Start a new game with `/newgame` before I make ye walk the plank.",
                          color=discord.Color.dark_gold())
            embed.set_thumbnail(url=generate_urls("nero", "confused"))
            await ctx.respond(embed=embed, ephemeral=True)
            return

        # Check the player's health before starting a battle
        if player.stats.health <= 0:
            embed = Embed(title="Captain Ner0",
                          description="Ahoy! Ye can't do that ye bloody ghost! Ye must travel to the 🪦 `/cemetery` to reenter the realm of the living.",
                          color=discord.Color.dark_gold())
            embed.set_thumbnail(url=generate_urls("nero", "confused"))
            await ctx.respond(embed=embed, ephemeral=True)
            return

        # Check for battle flag and return if battling
        if player_data["location"] == "citadel":
            await self.exit_citadel_response(ctx)
            return

        if player_data["location"] == "kraken" or player_data["location"] == "kraken_battle":
            await CommonResponses.during_kraken_battle_response(ctx)
            return

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
        wood_str = "{:,}".format(wood_count)

        # Add the initial fields to the embed
        embed.add_field(name="Stamina", value=stamina_str, inline=True)
        embed.add_field(name=f"{tree_type}", value=f"{tree_emoji}  {wood_str}", inline=True)

        # Calculate current woodcutting level and experience for the next level
        current_woodcutting_level = player.stats.woodcutting_level
        next_level = current_woodcutting_level + 1
        current_experience = player.stats.woodcutting_experience

        # Check if the player is at max level and add the XP field last
        if next_level >= 100:
            formatted_current_experience = "{:,}".format(current_experience)
            embed.add_field(name="Max Level", value=f"📊  {formatted_current_experience}", inline=True)
        else:
            next_level_experience_needed = LEVEL_DATA.get(str(current_woodcutting_level), {}).get("total_experience")
            xp_remaining = next_level_experience_needed - current_experience
            formatted_xp_remaining = "{:,}".format(xp_remaining)
            embed.add_field(name=f"XP to Level {next_level}",
                            value=f"📊 {formatted_xp_remaining}",
                            inline=True)

        # Set footer to show Woodcutting level and Probability
        footer = footer_text_for_woodcutting_embed(ctx, player, current_woodcutting_level, player.stats.zone_level,
                                                   tree_type)
        embed.set_footer(text=footer)

        # Create the view and send the response
        view = HarvestButton(ctx, player, tree_type, player_data, ctx.guild_id, str(ctx.author.id), embed)

        await ctx.respond(embed=embed, view=view)


def setup(bot):
    bot.add_cog(WoodcuttingCog(bot))

