import json
import math
import discord
from discord import Embed
from discord.ext import commands
from utils import load_player_data, load_all_player_data, save_player_data, CommonResponses
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
            discord.SelectOption(label="📊 Level Progress", value="level_progress", description="View your progress in levels"),
            discord.SelectOption(label="🎲 Three Eyed Snake", value="three_eyed_snake", description="View your Three Eyed Snake stats"),
            discord.SelectOption(label="👾 Monster Kills", value="monster_kills", description="View your Monster Kills stats")
        ]
        super().__init__(placeholder="Choose a category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        from exemplars.exemplars import DiceStats, MonsterKills

        # Authorization check
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        author_id = str(interaction.user.id)
        player_data = load_player_data(interaction.guild.id, author_id)

        if self.values[0] == "level_progress":
            # Send combined level progress information
            embed = self.create_level_progress_embed(player_data["stats"], self.zone_level)
            await interaction.response.send_message(embed=embed, ephemeral=False)

        elif self.values[0] == "three_eyed_snake":
            # Send Three Eyed Snake stats
            dice_stats = DiceStats.from_dict(player_data["dice_stats"])
            embed = self.create_three_eyed_snake_embed(dice_stats, self.zone_level)
            await interaction.response.send_message(embed=embed, ephemeral=False)

        elif self.values[0] == "monster_kills":
            # Send Monster Kills stats
            monster_kills = MonsterKills.from_dict(player_data["monster_kills"])
            embed = self.create_monster_kills_embed(monster_kills, self.zone_level)
            await interaction.response.send_message(embed=embed, ephemeral=False)

    @staticmethod
    def create_level_progress_embed(stats, zone_level):
        level_data = load_level_data()
        embed_color = color_mapping.get(zone_level, 0x969696)
        embed = discord.Embed(title="__Level Progress__", color=embed_color)

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
            formatted_current_exp = "{:,}".format(current_exp)

            # Display skill level
            embed.add_field(name=f"{emoji} {skill_capitalized}", value=f'Level {str(level)}', inline=True)

            # Display experience to next level or max level status
            if level == 99:
                embed.add_field(name="Total Experience", value=formatted_current_exp, inline=True)
                embed.add_field(name="Status", value="📊 Max Level!", inline=True)
            else:
                next_level = int(level) + 1
                exp_needed = experience_needed_to_next_level(level, current_exp, level_data)
                formatted_exp_needed = "{:,}".format(exp_needed)
                embed.add_field(name=f"🔼 XP to Lvl {next_level}", value=formatted_exp_needed, inline=True)
                embed.add_field(name="📊 Total XP", value=formatted_current_exp, inline=True)

            # Add progress bar for each skill
            progress_bar, progress_percentage = create_progress_bar(current_exp, level, level_data)
            embed.add_field(name=f"Progress: **{progress_percentage}%**", value=f"{progress_bar}\n\u200B", inline=False)

        return embed

    @staticmethod
    def create_three_eyed_snake_embed(dice_stats, zone_level):
        # Check if coppers won is negative and adjust the label and value accordingly
        coppers_label = "Coppers Lost" if dice_stats.coppers_won < 0 else "Coppers Won"
        formatted_coppers_won = "{:,}".format(abs(dice_stats.coppers_won))

        stats_info = (f"#️⃣ Total Games: {dice_stats.total_games:,}\n"
                      f"🏆 Games Won: {dice_stats.games_won:,}\n"
                      f"💸 Games Lost: {dice_stats.games_lost:,}\n"
                      f"{get_emoji('coppers_emoji')} {coppers_label}: {formatted_coppers_won}")

        embed_color = color_mapping.get(zone_level, 0x969696)
        embed = discord.Embed(title="🎲 __Three Eyed Snake Stats__ 🎲", color=embed_color)
        embed.add_field(name=stats_info, value="\u200B", inline=False)
        embed.set_thumbnail(url=generate_urls("nero", "dice"))

        return embed

    @staticmethod
    def create_monster_kills_embed(monster_kills, zone_level):
        # Format each kill count with commas
        formatted_kills_info = "\n".join(
            [f"{monster}: {count:,}" for monster, count in monster_kills.monster_kills.items()])

        # Find the monster with the highest kill count
        most_killed_monster = max(monster_kills.monster_kills.items(), key=lambda x: x[1])[0]

        embed_color = color_mapping.get(zone_level, 0x969696)
        embed = discord.Embed(
            title=f"👾 __Monster Kills__ 👾",
            color=embed_color)
        embed.add_field(name=formatted_kills_info, value="\u200B", inline=False)
        embed.set_thumbnail(url=generate_urls("monsters", most_killed_monster))

        return embed


class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="View your stats")
    async def stats(self, ctx):
        guild_id = ctx.guild.id
        author_id = str(ctx.author.id)

        player_data = load_player_data(guild_id, author_id)

        # Check if player data exists for the user
        if not player_data:
            embed = Embed(title="Captain Ner0",
                          description="Arr! What be this? No record of yer adventures? Start a new game with `/newgame` before I make ye walk the plank.",
                          color=discord.Color.dark_gold())
            embed.set_thumbnail(url=generate_urls("nero", "confused"))
            await ctx.respond(embed=embed, ephemeral=True)
            return

        player = player_data["stats"]
        inventory = player_data["inventory"]
        zone_level = player_data["stats"]["zone_level"]
        exemplar = player_data['exemplar']
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

        # Add overall stats and inventory to the embed
        all_stats = f"""**Exemplar**: {exemplar.capitalize()}
                        **Current Zone**: {zone_level}\n
                        ⚔️ **Combat Level**: {player['combat_level']}
                        {get_emoji('heart_emoji')} **Health**: {player['health']}
                        {get_emoji('strength_emoji')} **Strength**: {player['strength']}
                        {get_emoji('stamina_emoji')}️ **Stamina**: {player['stamina']}
                        🗡️ **Attack**: {player['attack']}
                        🛡️ **Defense**: {player['defense']}
                        ⛏️ **Mining Level**: {player['mining_level']}
                        🪓 **Woodcutting Level**: {player['woodcutting_level']}\n
                        {get_emoji('Materium')} **Materium**: {inventory.materium:,}
                        {get_emoji('coppers_emoji')} **Coppers**: {inventory.coppers:,}"""

        embed.add_field(name="📊  __Overall Stats__  📊", value=all_stats, inline=False)
        specialty = weapon_specialty.get(exemplar)
        embed.set_footer(text=f"Weapon Bonus: {specialty}")

        # Send the embed with overall stats
        await ctx.respond(content=f"{ctx.author.mention}'s Overall Stats", embed=embed)

        # Send the dropdown view for additional stats
        view = StatsView(author_id=str(ctx.author.id), zone_level=zone_level)
        await ctx.send("Select a category to view more details:", view=view)

    @commands.slash_command(description="View leaderboards")
    async def leaders(self, ctx):
        guild_id = ctx.guild.id
        author_id = str(ctx.author.id)

        # Embed with pirate-themed message
        embed = discord.Embed(
            title="🏴‍☠️ Captain Ner0's Scroll of Fame 🏴‍☠️",
            description=f"Ahoy, {ctx.author.mention}! Are ye keen to see where ye rank in the arts of cunning and coin? Cast your eye upon the leaderboards, and discover whether ye be a master of skill and splendor, or just another dockside drifter counting coppers.",
            color=discord.Color.dark_gold()
        )
        embed.set_image(url=generate_urls("nero", "leaderboard"))

        # Create the view with the dropdown and reset button
        view = LeaderboardView(author_id, guild_id)

        # Send the embed with the view
        await ctx.respond(embed=embed, view=view)

