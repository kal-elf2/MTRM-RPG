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
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        self.player, self.player_data = await refresh_player_from_data(interaction)

        if self.player_data["location"] != "citadel":
            await self.not_in_citadel_response(interaction)
            return

        def health_bar(current, max_health):
            bar_length = 20
            health_percentage = current / max_health
            filled_length = int(round(bar_length * health_percentage))
            return '◼' * filled_length + '◻' * (bar_length - filled_length)

        previous_health = self.player.stats.health
        heal_amount = int(get_server_setting(self.guild_id, 'tent_health'))
        self.player.stats.health = int(min(self.player.stats.health + heal_amount, self.player.stats.max_health))
        actual_healed_amount = self.player.stats.health - previous_health
        self.player_data["stats"] = self.player.stats
        save_player_data(self.guild_id, self.author_id, self.player_data)
        updated_health_bar = health_bar(self.player.stats.health, self.player.stats.max_health)
        health_emoji = get_emoji('heart_emoji')

        embed_description = ""
        if self.player.stats.health >= self.player.stats.max_health:
            button.disabled = True
            embed_description = f"**You are fully healed!**\n\n{health_emoji} Health: {updated_health_bar} {self.player.stats.health}/{self.player.stats.max_health}"
        else:
            button.disabled = False
            health_gained_text = f"(+{actual_healed_amount})"
            embed_description = f"**You feel rejuvenated!** {health_gained_text}\n\n{health_emoji} Health: {updated_health_bar} {self.player.stats.health}/{self.player.stats.max_health}"

        embed = discord.Embed(title="Heal Tent", description=embed_description, color=discord.Color.blue())
        tent_url = generate_urls('Citadel', 'Heal')
        embed.set_image(url=tent_url)

        await interaction.response.edit_message(embed=embed, view=self)

        if self.player.stats.health < self.player.stats.max_health:
            # Wait for 1.5 seconds then re-enable the button if not fully healed
            await asyncio.sleep(1.5)
            button.disabled = False
            await interaction.edit_original_response(view=self)
