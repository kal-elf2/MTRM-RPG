import discord
from images.urls import generate_urls
from utils import save_player_data, load_player_data
from exemplars.exemplars import Exemplar
from emojis import get_emoji

class HealTentButton(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx

    @discord.ui.button(label="Heal", custom_id="heal", style=discord.ButtonStyle.green)
    async def heal(self, button, interaction):
        def health_bar(current, max_health):
            bar_length = 20  # Fixed bar length
            health_percentage = current / max_health
            filled_length = round(bar_length * health_percentage)

            # Calculate how many '◼' symbols to display
            filled_symbols = '◼' * filled_length

            # Calculate how many '◻' symbols to display
            empty_symbols = '◻' * (bar_length - filled_length)
            return filled_symbols + empty_symbols

        author_id = str(interaction.user.id)
        guild_id = self.ctx.guild.id

        player_data = load_player_data(guild_id)
        player = Exemplar(
            player_data[author_id]["exemplar"],
            player_data[author_id]["stats"],
            player_data[author_id]["inventory"]
        )

        # Heal the player by 25 HP, up to the maximum health
        player.stats.health = min(player.stats.health + 25, player.stats.max_health)

        save_player_data(guild_id, player_data)

        # Update the health bar
        health_bar = health_bar(player.stats.health, player.stats.max_health)
        health_emoji = get_emoji('health_emoji')  # Replace with your health emoji

        # Create the embed to reflect the new health status
        embed = discord.Embed(
            title="Heal Tent",
            description=f"You feel rejuvenated!",
            color=discord.Color.blue()
        )

        tent_url = generate_urls("Citadel", "Heal")
        embed.set_thumbnail(url=tent_url)
        embed.set_footer(text=f"{health_emoji} Health: {health_bar} {player.stats.health}/{player.stats.max_health}")

        # Disable the button if health is full
        if player.stats.health >= player.stats.max_health:
            button.disabled = True
            embed.description += "\n\nYou are fully healed!"

        await interaction.response.edit_message(embed=embed, view=self)

