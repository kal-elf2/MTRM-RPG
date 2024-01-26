import json
import math
import discord
from discord.ext import commands
from utils import load_player_data, save_player_data, CommonResponses
from exemplars.exemplars import Exemplar
from emojis import get_emoji
from images.urls import generate_urls
import copy
from probabilities import buyback_cost
import asyncio

def load_level_data():
    with open('level_data.json', 'r') as f:
        return json.load(f)

def experience_needed_to_next_level(current_level, current_exp, level_data):
    if str(current_level) in level_data:
        return level_data[str(current_level)]['total_experience'] - current_exp
    return None

def create_progress_bar(current_exp, current_level, level_data):
    bar_length = 16  # Fixed bar length
    current_level_str = str(current_level)
    next_level_str = str(int(current_level) + 1)

    if next_level_str not in level_data:
        return "Max Level Reached", "N/A"

    exp_needed_this_level = level_data[current_level_str]['experience_needed']
    exp_needed_to_next_level = experience_needed_to_next_level(current_level, current_exp, level_data)

    # Calculate experience earned since the last level
    exp_earned_this_level = exp_needed_this_level - exp_needed_to_next_level

    # Calculate progress as the ratio of exp_earned_this_level to exp_needed_this_level
    progress = exp_earned_this_level / exp_needed_this_level

    # Calculate the number of filled and empty symbols needed
    filled_length = round(bar_length * progress)
    filled_symbols = '◼' * filled_length
    empty_symbols = '◻' * (bar_length - filled_length)

    progress_percentage = round(progress * 100)
    return filled_symbols + empty_symbols, progress_percentage

class StatsView(discord.ui.View):
    def __init__(self, author_id, zone_level):
        super().__init__()
        self.add_item(StatsDropdown(author_id, zone_level))

# Colors for each zone
color_mapping = {
    1: 0x969696,
    2: 0x15ce00,
    3: 0x0096f1,
    4: 0x9900ff,
    5: 0xfebd0d
}

