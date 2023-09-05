import json
import math
import discord
from discord.ext import commands
from discord.commands import Option
from utils import load_player_data, save_player_data
from exemplars.exemplars import Exemplar


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


class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="View your stats")
    async def stats(self, ctx, progress: Option(str, "Choose a subgroup to view details",
                                                choices=['Combat Level', 'Fishing', 'Mining', 'Woodcutting'],
                                                required=False,
                                                default=None)):
        guild_id = ctx.guild.id
        author_id = str(ctx.author.id)

        player_data = load_player_data(guild_id)
        player = player_data[author_id]["stats"]

        level_data = load_level_data()

        embed = discord.Embed(color=discord.Color.blue())

        if progress is None:
            all_stats = f"""**Exemplar**: {str(player_data[author_id]['exemplar']).capitalize()}\n
            ⚔️ **Combat Level**: {str(player['combat_level'])}
            ❤️ **Health**: {str(player['health'])}
            💪 **Strength**: {str(player['strength'])}
            🏃️ **Endurance**: {str(player['endurance'])}
            🗡️ **Attack**: {str(player['attack'])}
            🛡️ **Defense**: {str(player['defense'])}
            🎣 **Fishing Level**: {str(player['fishing_level'])}
            ⛏️ **Mining Level**: {str(player['mining_level'])}
            🪓 **Woodcutting Level**: {str(player['woodcutting_level'])}"""

            embed.add_field(name="Overall Stats", value=all_stats, inline=False)
            await ctx.respond(content=f"{ctx.author.mention}'s Overall Stats", embed=embed)
        else:
            if progress == 'Combat Level':
                display = '⚔️ Combat Level ⚔️'
                level = player['combat_level']
                current_exp = player['combat_experience']
            elif progress == 'Fishing':
                display = '🎣 Fishing Level 🎣'
                level = player['fishing_level']
                current_exp = player['fishing_experience']
            elif progress == 'Mining':
                display = '⛏️ Mining Level ⛏️'
                level = player['mining_level']
                current_exp = player['mining_experience']
            else: #woodcutting
                display = '🪓 Woodcutting Level 🪓'
                level = player['woodcutting_level']
                current_exp = player['woodcutting_experience']

            next_level = int(level) + 1
            exp_needed = experience_needed_to_next_level(level, current_exp, level_data)
            progress_bar, progress_percentage = create_progress_bar(current_exp, level, level_data)

            embed.add_field(name=f"Current Level", value=level, inline=True)

            if str(next_level) in level_data:
                embed.add_field(name=f"XP to Level {next_level}", value=exp_needed, inline=True)
                embed.add_field(name=f"Progress: **{progress_percentage}%**", value=progress_bar, inline=True)
            else:
                embed.add_field(name="XP to Level Up", value="Max Level Reached", inline=True)
                embed.add_field(name=f"Progress: **N/A**", value="Max Level Reached", inline=True)

            await ctx.respond(content=f"{ctx.author.mention}'s **{display}**", embed=embed)


