import discord
import random
import asyncio
from utils import save_player_data, CommonResponses, refresh_player_from_data
from emojis import get_emoji
from images.urls import generate_urls

class RepairView(discord.ui.View):
    def __init__(self, phase2, player_data, author_id):
        super().__init__()
        self.phase2 = phase2
        self.player_data = player_data
        self.selected_part = None
        self.author_id = author_id

        # Create part buttons
        self.mast_button = PartButton("Mast", self, user=self.author_id)
        self.hull_button = PartButton("Hull", self, user=self.author_id)
        self.helm_button = PartButton("Helm", self, user=self.author_id)

        # Add part buttons to the view (row 0)
        self.add_item(self.mast_button)
        self.add_item(self.hull_button)
        self.add_item(self.helm_button)

        # Create and add repair and sword buttons, initially disabled (row 1)
        self.repair_button = RepairButton(self, row=1, user=self.author_id)
        self.sword_button = SwordButton(self, row=1, user=self.author_id)
        self.add_item(self.repair_button)
        self.add_item(self.sword_button)

        self.disable_all_buttons()

    def enable_part_button(self, part):
        if part == "Mast":
            self.mast_button.disabled = False
        elif part == "Hull":
            self.hull_button.disabled = False
        elif part == "Helm":
            self.helm_button.disabled = False

        self.enable_repair_button()
        asyncio.create_task(self.phase2.battle_commands.battle_message.edit(view=self))

    def enable_repair_button(self):
        self.repair_button.disabled = False

    def update_part_buttons(self, selected_part):
        self.selected_part = selected_part

        # Update button colors
        if selected_part == "Mast":
            self.mast_button.style = discord.ButtonStyle.blurple
            self.hull_button.style = discord.ButtonStyle.gray
            self.helm_button.style = discord.ButtonStyle.gray
        elif selected_part == "Hull":
            self.hull_button.style = discord.ButtonStyle.blurple
            self.mast_button.style = discord.ButtonStyle.gray
            self.helm_button.style = discord.ButtonStyle.gray
        elif selected_part == "Helm":
            self.helm_button.style = discord.ButtonStyle.blurple
            self.mast_button.style = discord.ButtonStyle.gray
            self.hull_button.style = discord.ButtonStyle.gray

        asyncio.create_task(self.phase2.battle_commands.battle_message.edit(view=self))

    def refresh_view(self):
        self.clear_items()
        # Add part buttons in row 0
        self.add_item(self.mast_button)
        self.add_item(self.hull_button)
        self.add_item(self.helm_button)
        # Add repair and sword buttons in row 1
        self.add_item(self.repair_button)
        self.add_item(self.sword_button)

    def disable_all_buttons(self):
        self.mast_button.disabled = True
        self.hull_button.disabled = True
        self.helm_button.disabled = True
        self.repair_button.disabled = True
        self.sword_button.disabled = True

    def enable_sword_button(self):
        self.sword_button.disabled = False
        asyncio.create_task(self.phase2.battle_commands.battle_message.edit(view=self))

class PartButton(discord.ui.Button, CommonResponses):
    def __init__(self, part, custom_view, user):
        super().__init__(style=discord.ButtonStyle.gray, label=part)
        self.part = part
        self.custom_view = custom_view
        self.user = user

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            await self.nero_unauthorized_user_response(interaction)
            return

        self.custom_view.update_part_buttons(self.part)
        await interaction.response.edit_message(view=self.custom_view)


