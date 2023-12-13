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

        from probabilities import tent_health
        # Define the health_bar function
        def health_bar(current, max_health):
            bar_length = 20
            health_percentage = current / max_health
            filled_length = round(bar_length * health_percentage)
            return '◼' * filled_length + '◻' * (bar_length - filled_length)

        # Load player data
        author_id = str(interaction.user.id)
        guild_id = self.ctx.guild.id
        player_data = load_player_data(guild_id)
        player = Exemplar(
            player_data[author_id]["exemplar"],
            player_data[author_id]["stats"],
            player_data[author_id]["inventory"]
        )

        # Heal the player by tent_health HP, up to the maximum health
        previous_health = player.stats.health
        player.stats.health = min(player.stats.health + tent_health, player.stats.max_health)
        actual_healed_amount = player.stats.health - previous_health

        # Update the player_data with the modified player stats
        player_data[author_id]["stats"] = player.stats

        # Save the updated player data
        save_player_data(guild_id, player_data)

        # Generate and display the updated health bar
        updated_health_bar = health_bar(player.stats.health, player.stats.max_health)
        health_emoji = get_emoji('heart_emoji')

        # Create the updated embed
        health_gained_text = f"(+{actual_healed_amount})" if actual_healed_amount > 0 else ""
        embed_description = f"You feel rejuvenated! {health_gained_text}\n{health_emoji} Health: {updated_health_bar} {player.stats.health}/{player.stats.max_health}"
        if player.stats.health >= player.stats.max_health:
            button.disabled = True
            embed_description += "\n\nYou are fully healed!"

        embed = discord.Embed(
            title="Heal Tent",
            description=embed_description,
            color=discord.Color.blue()
        )
        tent_url = generate_urls('Citadel', 'Heal')
        embed.set_image(url=tent_url)

        await interaction.response.edit_message(embed=embed, view=self)