class LeaderboardView(discord.ui.View):
    def __init__(self, author_id, guild_id):
        super().__init__()
        self.add_item(LeaderboardDropdown(author_id, guild_id))

class LeaderboardDropdown(discord.ui.Select, CommonResponses):
    def __init__(self, author_id, guild_id):
        self.author_id = author_id
        self.guild_id = guild_id

        options = [
            discord.SelectOption(label="📊 Skills", description="View skills leaderboard", value="skills"),
            discord.SelectOption(label="👾 Monster Kills", description="View monster kills leaderboard",
                                 value="monster_kills"),
            discord.SelectOption(label="🎲 Three-Eyed-Snake", description="View Three-Eyed-Snake game leaderboard",
                                 value="three_eyed_snake"),
            discord.SelectOption(label="💰 Rich List", description="View the rich list leaderboard", value="rich_list")
        ]
        super().__init__(placeholder="Choose a category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        self.view.clear_items()
        selected_value = self.values[0]
        if selected_value == "skills":
            self.view.add_item(SkillsDropdown(self.author_id, self.guild_id))
        elif selected_value == "monster_kills":
            self.view.add_item(MonsterKillsDropdown(self.author_id, self.guild_id))
        elif selected_value == "three_eyed_snake":
            self.view.add_item(ThreeEyedSnakeDropdown(self.author_id, self.guild_id))
        elif selected_value == "rich_list":
            self.view.add_item(RichListDropdown(self.author_id, self.guild_id))

        # Add the ResetButton back to the view
        self.view.add_item(ResetButton(self.author_id, self.guild_id))

        await interaction.response.edit_message(view=self.view)

class SkillsDropdown(discord.ui.Select, CommonResponses):
    def __init__(self, author_id, guild_id):
        self.author_id = author_id
        self.guild_id = guild_id
        options = [
            discord.SelectOption(label="⚔️ Combat", value="combat"),
            discord.SelectOption(label="🪓 Woodcutting", value="woodcutting"),
            discord.SelectOption(label="⛏️ Mining", value="mining")
        ]
        super().__init__(placeholder="Choose a skill...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Load player data
        player_data = load_all_player_data(self.guild_id)

        # Sort players based on selected skill's experience
        skill = self.values[0]
        sorted_players = sorted(player_data.items(), key=lambda x: x[1]['stats'][f'{skill}_experience'], reverse=True)

        # Check if there are players with data
        if not sorted_players or all(data['stats'][f'{skill}_experience'] == 0 for _, data in sorted_players):
            await interaction.response.send_message("No leaders yet in this category.", ephemeral=True)
            return

        # Create embed to display leaderboard
        skill_emoji = "⚔️" if skill == "combat" else "🪓" if skill == "woodcutting" else "⛏️"
        embed = discord.Embed(title=f"{skill_emoji} __Top 5 {skill.capitalize()} Leaders__ {skill_emoji}",
                              color=discord.Color.blue())

        medals = ["🥇", "🥈", "🥉"]
        for index, (player_id, data) in enumerate(sorted_players[:5]):
            if data['stats'][f'{skill}_experience'] == 0:
                continue
            player = interaction.guild.get_member(int(player_id))
            player_name = player.display_name
            level = data['stats'][f'{skill}_level']
            experience = "{:,}".format(data['stats'][f'{skill}_experience'])
            rank = medals[index] if index < 3 else f"{index + 1}th"
            embed.add_field(name=f"{rank} - {player_name}", value=f"Level: {level}  |  XP: {experience}", inline=False)

            if index == 0 and player and player.avatar:  # Set thumbnail for the first-place player
                embed.set_thumbnail(url=player.avatar.url)

        # Send the embed as an ephemeral message
        await interaction.response.send_message(embed=embed, ephemeral=True)

class MonsterKillsDropdown(discord.ui.Select, CommonResponses):
    def __init__(self, author_id, guild_id):
        self.author_id = author_id
        self.guild_id = guild_id

        # Dynamically generate options based on the monsters in your game
        options = [
            discord.SelectOption(label="Rabbit", value="Rabbit"),
            discord.SelectOption(label="Deer", value="Deer"),
            discord.SelectOption(label="Buck", value="Buck"),
            discord.SelectOption(label="Wolf", value="Wolf"),
            discord.SelectOption(label="Goblin", value="Goblin"),
            discord.SelectOption(label="Goblin Hunter", value="Goblin Hunter"),
            discord.SelectOption(label="Mega Brute", value="Mega Brute"),
            discord.SelectOption(label="Wisp", value="Wisp"),
            discord.SelectOption(label="Mother", value="Mother"),
            discord.SelectOption(label="Kraken", value="Kraken")
        ]
        super().__init__(placeholder="Choose a monster...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Load player data
        player_data = load_all_player_data(self.guild_id)

        # Select the monster
        monster = self.values[0]

        # Sort players based on the selected monster's kill count
        sorted_players = sorted(player_data.items(), key=lambda x: x[1]['monster_kills'].get(monster, 0), reverse=True)

        # Check if there are players with data
        if not sorted_players or all(data['monster_kills'].get(monster, 0) == 0 for _, data in sorted_players):
            await interaction.response.send_message(f"The {monster.capitalize()} has yet to be slain.", ephemeral=True)
            return

        # Create embed to display leaderboard
        embed = discord.Embed(title=f"Top 5 {monster.title()} Slayers", color=discord.Color.green())

        medals = ["🥇", "🥈", "🥉"]
        for index, (player_id, data) in enumerate(sorted_players[:5]):
            if data['monster_kills'].get(monster, 0) == 0:
                continue
            player = interaction.guild.get_member(int(player_id))
            player_name = player.display_name if player else "Unknown Player"
            kill_count = "{:,}".format(data['monster_kills'][monster])  # Format with commas
            rank = medals[index] if index < 3 else f"{index + 1}th"
            embed.add_field(name=f"{rank} - {player_name}", value=f"Kills: {kill_count}", inline=False)

            if index == 0:
                if player and player.avatar:
                    embed.set_thumbnail(url=player.avatar.url)
                else:
                    # Set default thumbnail to the monster image
                    embed.set_thumbnail(url=generate_urls('monsters', monster.title()))

        # Send the embed as an ephemeral message
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ThreeEyedSnakeDropdown(discord.ui.Select, CommonResponses):
    def __init__(self, author_id, guild_id):
        self.author_id = author_id
        self.guild_id = guild_id
        options = [
            discord.SelectOption(label="Games Played", value="total_games", emoji="🎲"),
            discord.SelectOption(label="Games Won", value="games_won", emoji="🏆"),
            discord.SelectOption(label="Coppers Won", value="coppers_won", emoji=get_emoji('coppers_emoji'))
        ]
        super().__init__(placeholder="Choose a category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Load player data
        player_data = load_all_player_data(self.guild_id)

        # Select the category
        category = self.values[0]

        # Sort players based on the selected category
        sorted_players = sorted(player_data.items(), key=lambda x: x[1]['dice_stats'].get(category, 0), reverse=True)

        # Filter out negative coppers if category is 'coppers_won'
        if category == 'coppers_won':
            sorted_players = [(id, data) for id, data in sorted_players if data['dice_stats'].get(category, 0) > 0]

        # Check if there are players with data
        if not sorted_players:
            await interaction.response.send_message(f"No leaders yet for {category.replace('_', ' ').capitalize()}.",
                                                    ephemeral=True)
            return

        # Create embed to display leaderboard
        category_title = category.replace('_', ' ').title()
        stat_label = "Games Played" if category == "total_games" else category_title
        emoji = "🎲" if category == "total_games" else "🏆" if category == "games_won" else get_emoji('coppers_emoji')
        title = f"{emoji} __Top 5 {category_title} Leaders__ {emoji}"
        embed = discord.Embed(title=title, color=discord.Color.orange())

        medals = ["🥇", "🥈", "🥉"]
        for index, (player_id, data) in enumerate(sorted_players[:5]):
            player = interaction.guild.get_member(int(player_id))
            player_name = player.display_name if player else "Unknown Player"
            stat_count = "{:,}".format(data['dice_stats'][category])
            rank = medals[index] if index < 3 else f"{index + 1}th"

            # Format the label differently for 'Coppers Won' category
            if category == 'coppers_won':
                label = f"{emoji} {stat_count}"
            else:
                label = f"{stat_label}: {stat_count}"

            embed.add_field(name=f"{rank} - {player_name}", value=label, inline=False)

            if index == 0 and player and player.avatar:
                embed.set_thumbnail(url=player.avatar.url)

        # Send the embed as an ephemeral message
        await interaction.response.send_message(embed=embed, ephemeral=True)

class RichListDropdown(discord.ui.Select, CommonResponses):
    def __init__(self, author_id, guild_id):
        self.author_id = author_id
        self.guild_id = guild_id
        options = [
            discord.SelectOption(label="Coppers", value="coppers", emoji=get_emoji('coppers_emoji')),
            discord.SelectOption(label="Materium", value="materium", emoji=get_emoji('Materium'))
        ]
        super().__init__(placeholder="Choose a category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Load player data
        player_data = load_all_player_data(self.guild_id)

        # Initialize player objects and sort based on the selected category
        sorted_players = []
        for player_id, data in player_data.items():
            player = Exemplar(data["exemplar"], data["stats"], data["inventory"])
            sorted_players.append((player_id, player))

        # Select the category
        category = self.values[0]

        sorted_players.sort(key=lambda x: getattr(x[1].inventory, category, 0), reverse=True)

        # Filter out players with 0 value and limit to top 5
        sorted_players = [(pid, p) for pid, p in sorted_players if getattr(p.inventory, category, 0) > 0][:5]

        # Check if there are players with data
        if not sorted_players:
            await interaction.response.send_message(f"No leaders yet for {category.capitalize()}.", ephemeral=True)
            return

        # Create embed to display leaderboard
        emoji = get_emoji('coppers_emoji') if category == 'coppers' else get_emoji('Materium')
        title = f"{emoji} __Top 5 {category.capitalize()} Leaders__ {emoji}"
        embed = discord.Embed(title=title, color=discord.Color.orange())

        medals = ["🥇", "🥈", "🥉"]
        for index, (player_id, player) in enumerate(sorted_players):
            guild_member = interaction.guild.get_member(int(player_id))
            player_name = guild_member.display_name if guild_member else "Unknown Player"
            stat_count = "{:,}".format(getattr(player.inventory, category))
            rank = medals[index] if index < 3 else f"{index + 1}th"
            embed.add_field(name=f"{rank} - {player_name}", value=f"{emoji} {stat_count}", inline=False)

            if index == 0 and guild_member and guild_member.avatar:
                embed.set_thumbnail(url=guild_member.avatar.url)

        # Send the embed as an ephemeral message
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ResetButton(discord.ui.Button, CommonResponses):
    def __init__(self, author_id, guild_id):
        self.author_id = author_id
        self.guild_id = guild_id
        super().__init__(label="Reset", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        self.view.clear_items()
        self.view.add_item(LeaderboardDropdown(self.author_id, self.guild_id))
        await interaction.response.edit_message(view=self.view)

class ResurrectOptions(discord.ui.View, CommonResponses):
    def __init__(self, interaction, player_data, author_id, include_nero=True):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.player_data = player_data
        self.author_id = author_id
        self.include_nero = include_nero

        self.player = Exemplar(player_data["exemplar"],
                               player_data["stats"],
                               player_data["inventory"])

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

        self.player_data = load_player_data(interaction.guild.id, self.author_id)
        self.player = Exemplar(self.player_data["exemplar"],
                               self.player_data["stats"],
                               self.player_data["inventory"])

        if self.player.stats.health > 0:
            # Player is not dead
            return await self.not_dead_response(interaction)

        if self.player_data["inventory"].materium >= 1:
            self.player_data["inventory"].materium -= 1
            self.player.stats.health = self.player.stats.max_health
            self.player.stats.stamina = self.player.stats.max_stamina
            self.player_data["stats"].update(self.player.stats.__dict__)  # Save the updated stats

            # Create a new embed with only the renewed message
            new_embed = discord.Embed(title="Revived", description="You feel *strangely renewed* and **ready for battle**!",
                                      color=discord.Color.green())

            # Add the full health bar to the embed
            new_embed.add_field(name="Your Health & Stamina have been Restored",
                                value=f"{get_emoji('heart_emoji')}  {self.player.stats.health}/{self.player.stats.max_health}\n"
                                      f"{get_emoji('stamina_emoji')}  {self.player.stats.stamina}/{self.player.stats.max_stamina}")

            new_embed.add_field(name=f"{self.mtrm}  Remaining",
                                value=f"{self.player_data['inventory'].materium}")

            # Add the "Revive" image to the embed
            new_embed.set_image(url="https://raw.githubusercontent.com/kal-elf2/MTRM-RPG/master/images/cemetery/Revive.png")

            await interaction.message.edit(
                embed=new_embed,
                view=None,
            )
            save_player_data(interaction.guild.id, self.author_id, self.player_data)

    async def resurrect_callback(self, interaction):

        # Check if the user who interacted is the same as the one who initiated the view
        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        self.player_data = load_player_data(interaction.guild.id, self.author_id)
        self.player = Exemplar(self.player_data["exemplar"],
                               self.player_data["stats"],
                               self.player_data["inventory"])

        if self.player.stats.health > 0:
            # Player is not dead
            return await self.not_dead_response(interaction)

        # Apply the penalty since the user doesn't have enough MTRM
        levels_decreased = await apply_penalty(self.player_data, self.author_id, interaction)

        # Update player data for death penalty
        player_inventory = self.player_data['inventory']

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
        save_player_data(interaction.guild.id, self.author_id, self.player_data)

        # Update self.player based on updated player_data
        updated_stats = self.player_data['stats']
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
    stats = player_data["stats"]
    levels_decreased = {}
    player = Exemplar(player_data["exemplar"],
                      player_data["stats"],
                      player_data["inventory"])

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

    player_data["stats"]["health"] = player.stats.health
    player_data["stats"]["max_health"] = player.stats.max_health
    player_data["stats"]["strength"] = player.stats.strength
    player_data["stats"]["stamina"] = player.stats.stamina
    player_data["stats"]["max_stamina"] = player.stats.max_stamina
    player_data["stats"]["attack"] = player.stats.attack
    player_data["stats"]["defense"] = player.stats.defense

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