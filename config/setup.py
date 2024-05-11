from discord import Embed
import discord
from discord import ButtonStyle
from discord.ui import View
import datetime
from discord.ext import commands
from utils import load_player_data, save_player_data, CommonResponses, refresh_player_from_data, save_server_settings, load_server_settings
from images.urls import generate_urls
from emojis import get_emoji
from probabilities import default_settings

class PrivateGameView(View, CommonResponses):
    def __init__(self, user_id: str, author_id):
        super().__init__()
        self.user_id = user_id
        self.author_id = author_id

    @discord.ui.button(label="Secret Cove", style=ButtonStyle.blurple, emoji="🔒", custom_id="private_play")
    async def play_privately(self, button, interaction):

        if interaction.user.id != self.author_id:
            return await self.nero_unauthorized_user_response(interaction)

        # Retrieve active threads in the channel that are not archived and match the naming convention
        existing_threads = [t for t in interaction.channel.threads if
                            t.name.startswith(f"{interaction.user.display_name}-private") and not t.archived]

        if existing_threads:
            thread = existing_threads[0]  # Get the first active thread
            # Ensure the user is added back with permissions to read and send messages
            await thread.add_user(interaction.user)
            button.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(
                f"You already have an active private session here: {thread.mention}. You've been added back to it, so feel free to continue your adventure!", ephemeral=True)
            return

        # Generate a unique identifier using the current timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        thread_name = f"{interaction.user.display_name}-private-{timestamp}"

        # Create a private thread in the channel the command was used
        thread = await interaction.channel.create_thread(
            name=thread_name,
            auto_archive_duration=4320,  # 3 days
            type=discord.ChannelType.private_thread
        )
        # Add the user to the thread explicitly, even if they're the creator, to handle any permissions issues preemptively
        await thread.add_user(interaction.user)

        # Create a custom embed message to welcome the user to their private game session
        welcome_embed = discord.Embed(
            title="Welcome to Your Secret Cove!",
            description=f"Ahoy, {interaction.user.mention}! Yer private game session is ready.",
            color=discord.Color.dark_gold()
        )
        welcome_embed.set_image(
            url=generate_urls("nero", "welcome"))

        # Send the embed to the newly created thread
        await thread.send(embed=welcome_embed)

        # Update the button to be disabled and update the original message
        button.disabled = True
        await interaction.response.edit_message(view=self)  # This updates the message if it's the first response

        # Inform the user with a follow-up message in the main channel, if necessary
        await interaction.followup.send(f"Private thread created: {thread.mention}", ephemeral=True)

        # Stop the view to prevent further interactions
        self.stop()

class TeleportModal(discord.ui.Modal):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(title="Teleport Player", *args, **kwargs)
        self.bot = bot

        self.discord_id = discord.ui.InputText(
            label="Player's Discord ID",
            placeholder="Enter the Discord ID here...",
            style=discord.InputTextStyle.short
        )
        self.add_item(self.discord_id)

    async def callback(self, interaction: discord.Interaction):
        discord_id = self.discord_id.value.strip()
        if not discord_id.isdigit():
            await interaction.response.send_message("Invalid ID: IDs must be numeric.", ephemeral=True)
            return

        player_data = load_player_data(interaction.guild_id, discord_id)
        if player_data is None:
            await interaction.response.send_message("No player data found for the given ID.", ephemeral=True)
            return

        user = await self.bot.fetch_user(discord_id)  # Fetch the user object using the discord ID
        if user is None:
            await interaction.response.send_message("No user found with the given Discord ID.", ephemeral=True)
            return

        player_data["location"] = None
        save_player_data(interaction.guild_id, discord_id, player_data)

        # Use user.mention to mention the user in the response
        await interaction.response.send_message(f"{user.mention} has been teleported to neutral ground.", ephemeral=True)

class SettingsView(View):
    def __init__(self, guild_id):
        super().__init__()
        self.add_item(SettingsSelect(guild_id))

def get_formatted_name(setting_name):
    emoji_key = emoji_map.get(setting_name, '')
    if isinstance(emoji_key, str) and emoji_key not in ['💀', '🎯', '✨', '🏕️']:
        # If the emoji key is a string that indicates it needs resolving
        emoji = get_emoji(emoji_key)
    else:
        # Directly use the emoji from the map
        emoji = emoji_key
    name_parts = setting_name.split('_')
    readable_name = ' '.join(word.capitalize() for word in name_parts)
    return f"{emoji} **{readable_name}**"


emoji_map = {
    "mtrm_drop_percent": 'Materium',
    "herb_drop_percent": 'Ranarr',
    "potion_drop_percent": 'Super Stamina Potion',
    "weapon_specialty_bonus": 'Voltaic Sword',
    "death_penalty": '💀',
    "critical_hit_chance": '🎯',
    "critical_hit_multiplier": '✨',
    "tent_health": '🏕️',
    "stonebreaker_percent": 'Stonebreaker',
    "woodcleaver_percent": 'Woodcleaver',
    "loothaven_percent": 'Loothaven',
    "ironhide_percent": 'Ironhide'
}