class StatsDropdown(discord.ui.Select, CommonResponses):
    def __init__(self, author_id, zone_level):
        self.author_id = author_id
        self.zone_level = zone_level
        options = [
            discord.SelectOption(label="Level Progress"),
            discord.SelectOption(label="Three Eyed Snake"),
            discord.SelectOption(label="Monster Kills")
        ]
        super().__init__(placeholder="Choose a category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        from exemplars.exemplars import DiceStats, MonsterKills

        # Authorization check
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        author_id = str(interaction.user.id)
        player_data = load_player_data(interaction.guild.id)

        if self.values[0] == "Level Progress":
            # Send combined level progress information
            embed = self.create_level_progress_embed(player_data[author_id]["stats"], self.zone_level)
            await interaction.response.send_message(embed=embed, ephemeral=False)

        elif self.values[0] == "Three Eyed Snake":
            # Send Three Eyed Snake stats
            dice_stats = DiceStats.from_dict(player_data[author_id]["dice_stats"])
            embed = self.create_three_eyed_snake_embed(dice_stats, self.zone_level)
            await interaction.response.send_message(embed=embed, ephemeral=False)

        elif self.values[0] == "Monster Kills":
            # Send Monster Kills stats
            monster_kills = MonsterKills.from_dict(player_data[author_id]["monster_kills"])
            embed = self.create_monster_kills_embed(monster_kills, self.zone_level)
            await interaction.response.send_message(embed=embed, ephemeral=False)

    @staticmethod
    def create_level_progress_embed(stats, zone_level):
        level_data = load_level_data()
        embed_color = color_mapping.get(zone_level, 0x969696)  # Default color if zone level is not found
        embed = discord.Embed(title="📈 Level Progress 📈", color=embed_color)

        # Define emojis for each skill
        skill_emojis = {
            "combat": "⚔️",
            "mining": "⛏️",
            "woodcutting": "🪓"
        }

        # Loop through each skill and add its progress to the embed
        for skill in ['combat', 'mining', 'woodcutting']:
            emoji = skill_emojis.get(skill, "")
            skill_capitalized = skill.capitalize()
            level = stats[f'{skill}_level']
            current_exp = stats[f'{skill}_experience']

            next_level = int(level) + 1
            exp_needed = experience_needed_to_next_level(level, current_exp, level_data)
            progress_bar, progress_percentage = create_progress_bar(current_exp, level, level_data)

            embed.add_field(name=f"{emoji} {skill_capitalized} Level ", value=str(level), inline=True)
            embed.add_field(name=f"XP to Level {next_level}", value=str(exp_needed), inline=True)
            embed.add_field(name=f"Progress: **{progress_percentage}%**\n{progress_bar}", value="\u200B", inline=False)


        return embed

    @staticmethod
    def create_three_eyed_snake_embed(dice_stats, zone_level):
        stats_info = (f"#️⃣ Total Games: {dice_stats.total_games}\n"
                      f"🏆 Games Won: {dice_stats.games_won}\n"
                      f"💸 Games Lost: {dice_stats.games_lost}\n"
                      f"{get_emoji('coppers_emoji')} Coppers Won: {dice_stats.coppers_won:,}")

        embed_color = color_mapping.get(zone_level, 0x969696)
        embed = discord.Embed(title="🎲 Three Eyed Snake Stats 🎲", color=embed_color)
        embed.add_field(name=stats_info, value="\u200B", inline=False)
        embed.set_thumbnail(url=generate_urls("nero", "dice"))

        return embed

    @staticmethod
    def create_monster_kills_embed(monster_kills, zone_level):
        kills_info = "\n".join([f"{monster}: {count}" for monster, count in monster_kills.monster_kills.items()])

        # Find the monster with the highest kill count
        most_killed_monster = max(monster_kills.monster_kills.items(), key=lambda x: x[1])[0]

        embed_color = color_mapping.get(zone_level, 0x969696)
        embed = discord.Embed(
            title=f"{get_emoji('goblin_crown_emoji')} Monster Kills {get_emoji('goblin_crown_emoji')}",
            color=embed_color)
        embed.add_field(name=kills_info, value="\u200B", inline=False)
        embed.set_thumbnail(url=generate_urls("monsters", most_killed_monster))

        return embed

class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="View your stats")
    async def stats(self, ctx):
        guild_id = ctx.guild.id
        author_id = str(ctx.author.id)

        player_data = load_player_data(guild_id)
        player = player_data[author_id]["stats"]
        zone_level = player_data[author_id]["stats"]["zone_level"]
        exemplar = player_data[author_id]['exemplar']
        exemplar_capitalized = exemplar.capitalize()

        embed_color = color_mapping.get(zone_level, 0x969696)
        embed = discord.Embed(color=embed_color)
        embed.set_thumbnail(url=generate_urls("exemplars", exemplar_capitalized))

        weapon_specialty = {
                        "human": "Sword",
                        "elf": "Bow",
                        "orc": "Spear",
                        "dwarf": "Hammer",
                        "halfling": "Sword"
                    }

        # Add overall stats to the embed
        all_stats = f"""**Exemplar**: {str(player_data[author_id]['exemplar']).capitalize()}\n
                    ⚔️ **Combat Level**: {str(player['combat_level'])}
                    {get_emoji('heart_emoji')} **Health**: {str(player['health'])}
                    {get_emoji('strength_emoji')} **Strength**: {str(player['strength'])}
                    {get_emoji('stamina_emoji')}️ **Stamina**: {str(player['stamina'])}
                    🗡️ **Attack**: {str(player['attack'])}
                    🛡️ **Defense**: {str(player['defense'])}
                    ⛏️ **Mining Level**: {str(player['mining_level'])}
                    🪓 **Woodcutting Level**: {str(player['woodcutting_level'])}"""
        embed.add_field(name="Overall Stats", value=all_stats, inline=False)
        specialty = weapon_specialty.get(exemplar)
        embed.set_footer(text=f"Weapon Bonus: {specialty}")

        # Send the embed with overall stats
        await ctx.respond(content=f"{ctx.author.mention}'s Overall Stats", embed=embed)

        # Send the dropdown view for additional stats
        view = StatsView(author_id=str(ctx.author.id), zone_level=zone_level)
        await ctx.send("Select a category to view more details:", view=view)

