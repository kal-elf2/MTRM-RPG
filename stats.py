import json
import discord
from discord.ext import commands
from discord.commands import Option
from utils import load_player_data

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


def setup(bot):
    bot.add_cog(StatsCog(bot))