class RepairButton(discord.ui.Button, CommonResponses):
    def __init__(self, custom_view, row, user):
        poplar_count = custom_view.player_data['shipwreck'].get('Poplar Strip', 0)
        super().__init__(style=discord.ButtonStyle.primary, label=f"{poplar_count}", emoji=get_emoji('Poplar Strip'), disabled=True, row=row)
        self.custom_view = custom_view
        self.user = user

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            await self.nero_unauthorized_user_response(interaction)
            return

        if not self.custom_view.selected_part:
            await interaction.response.send_message("You need to select the part of the ship you need to repair.", ephemeral=True)
            return

        player_data = self.custom_view.player_data
        poplar_count = player_data['shipwreck'].get('Poplar Strip', 0)

        if poplar_count > 0:
            player_data['shipwreck']['Poplar Strip'] -= 1
            self.custom_view.phase2.battle_commands.ship.repair(self.custom_view.selected_part, 1)

            # Update the button label with the new Poplar Strip count
            poplar_count = player_data['shipwreck'].get('Poplar Strip', 0)
            self.label = f"{poplar_count}"
            save_player_data(interaction.guild_id, str(interaction.user.id), player_data)

            if poplar_count == 0:
                await self.custom_view.phase2.end_battle()
                await interaction.response.edit_message(embed=self.custom_view.phase2.create_phase2_battle_embed(),
                                                        view=self.custom_view)
                await asyncio.sleep(2)
                await self.handle_no_poplar_strips(interaction)
            else:
                await interaction.response.edit_message(embed=self.custom_view.phase2.create_phase2_battle_embed(),
                                                        view=self.custom_view)
        else:
            await self.custom_view.phase2.end_battle()
            await interaction.response.edit_message(view=self.custom_view)
            await asyncio.sleep(2)
            await self.handle_no_poplar_strips(interaction)

    async def handle_no_poplar_strips(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer()

        # Refresh player object from the latest player data
        self.custom_view.player, self.custom_view.player_data = await refresh_player_from_data(interaction)
        player_data = self.custom_view.player_data
        player = self.custom_view.player

        citadel_names = ["Sun", "Moon", "Earth", "Wind", "Stars"]

        # Colors for each zone
        color_mapping = {
            1: 0x969696,
            2: 0x15ce00,
            3: 0x0096f1,
            4: 0x9900ff,
            5: 0xfebd0d
        }

        if player.stats.zone_level < 5:
            # Advance to the next zone
            player.stats.zone_level += 1
            player_data["stats"]["zone_level"] = player.stats.zone_level

            embed_color = color_mapping.get(player.stats.zone_level)
            new_zone_index = player.stats.zone_level - 1  # Adjust for 0-based indexing

            # Determine citadel name based on the new zone level
            citadel_name = citadel_names[new_zone_index]

            message_title = "We Had to Flee!"
            message_description = (
                f"Arrr, {interaction.user.mention}! Ye ran out of {get_emoji('Poplar Strip')}Poplar Strips! \n\n"
                "That monstrous Kraken nearly had us in its clutches. Luckily this citadel was here when we needed it.\n\n"
                "I'll be seeking out a grander vessel to hold more powder and plunder. Ye best start honing yer skills and pillaging for loot. "
                "Mark me words, the beasts lurking in these waters be ***far deadlier*** than any we've crossed swords with before. Keep a weather eye on the horizon and ready yer cutlass..."
                f"\n\n### Welcome to Zone {player.stats.zone_level}:\n## The Citadel of the {citadel_name}"
            )
            player_data['shipwreck']['Poplar Strip'] = 0
            player_data['shipwreck']['Cannonball'] = 0

        else:
            # Stay in zone 5
            message_title = "A Narrow Escape!"
            message_description = (
                f"Ye ran out of {get_emoji('Poplar Strip')}Poplar Strips {interaction.user.mention}!\n\nI could tell we weren't going to make it so I turned her back around "
                "before we got lost to the sea... try bringing more Poplar Strips next time.\n\n"
                "I'll start repairing the ship. Come back and see me at the **Jolly Roger** when yer ready."
            )
            embed_color = color_mapping.get(player.stats.zone_level)
            new_zone_index = player.stats.zone_level - 1  # Adjust for 0-based indexing
            citadel_name = citadel_names[new_zone_index]

        player_data["location"] = None

        # Update the player data and save
        save_player_data(interaction.guild_id, str(interaction.user.id), player_data)

        # Send Nero's message
        embed = discord.Embed(
            title=message_title,
            description=message_description,
            color=embed_color
        )
        # Set the image to the citadel they are now in
        embed.set_image(url=generate_urls("Citadel", citadel_name))
        await interaction.followup.send(embed=embed, ephemeral=False)

class SwordButton(discord.ui.Button, CommonResponses):
    def __init__(self, custom_view, row, user):
        super().__init__(style=discord.ButtonStyle.secondary, emoji=get_emoji('Voltaic Sword'), row=row)
        self.custom_view = custom_view
        self.user = user

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            await self.nero_unauthorized_user_response(interaction)
            return
        # Implement the logic for when the player uses the sword to attack the Kraken
        await interaction.response.send_message("You used the sword to attack the Kraken!", ephemeral=True)

class Phase2:
    def __init__(self, battle_commands, player_data, user):
        self.battle_commands = battle_commands
        self.player_data = player_data
        self.custom_view = None
        self.attack_messages = []
        self.user = user
        self.battle_ended = False

    async def enter_phase_2(self):
        # Remove the views from Phase 1
        if hasattr(self.battle_commands, 'steering_view_message'):
            await self.battle_commands.steering_view_message.delete()
        if hasattr(self.battle_commands, 'aiming_view_message'):
            await self.battle_commands.aiming_view_message.delete()

        # Notify players of the phase transition
        phase_2_notification = discord.Embed(
            title="The Kraken's Fury Unleashed!",
            description=(
                "Arrr, matey! She be headed right for us! Prepare yerself for a direct assault!"
                f"\n### {get_emoji('Poplar Strip')} **REPAIR** any damage to the ship.\n\n### {get_emoji('Voltaic Sword')} **ATTACK** her with yer sword!"
            ),
            color=discord.Color.red()
        )
        phase_2_notification.set_image(url=generate_urls("nero", "kraken"))

        if self.battle_commands.battle_message:
            await self.battle_commands.battle_message.edit(embed=phase_2_notification)

        await asyncio.sleep(5)  # Short delay before starting phase 2

        # Send the new repair and attack view
        self.custom_view = RepairView(self, self.player_data, self.user)
        await self.battle_commands.battle_message.edit(view=self.custom_view)

        # Start the Kraken attack loop
        asyncio.create_task(self.kraken_attack_loop())

    async def kraken_attack_loop(self):
        while self.battle_commands.kraken.is_alive() and self.battle_commands.ship.is_sailable() and not self.battle_ended:
            await asyncio.sleep(random.randint(3, 6))  # Random delay before Kraken attacks

            if self.battle_commands.kraken_visible and not self.battle_ended:
                part, damage = self.battle_commands.kraken.tentacle_slam(self.battle_commands.ship)
                attack_message = f"The Kraken attacks the **{part}**, dealing **{damage} damage**!"
                self.add_attack_message(attack_message)

                self.custom_view.enable_part_button(part)
                self.custom_view.enable_sword_button()
                self.custom_view.enable_repair_button()

                # Update the ship's health part and ensure 0 is displayed if it reaches 0
                if self.battle_commands.ship.get_health(part) <= 0:
                    await self.battle_commands.battle_message.edit(embed=self.create_phase2_battle_embed())
                    await self.handle_ship_destruction(part)
                    return

                await self.battle_commands.battle_message.edit(embed=self.create_phase2_battle_embed())

    def add_attack_message(self, new_message):
        if len(self.attack_messages) >= 5:
            self.attack_messages.pop(0)
        self.attack_messages.append(new_message)

    def create_phase2_battle_embed(self):
        description = f"**The Kraken is attacking your ship!**\n\n" + "\n".join(self.attack_messages)
        embed = discord.Embed(title=f"{get_emoji('kraken')} Battle with the Kraken {get_emoji('kraken')}",
                              description=description, color=discord.Color.red())

        # Kraken's health bar
        kraken_health_bar = self.battle_commands.kraken.health_bar()
        kraken_current_health_formatted = f"{self.battle_commands.kraken.health:,}"
        kraken_max_health_formatted = f"{self.battle_commands.kraken.max_health:,}"

        embed.add_field(name="Kraken's Health",
                        value=f"{get_emoji('heart_emoji')} {kraken_current_health_formatted}/{kraken_max_health_formatted}\n{kraken_health_bar}",
                        inline=False)

        # Ship's health - Ensure 0 health is displayed correctly
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

        embed.set_image(url=generate_urls("nero", "kraken"))

        return embed

    async def end_battle(self):
        self.battle_ended = True
        self.custom_view.disable_all_buttons()
        await self.battle_commands.battle_message.edit(view=self.custom_view)

    async def handle_ship_destruction(self, part):
        await self.end_battle()

        citadel_names = ["Sun", "Moon", "Earth", "Wind", "Stars"]
        zone_level = self.player_data["stats"]["zone_level"]
        if zone_level < 5:
            # Advance to the next zone
            zone_level += 1
            self.player_data["stats"]["zone_level"] = zone_level
            citadel_name = citadel_names[zone_level - 1]

            message_title = "We Had to Flee!"
            message_description = (
                f"Arrr, {self.user.mention}! The ship's {part} has been destroyed!\n\n"
                "That monstrous Kraken nearly had us in its clutches. Just before we lost control, I managed to point her in the right direction and we made it to safety at this citadel.\n\n"
                "I'll be seeking out a grander vessel to hold more powder and plunder. Ye best start honing yer skills and pillaging for loot. "
                "Mark me words, the beasts lurking in these waters be ***far deadlier*** than any we've crossed swords with before. Keep a weather eye on the horizon and ready yer cutlass..."
                f"\n\n### Welcome to Zone {zone_level}:\n## The Citadel of the {citadel_name}"
            )

        else:
            citadel_name = citadel_names[zone_level - 1]
            message_title = "A Narrow Escape!"
            message_description = (
                f"Arrr, {self.user.mention}! The ship's {part} has been destroyed!\n\n"
                "We barely escaped... I could tell we weren't going to make it, so I turned her back around before we got lost to the sea. Try bringing more resources next time.\n\n"
                "I'll start repairing the ship. Come back and see me at the **Jolly Roger** when yer ready."
            )

        self.player_data["location"] = None
        save_player_data(self.battle_commands.guild_id, str(self.user.id), self.player_data)

        embed = discord.Embed(title=message_title, description=message_description, color=0xff0000)
        embed.set_image(url=generate_urls("Citadel", citadel_name))
        await asyncio.sleep(2)
        await self.battle_commands.battle_message.channel.send(embed=embed)