class SettingsModal(discord.ui.Modal):
    def __init__(self, setting_name, current_value, default_value, valid_range, *args, **kwargs):
        super().__init__(title=f'Modify {setting_name.capitalize()}')
        self.setting_name = setting_name
        self.valid_range = valid_range
        self.add_item(discord.ui.InputText(
            label=f'New Value (Valid range: {valid_range[0]} to {valid_range[1]})',
            placeholder=f'Current: {current_value} (Default: {default_value})'
        ))

    async def callback(self, interaction: discord.Interaction):
        new_value = self.children[0].value
        settings_data = load_server_settings(interaction.guild_id)
        if settings_data is not None:
            try:
                value = float(new_value)
                if not (self.valid_range[0] <= value <= self.valid_range[1]):
                    raise ValueError(f"Please enter a value between {self.valid_range[0]} and {self.valid_range[1]}.")
                settings_data[self.setting_name] = value
                save_server_settings(interaction.guild_id, settings_data)
                formatted_name = get_formatted_name(self.setting_name)
                await interaction.response.send_message(f"{formatted_name} updated to {new_value}", ephemeral=True)
            except ValueError as e:
                await interaction.response.send_message(str(e), ephemeral=True)
        else:
            await interaction.response.send_message("Failed to update settings. Settings data could not be loaded.",
                                                    ephemeral=True)