class ResurrectOptions(discord.ui.View, CommonResponses):
    def __init__(self, interaction, player_data, author_id, include_nero=True):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.player_data = player_data
        self.author_id = author_id
        self.include_nero = include_nero

        self.player = Exemplar(player_data[author_id]["exemplar"],
                               player_data[author_id]["stats"],
                               player_data[author_id]["inventory"])

        # Create the MTRM button, disabled if Materium is 0
        mtrm_button = discord.ui.Button(
            custom_id="use_mtrm",
            label="MTRM",
            style=discord.ButtonStyle.primary,
            emoji=get_emoji('Materium'),
            disabled=self.player.inventory.materium == 0
        )
        mtrm_button.callback = self.use_mtrm_callback  # Link callback function
        self.add_item(mtrm_button)

        # Create the Resurrect button
        resurrect_button = discord.ui.Button(
            custom_id="resurrect",
            label="Resurrect",
            style=discord.ButtonStyle.danger
        )
        resurrect_button.callback = self.resurrect_callback  # Link callback function
        self.add_item(resurrect_button)

    mtrm = get_emoji('Materium')
    async def use_mtrm_callback(self, interaction):

        # Check if the user who interacted is the same as the one who initiated the view
        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        self.player_data = load_player_data(interaction.guild.id)
        self.player = Exemplar(self.player_data[self.author_id]["exemplar"],
                               self.player_data[self.author_id]["stats"],
                               self.player_data[self.author_id]["inventory"])

        if self.player.stats.health > 0:
            # Player is not dead
            return await self.not_dead_response(interaction)

        if self.player_data[self.author_id]["inventory"].materium >= 1:
            self.player_data[self.author_id]["inventory"].materium -= 1
            self.player.stats.health = self.player.stats.max_health
            self.player.stats.stamina = self.player.stats.max_stamina
            self.player_data[self.author_id]["stats"].update(self.player.stats.__dict__)  # Save the updated stats

            # Create a new embed with only the renewed message
            new_embed = discord.Embed(title="Revived", description="You feel *strangely renewed* and **ready for battle**!",
                                      color=discord.Color.green())

            # Add the full health bar to the embed
            new_embed.add_field(name="Your Health & Stamina have been Restored",
                                value=f"{get_emoji('heart_emoji')}  {self.player.stats.health}/{self.player.stats.max_health}\n"
                                      f"{get_emoji('stamina_emoji')}  {self.player.stats.stamina}/{self.player.stats.max_stamina}")

            new_embed.add_field(name=f"{self.mtrm}  Remaining",
                                value=f"{self.player_data[self.author_id]['inventory'].materium}")

            # Add the "Revive" image to the embed
            new_embed.set_image(url="https://raw.githubusercontent.com/kal-elf2/MTRM-RPG/master/images/cemetery/Revive.png")

            await interaction.message.edit(
                embed=new_embed,
                view=None,
            )
            save_player_data(interaction.guild.id, self.player_data)

    async def resurrect_callback(self, interaction):

        # Check if the user who interacted is the same as the one who initiated the view
        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        self.player_data = load_player_data(interaction.guild.id)
        self.player = Exemplar(self.player_data[self.author_id]["exemplar"],
                               self.player_data[self.author_id]["stats"],
                               self.player_data[self.author_id]["inventory"])

        if self.player.stats.health > 0:
            # Player is not dead
            return await self.not_dead_response(interaction)

        # Apply the penalty since the user doesn't have enough MTRM
        levels_decreased = await apply_penalty(self.player_data, self.author_id, interaction)

        # Update player data for death penalty
        player_inventory = self.player_data[self.author_id]['inventory']

        # Before resetting the inventory, deep copy the entire inventory
        saved_inventory = copy.deepcopy(player_inventory)

        # Reset the inventory attributes
        player_inventory.items = []
        player_inventory.trees = []
        player_inventory.herbs = []
        player_inventory.ore = []
        player_inventory.armors = []
        player_inventory.weapons = []
        player_inventory.shields = []

        # Save the updated stats
        save_player_data(interaction.guild.id, self.player_data)

        # Update self.player based on updated player_data
        updated_stats = self.player_data[self.author_id]['stats']
        self.player.stats.health = updated_stats['health']
        self.player.stats.max_health = updated_stats['max_health']

        # Create a new embed with adjusted info
        new_embed = discord.Embed(title="You've been resurrected, but at a cost.",
                                  color=0xff0000)

        # Define emojis for skills
        skill_emojis = {
            "combat": "⚔️",
            "woodcutting": "🪓",
            "mining": "⛏️"
        }

        # If levels were decreased, show that information
        if levels_decreased:
            level_decreased_message = '\n'.join(
                [f"{skill_emojis.get(skill, '')}  **{skill.capitalize()}**: {new_level}  ({diff})"
                 for skill, (new_level, diff) in levels_decreased.items()]
            )
            # Add the full health bar to the embed
            new_embed.add_field(name="Your Health has been Restored",
                                value=f"{get_emoji('heart_emoji')}  {self.player.stats.health}/{self.player.stats.max_health}")

            new_embed.add_field(name="Skills Affected", value=level_decreased_message)

        else:
            # Add the full health bar to the embed
            new_embed.add_field(name="Your Health has been Restored",
                                value=f"{get_emoji('heart_emoji')}  {self.player.stats.health}/{self.player.stats.max_health}")

            new_embed.add_field(name="Skills Affected", value="No skills were affected.")

        # Add the "dead.png" image to the embed
        new_embed.set_image(url=generate_urls("cemetery", "Revive"))

        # Send the new embed as a new message, without view buttons
        await interaction.message.edit(embed=new_embed, view=None)

        if self.include_nero:
            from nero.cemetery_buyback import NeroView
            nero_view = NeroView(interaction, self.player_data, self.author_id, self.player, saved_inventory)

            cost = buyback_cost * self.player.stats.zone_level
            formatted_cost = f"{cost:,}"  # Format the number with commas
            formatted_coppers = f"{self.player.inventory.coppers:,}"  # Format player's coppers with commas

            thumbnail_url = generate_urls("nero", "cemetery")
            nero_embed = discord.Embed(
                title="Captain Ner0",
                description=f"Arr, there ye be, {interaction.user.mention}! I've scooped up all yer belongings after that nasty scuffle. "
                            f"Ye can have 'em back, but it'll cost ye some coppers, savvy? Hows about **{formatted_cost}**{get_emoji('coppers_emoji')}? A fair price for a fair service, says I.\n\n"
                            f"**Backpack**: {formatted_coppers}{get_emoji('coppers_emoji')}",
                color=discord.Color.dark_gold()
            )
            nero_embed.set_thumbnail(url=thumbnail_url)

            # Send the message with the NeroView in the channel
            channel = interaction.channel
            await asyncio.sleep(1)
            await channel.send(embed=nero_embed, view=nero_view)

    @staticmethod
    async def not_dead_response(interaction):
        # Static method to handle the response when the player is not dead
        nero_embed = discord.Embed(
            title="Captain Ner0",
            description="Errr... Yer not dead, matey. What are ye doin' here playin' with these buttons?",
            color=discord.Color.dark_gold()
        )
        nero_embed.set_thumbnail(url=generate_urls("nero", "confused"))
        await interaction.response.send_message(embed=nero_embed, ephemeral=True)

