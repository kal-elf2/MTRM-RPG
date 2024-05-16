import discord
import random
import asyncio
from utils import save_player_data, CommonResponses, refresh_player_from_data, get_server_setting
from emojis import get_emoji
from images.urls import generate_urls

class Phase3:
    def __init__(self, battle_commands, player_data, user):
        self.battle_commands = battle_commands
        self.player_data = player_data
        self.user = user
        self.battle_ended = False

    async def enter_phase_3(self, interaction):
        # Notify players of the phase transition
        phase_3_notification = discord.Embed(
            title="Entered Phase 3",
            description=(
                "The Kraken is on its last legs! Prepare for its final, desperate attacks!"
            ),
            color=discord.Color.red()
        )
        if self.battle_commands.battle_message:
            await self.battle_commands.battle_message.edit(embed=phase_3_notification)

        # Clear attack messages for Phase 3
        self.battle_commands.phase3_attack_messages = []

        await asyncio.sleep(5)  # Short delay before starting phase 3

    async def update_battle_embed(self):
        await self.battle_commands.battle_message.edit(embed=self.create_phase3_battle_embed())

    def create_phase3_battle_embed(self):
        description = f"**The Kraken's final assault!**\n\n" + "\n".join(self.battle_commands.phase3_attack_messages)
        embed = discord.Embed(title=f"{get_emoji('kraken')} Battle with the Kraken {get_emoji('kraken')}",
                              description=description, color=discord.Color.red())

        kraken_health_bar = self.battle_commands.kraken.health_bar()
        kraken_current_health_formatted = f"{self.battle_commands.kraken.health:,}"
        kraken_max_health_formatted = f"{self.battle_commands.kraken.max_health:,}"

        embed.add_field(name="Kraken's Health",
                        value=f"{get_emoji('heart_emoji')} {kraken_current_health_formatted}/{kraken_max_health_formatted}\n{kraken_health_bar}",
                        inline=False)

        # Ship's health
        mast_health = max(0, self.battle_commands.ship.mast_health)
        hull_health = max(0, self.battle_commands.ship.hull_health)
        helm_health = max(0, self.battle_commands.ship.helm_health)

        embed.add_field(name="Mast Health",
                        value=f"{mast_health}/{self.battle_commands.ship.mast_max_health}",
                        inline=True)
        embed.add_field(name="Hull Health",
                        value=f"{hull_health}/{self.battle_commands.ship.hull_max_health}",
                        inline=True)
        embed.add_field(name="Helm Health",
                        value=f"{helm_health}/{self.battle_commands.ship.helm_max_health}",
                        inline=True)

        embed.set_image(url=generate_urls("nero", "kraken_final"))

        return embed

    async def end_battle(self):
        self.battle_ended = True
        await self.battle_commands.battle_message.edit(view=None)