class SettingsSelect(discord.ui.Select):
    def __init__(self, guild_id):
        # Fetch the settings for the specific guild
        settings_data = load_server_settings(guild_id)

        options = [
            discord.SelectOption(
                label=f"MTRM Drop Percent - Default: {default_settings['mtrm_drop_percent']}",
                description=f"Chance of MTRM loot drop - Current: {settings_data.get('mtrm_drop_percent')}",
                value="mtrm_drop_percent",
                emoji=get_emoji('Materium')
            ),
            discord.SelectOption(
                label=f"Herb Drop Percent - Default: {default_settings['herb_drop_percent']}",
                description=f"Chance of Herb loot drop - Current: {settings_data.get('herb_drop_percent')}",
                value="herb_drop_percent",
                emoji=get_emoji('Ranarr')
            ),
            discord.SelectOption(
                label=f"Potion Drop Percent - Default: {default_settings['potion_drop_percent']}",
                description=f"Chance of Potion loot drop - Current: {settings_data.get('potion_drop_percent')}",
                value="potion_drop_percent",
                emoji=get_emoji('Super Stamina Potion')
            ),
            discord.SelectOption(
                label=f"Weapon Specialty Bonus - Default: {default_settings['weapon_specialty_bonus']}",
                description=f"Bonus to damage for weapon specialty - Current: {settings_data.get('weapon_specialty_bonus')}",
                value="weapon_specialty_bonus",
                emoji=get_emoji('Voltaic Sword')
            ),
            discord.SelectOption(
                label=f"Death Penalty - Default: {default_settings['death_penalty']}",
                description=f"Stat reduction upon death - Current: {settings_data.get('death_penalty')}",
                value="death_penalty",
                emoji='💀'
            ),
            discord.SelectOption(
                label=f"Critical Hit Chance - Default: {default_settings['critical_hit_chance']}",
                description=f"Chance of a critical hit - Current: {settings_data.get('critical_hit_chance')}",
                value="critical_hit_chance",
                emoji='🎯'
            ),
            discord.SelectOption(
                label=f"Critical Hit Multiplier - Default: {default_settings['critical_hit_multiplier']}",
                description=f"Critical hit damage multiplier - Current: {settings_data.get('critical_hit_multiplier')}",
                value="critical_hit_multiplier",
                emoji='✨'
            ),
            discord.SelectOption(
                label=f"Tent Health - Default: {default_settings['tent_health']}",
                description=f"HP per heal from tent - Current: {settings_data.get('tent_health')}",
                value="tent_health",
                emoji='🏕️'
            ),
            discord.SelectOption(
                label=f"Stonebreaker Percent - Default: {default_settings['stonebreaker_percent']}",
                description=f"Increase mining success rate - Current: {settings_data.get('stonebreaker_percent')}",
                value="stonebreaker_percent",
                emoji=get_emoji('Stonebreaker')
            ),
            discord.SelectOption(
                label=f"Woodcleaver Percent - Default: {default_settings['woodcleaver_percent']}",
                description=f"Increase woodcutting success rate - Current: {settings_data.get('woodcleaver_percent')}",
                value="woodcleaver_percent",
                emoji=get_emoji('Woodcleaver')
            ),
            discord.SelectOption(
                label=f"Loothaven Percent - Default: {default_settings['loothaven_percent']}",
                description=f"Doubles loot drops and drop rates - Current: {settings_data.get('loothaven_percent')}",
                value="loothaven_percent",
                emoji=get_emoji('Loothaven')
            ),
            discord.SelectOption(
                label=f"Ironhide Percent - Default: {default_settings['ironhide_percent']}",
                description=f"Increase evade chance in battle - Current: {settings_data.get('ironhide_percent')}",
                value="ironhide_percent",
                emoji=get_emoji('Ironhide')
            )

        ]
        super().__init__(placeholder="Select a setting to modify", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_setting = self.values[0]
        settings_data = load_server_settings(interaction.guild_id)
        if settings_data:
            current_value = settings_data.get(selected_setting)
            default_value = default_settings.get(selected_setting)
            valid_range = valid_ranges.get(selected_setting)
            modal = SettingsModal(setting_name=selected_setting, current_value=current_value, default_value=default_value, valid_range=valid_range)
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message("Error: Unable to retrieve settings.", ephemeral=True)


# Define valid ranges for each setting.
valid_ranges = {
    "mtrm_drop_percent": (0.005, 0.025),
    "herb_drop_percent": (0.025, 0.25),
    "potion_drop_percent": (0.05, 0.15),
    "weapon_specialty_bonus": (0.025, 0.10),
    "death_penalty": (0.01, 0.10),
    "critical_hit_chance": (0.025, 0.15),
    "critical_hit_multiplier": (1.25, 2.0),
    "tent_health": (25, 100),
    "stonebreaker_percent": (0.05, 0.25),
    "woodcleaver_percent": (0.05, 0.25),
    "loothaven_percent": (0.05, 0.25),
    "ironhide_percent": (0.05, 0.25)
}

class SetupCog(commands.Cog, CommonResponses):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Start a private game session.")
    async def private(self, ctx):

        # Refresh player object from the latest player data
        _, player_data = await refresh_player_from_data(ctx)

        if not player_data:
            embed = Embed(title="Captain Ner0",
                          description="Arr! What be this? No record of yer adventures? Start a new game with `/newgame` before I make ye walk the plank.",
                          color=discord.Color.dark_gold())
            embed.set_thumbnail(url=generate_urls("nero", "confused"))
            await ctx.respond(embed=embed, ephemeral=True)
            return

        # Determine the image and the specific part of the message based on the exemplar selection
        if player_data["exemplar"] == "elf":
            image_url = generate_urls("nero", "laugh")
            description = (f"Of course ye want to play privately, {ctx.user.mention}. Yer a *bloody elf*! "
                           "Skulking about like a leaf in the wind. "
                           "Well, if ye insist on hiding, click the button below. "
                           "Let's see if ye can prove yer worth away from prying eyes!")
        else:
            image_url = generate_urls("nero", "laugh")
            description = (f"Arr! Playing privately, are we, {ctx.user.mention}? What's the matter, scared of a little company? "
                           "Ye're acting just like those elf cowards. "
                           "Well, if ye insist on hiding from prying eyes, click the button below. ")

        # Create the ephemeral embed message asking if they want to create a private thread
        embed = Embed(
            title="Captain Ner0's Private Invitation",
            description=description,
            color=discord.Color.dark_gold()
        )
        embed.set_thumbnail(url=image_url)

        # Instantiate the view with the ID of the user who invoked the command
        view = PrivateGameView(user_id=ctx.user.id, author_id=ctx.user.id)

        # Send the ephemeral message with the button to the user
        await ctx.respond(embed=embed, view=view, ephemeral=False)

    @commands.slash_command(name="teleport", description="Teleport a player to a neutral location.")
    @commands.has_permissions(administrator=True)
    async def teleport(self, ctx):
        await ctx.send_modal(TeleportModal(self.bot))

    @commands.slash_command(name="settings", description="Manage server settings.")
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        """Sends a select menu to change settings."""
        view = SettingsView(ctx.guild.id)
        await ctx.respond("Change game difficulty settings:", view=view, ephemeral=True)

    @commands.slash_command(name="resetsettings", description="Reset all game settings to their default values.")
    @commands.has_permissions(administrator=True)
    async def reset_settings(self, ctx):
        class ResetSettingsConfirmation(discord.ui.View):
            def __init__(self):
                super().__init__()

            @discord.ui.button(label="Confirm", style=discord.ButtonStyle.blurple)
            async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
                # Disable all buttons
                for item in self.children:
                    if isinstance(item, discord.ui.Button):
                        item.disabled = True

                # Acknowledge the interaction with updated buttons
                await interaction.response.edit_message(view=self)

                # Handle the confirmation logic
                # Load settings, check, and reset to defaults as needed
                settings_data = load_server_settings(interaction.guild_id)
                if settings_data is None:
                    await interaction.followup.send("Settings file could not be found or loaded.", ephemeral=True)
                else:
                    save_server_settings(interaction.guild_id, default_settings)
                    await interaction.followup.send("All settings have been reset to default values.", ephemeral=True)
                self.stop()

            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
            async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
                # Disable all buttons
                for item in self.children:
                    if isinstance(item, discord.ui.Button):
                        item.disabled = True

                # Acknowledge the interaction with updated buttons
                await interaction.response.edit_message(view=self)

                # Send a cancellation message
                await interaction.followup.send("Settings reset cancelled.", ephemeral=True)
                self.stop()

        confirmation_view = ResetSettingsConfirmation()
        await ctx.respond("Are you sure you want to reset all settings to their default values?",
                          view=confirmation_view, ephemeral=True)

        # Wait for user interaction
        await confirmation_view.wait()

def setup(bot):
    bot.add_cog(SetupCog(bot))