async def apply_penalty(player_data, author_id, interaction):
    stats = player_data[author_id]["stats"]
    levels_decreased = {}
    player = Exemplar(player_data[author_id]["exemplar"],
                      player_data[author_id]["stats"],
                      player_data[author_id]["inventory"])

    new_combat_level = None
    for skill in ["combat_experience", "woodcutting_experience", "mining_experience"]:
        original_skill_name = skill[:-11]  # Remove '_experience' from the skill name
        original_level = stats[f"{original_skill_name}_level"]

        # Apply the 2.5% penalty
        new_exp = max(0, math.floor(stats[skill] * 0.975))
        stats[skill] = new_exp  # Update the experience in player_data

        # Recalculate the level based on the new experience
        new_level = recalculate_level(stats[skill])

        if new_level < original_level:
            diff = new_level - original_level  # Calculate the difference
            levels_decreased[original_skill_name] = (new_level, diff)  # Storing new level and the decrease

        if original_skill_name == "combat":
            new_combat_level = new_level

        stats[f"{original_skill_name}_level"] = new_level  # Update the level in the player's stats

        # Extract only the level (first element of the tuple) for woodcutting and mining
        woodcutting_level = levels_decreased.get('woodcutting', (None,))[0]
        mining_level = levels_decreased.get('mining', (None,))[0]

    # Call the function to update combat stats once, after all skills have been processed
    player.set_combat_stats(new_combat_level, player, woodcutting_level, mining_level)

    player_data[author_id]["stats"]["health"] = player.stats.health
    player_data[author_id]["stats"]["max_health"] = player.stats.max_health
    player_data[author_id]["stats"]["strength"] = player.stats.strength
    player_data[author_id]["stats"]["stamina"] = player.stats.stamina
    player_data[author_id]["stats"]["max_stamina"] = player.stats.max_stamina
    player_data[author_id]["stats"]["attack"] = player.stats.attack
    player_data[author_id]["stats"]["defense"] = player.stats.defense

    return levels_decreased

def recalculate_level(updated_exp):
    with open("level_data.json", "r") as f:
        LEVEL_DATA = json.load(f)
    # Find the correct level range based on the player's total experience
    for level, level_data in LEVEL_DATA.items():
        if updated_exp <= level_data["total_experience"]:
            new_level = int(level)
            break
    else:
        new_level = len(LEVEL_DATA)
    return new_level

def setup(bot):
    bot.add_cog(StatsCog(bot))