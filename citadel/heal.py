import discord
from images.urls import generate_urls
from utils import save_player_data, CommonResponses, refresh_player_from_data, get_server_setting
from emojis import get_emoji
import asyncio

class HealTentButton(discord.ui.View, CommonResponses):
    def __init__(self, ctx, player, player_data, author_id, guild_id):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.player = player
        self.player_data = player_data
        self.author_id = author_id
        self.guild_id = guild_id

    @discord.ui.button(label="Heal", custom_id="heal", style=discord.ButtonStyle.blurple)
    async def heal(self, button, interaction):

        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player object from the latest player data
        self.player, self.player_data = await refresh_player_from_data(interaction)

        # Check if the player is not in the citadel
        if self.player_data["location"] != "citadel":
            await self.not_in_citadel_response(interaction)
            return

        # Define the health_bar function
        def health_bar(current, max_health):
            bar_length = 20
            health_percentage = current / max_health
            filled_length = round(bar_length * health_percentage)
            return '◼' * filled_length + '◻' * (bar_length - filled_length)

        # Heal the player
        previous_health = self.player.stats.health
        self.player.stats.health = min(self.player.stats.health + get_server_setting(interaction.guild_id, 'tent_health'), self.player.stats.max_health)
        actual_healed_amount = self.player.stats.health - previous_health

        # Update the player_data with the modified player stats
        self.player_data["stats"] = self.player.stats

        # Save the updated player data
        save_player_data(self.guild_id, self.author_id, self.player_data)

        # Generate and display the updated health bar
        updated_health_bar = health_bar(self.player.stats.health, self.player.stats.max_health)
        health_emoji = get_emoji('heart_emoji')

        # Determine the message based on whether the player is fully healed or not
        if self.player.stats.health >= self.player.stats.max_health:
            button.disabled = True
            embed_description = f"**You are fully healed!**\n\n{health_emoji} Health: {updated_health_bar} {self.player.stats.health}/{self.player.stats.max_health}"
        else:
            health_gained_text = f"(+{actual_healed_amount})"
            embed_description = f"**You feel rejuvenated!** {health_gained_text}\n\n{health_emoji} Health: {updated_health_bar} {self.player.stats.health}/{self.player.stats.max_health}"

        # Create and configure the embed
        embed = discord.Embed(
            title="Heal Tent",
            description=embed_description,
            color=discord.Color.blue()
        )
        tent_url = generate_urls('Citadel', 'Heal')
        embed.set_image(url=tent_url)

        # Disable the button
        button.disabled = True
        # Reflect the button's disabled state in the response
        await interaction.response.edit_message(embed=embed, view=self)

        # Wait for 1.5 seconds
        await asyncio.sleep(1.5)

        # Re-enable the button
        button.disabled = False
        # You might need to update the message again to reflect the re-enabled state
        await interaction.edit_original_response(view=self)