class ResurrectOptions(discord.ui.View):
    def __init__(self, interaction, player_data, author_id, battle_embed):
        super().__init__(timeout=1800)  # 30 minutes
        self.interaction = interaction
        self.player_data = player_data
        self.author_id = author_id
        self.battle_embed = battle_embed

        self.player = Exemplar(player_data[author_id]["exemplar"],
                               player_data[author_id]["stats"],
                               player_data[author_id]["inventory"])

    mtrm_emoji = '<:mtrm:1148449848085979167>'

    @discord.ui.button(custom_id="use_mtrm", label="MTRM", style=discord.ButtonStyle.primary, emoji=mtrm_emoji)
    async def use_mtrm(self, button, interaction):
        if self.player_data[self.author_id]["inventory"].materium_count >= 1:
            self.player_data[self.author_id]["inventory"].materium_count -= 1
            self.player.stats.health = self.player.stats.max_health  # Update health here
            self.player_data[self.author_id]["stats"].update(self.player.stats.__dict__)  # Save the updated stats

            # Create a new embed with only the renewed message
            new_embed = discord.Embed(title="Revived", description="You feel *strangely renewed* and **ready for battle**!",
                                      color=discord.Color.green())

            # Add the full health bar to the embed
            new_embed.add_field(name="Your Health has been Restored",
                                value=f"❤️  {self.player.stats.health}/{self.player.stats.max_health}")

            new_embed.add_field(name=f"{self.mtrm_emoji}  Remaining",
                                value=f"{self.player_data[self.author_id]['inventory'].materium_count}")

            # Add the "Revive" image to the embed
            new_embed.set_image(url="https://raw.githubusercontent.com/kal-elf2/MTRM-RPG/master/images/Revive.png")

            await interaction.message.edit(
                embed=new_embed,
                view=None,
            )
            save_player_data(interaction.guild.id, self.player_data)
        else:
            # Apply the penalty since the user doesn't have enough MTRM
            levels_decreased = await apply_penalty(self.player_data, self.author_id, interaction)

            # Define emojis for skills
            skill_emojis = {
                "combat": "⚔️",
                "fishing": "🎣",
                "woodcutting": "🪓",
                "mining": "⛏️"
            }

            # Create a new embed
            new_embed = discord.Embed(title=f"You don't have enough {self.mtrm_emoji}  MTRM. \n\nYou've been resurrected but at a cost.",
                                      color=0xff0000)  # Red color

            # If levels were decreased, show that information
            if levels_decreased:
                level_decreased_message = '\n'.join(
                    [f"{skill_emojis.get(skill, '')}  **{skill.capitalize()}**: {new_level}  ({diff})"
                     for skill, (new_level, diff) in levels_decreased.items()]
                )
                new_embed.add_field(name="Skills Affected", value=level_decreased_message)
            else:
                new_embed.add_field(name="Skills Affected", value="No skills were affected.")

            # Send the new embed as a new message
            await interaction.response.send_message(embed=new_embed)

            # Save player data
            save_player_data(interaction.guild.id, self.player_data)

    @discord.ui.button(custom_id="resurrect", label="Resurrect", style=discord.ButtonStyle.danger)
    async def resurrect(self, button, interaction):

        levels_decreased = await apply_penalty(self.player_data, self.author_id,
                                               interaction)  # Capture the return value

        # Create a new embed with adjusted info
        new_embed = discord.Embed(title="You've been resurrected, but at a cost.",
                                  color=0xff0000)  # Red color

        # Define emojis for skills
        skill_emojis = {
            "combat": "⚔️",
            "fishing": "🎣",
            "woodcutting": "🪓",
            "mining": "⛏️"
        }

        # If levels were decreased, show that information
        if levels_decreased:
            level_decreased_message = '\n'.join(
                [f"{skill_emojis.get(skill, '')} **{skill.capitalize()}**: {new_level} ({diff})"
                 for skill, (new_level, diff) in levels_decreased.items()]
            )
            new_embed.add_field(name="Skills Affected", value=level_decreased_message)
        else:
            new_embed.add_field(name="Skills Affected", value="No skills were affected.")

        # Send the new embed as a new message
        await interaction.response.send_message(embed=new_embed)

        # Save player data
        save_player_data(interaction.guild.id, self.player_data)


async def apply_penalty(player_data, author_id, interaction):
    stats = player_data[author_id]["stats"]
    levels_decreased = {}
    for skill in ["combat_experience", "fishing_experience", "woodcutting_experience", "mining_experience"]:
        original_skill_name = skill[:-11]  # Remove '_experience' from the skill name
        original_level = stats[f"{original_skill_name}_level"]

        # Apply the 2.5% penalty
        stats[skill] = max(1, math.floor(stats[skill] * 0.975))

        # Recalculate the level based on the new experience
        new_level = recalculate_level(stats[skill])

        if new_level < original_level:
            diff = new_level - original_level  # Calculate the difference
            levels_decreased[original_skill_name] = (new_level, diff)  # Storing new level and the decrease

        stats[f"{original_skill_name}_level"] = new_level  # Update the level in the player's stats

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