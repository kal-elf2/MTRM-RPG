import os
import json
import discord
from discord.ext import commands
from discord.commands import Option
from utils import save_player_data, send_message, CommonResponses, refresh_player_from_data
from monsters.monster import generate_monster_list, generate_monster_by_name, monster_battle, create_battle_embed, footer_text_for_embed
from discord import Embed
from stats import ResurrectOptions
from monsters.battle import BattleOptions, LootOptions, SpecialAttackOptions
from emojis import get_emoji
from images.urls import generate_urls
from probabilities import default_settings
import logging

bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())
# Add the cogs to the bot
bot.load_extension("stats")
bot.load_extension("resources.woodcutting")
bot.load_extension("resources.mining")
bot.load_extension("resources.backpack")
bot.load_extension("citadel.buttons")
bot.load_extension("nero.kraken")
bot.load_extension("exemplars.newgame")
bot.load_extension("nero.spork")
bot.load_extension("config.setup")

@bot.event
async def on_ready():
    # await bot.sync_commands()
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_guild_join(guild):
    # Overwrites to restrict the bot to operate within this category only
    category_overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }

    # Create a category with specific overwrites
    category = await guild.create_category("☠️ Nero's Landing ☠️", overwrites=category_overwrites)

    # Determine the admin or owner for special permissions
    admin_role = discord.utils.get(guild.roles, name="Admin")
    if admin_role:
        admin_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            admin_role: discord.PermissionOverwrite(read_messages=True)
        }
        recipient = admin_role.mention
    else:
        admin_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            guild.owner: discord.PermissionOverwrite(read_messages=True)
        }
        recipient = guild.owner.mention

    # Create the public 'town-square' channel with modified permissions for @everyone
    town_square_overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=True, use_application_commands=True),  # Allow everyone to read messages and use application commands
        guild.me: discord.PermissionOverwrite(send_messages=True, read_messages=True, use_application_commands=True)  # Bot can send and read messages, and use commands
    }
    town_square_channel = await guild.create_text_channel("town-square", overwrites=town_square_overwrites, category=category)

    # Create the setup channel with more restricted access
    setup_channel = await guild.create_text_channel('Neros Landing Setup', overwrites=admin_overwrites,
                                                    category=category)

    # Send a setup message
    await setup_channel.send(f"Game setup here: {recipient}")

    # Send instructions on setting up channel permissions and pin it
    setup_instructions_embed = discord.Embed(
        title="🛠️ Setup Nero's Landing Bot 🛠️",
        description="To ensure that the Nero's Landing bot operates only within designated channels, please follow the steps below.",
        color=discord.Color.blue()
    )
    setup_instructions_embed.add_field(name="- Step 1: Go to Server Settings",
                                       value="Navigate to the 'Server Settings' of your Discord server.", inline=False)
    setup_instructions_embed.add_field(name="- Step 2: Integrations",
                                       value="Click on 'Integrations' to access bot settings.", inline=False)
    setup_instructions_embed.add_field(name="- Step 3: Select Nero's Landing",
                                       value="Find 'Nero's Landing' in the list of integrations and select it.",
                                       inline=False)
    setup_instructions_embed.add_field(name="- Step 4: Adjust Channel Permissions",
                                       value="Set 'All Channels' to ❌ to deny default access.",
                                       inline=False)
    setup_instructions_embed.add_field(name="- Step 5: Add Game Channels",
                                       value="Add only the channels where you want Nero's Landing to operate by enabling permissions specifically for those channels.",
                                       inline=False)
    setup_instructions_embed.set_footer(
        text="This configuration helps maintain order and ensures the bot functions only where intended.")
    setup_message = await setup_channel.send(embed=setup_instructions_embed)
    await setup_message.pin()

    # Send admin commands embed and pin it
    admin_commands_embed = discord.Embed(
        title="🛡️ Admin Slash Commands 🛡️",
        description="Here are slash commands available exclusively for admins and the server owner:",
        color=discord.Color.gold()
    )
    admin_commands_embed.add_field(name="`/teleport`",
                                   value="Teleport a player to neutral ground. Use this command to resolve issues where a player might get stuck in a game location.",
                                   inline=False)
    admin_commands_embed.add_field(name="`/settings`",
                                   value="Manage game server settings. Adjust cautiously to avoid impacting active gameplay fairness.",
                                   inline=False)
    admin_commands_embed.add_field(name="`/resetsettings`",
                                   value="Reset all game settings to their default values.",
                                   inline=False)
    admin_commands_embed.set_footer(
        text="Use these commands responsibly to manage game settings and player interactions.")
    admin_commands_message = await setup_channel.send(embed=admin_commands_embed)
    await admin_commands_message.pin()

    # Initialize directory and files for server-specific data
    guild_id = guild.id
    directory_path = f'server/{guild_id}'
    player_data_file = f'{directory_path}/player_data.json'
    settings_file = f'{directory_path}/server_settings.json'

    os.makedirs(directory_path, exist_ok=True)

    # Initialize player data
    if not os.path.exists(player_data_file):
        with open(player_data_file, 'w') as f:
            json.dump({}, f)  # Initially empty

    # Initialize server settings if not already set
    if not os.path.exists(settings_file):
        with open(settings_file, 'w') as f:
            json.dump(default_settings, f, indent=4)

    # Create Nero embed for town-square
    nero_embed = discord.Embed(
        title="Captain Nero",
        description="Welcome scallywags! Use `/newgame` to begin your adventure!",
        color=discord.Color.dark_gold()
    )
    nero_embed.set_image(url=generate_urls("nero", "welcome"))

    # Send the embed and pin it
    welcome_message = await town_square_channel.send(embed=nero_embed)
    await welcome_message.pin()

@bot.event
async def on_application_command_error(ctx, error):
    logger = logging.getLogger(__name__)
    # Log the error details for debugging
    logger.error(f"An error occurred: {error}")
    logger.debug(f"Error type: {type(error).__name__}, Error details: {error}")

    if isinstance(error, commands.MissingRole):
        await ctx.respond("You must be an admin to use this command.", ephemeral=True)
    elif isinstance(error, commands.MissingPermissions):
        await ctx.respond("You do not have the necessary permissions to execute this command.", ephemeral=True)
    elif isinstance(error, commands.CommandInvokeError):
        # Handle specific internal command invocation errors
        logger.error(f"Command invocation failed: {error.original}")
        await ctx.respond(f"An internal error occurred: {error.original}", ephemeral=True)
    else:
        # Generic error response if not one of the above
        await ctx.respond(f"An error occurred while processing the command: {error}", ephemeral=True)

def update_special_attack_options(battle_context):
    if battle_context.special_attack_options_view:
        battle_context.special_attack_options_view.update_button_states()

@bot.slash_command(description="Battle a monster!")
async def battle(ctx, monster: Option(str, "Pick a monster to battle.", choices=generate_monster_list(), required=True)):
    from monsters.monster import BattleContext
    from utils import CommonResponses

    guild_id = ctx.guild.id
    player_id = str(ctx.author.id)

    # Refresh player object from the latest player data
    player, player_data = await refresh_player_from_data(ctx)

    if not player_data:
        embed = Embed(title="Captain Ner0",
                      description="Arr! What be this? No record of yer adventures? Start a new game with `/newgame` before I make ye walk the plank.",
                      color=discord.Color.dark_gold())
        embed.set_thumbnail(url=generate_urls("nero", "confused"))
        await ctx.respond(embed=embed, ephemeral=True)
        return

    if player.stats.health <= 0:
        embed = Embed(title="Captain Ner0",
                      description="Ahoy! Ye can't do that ye bloody ghost! Ye must travel to the 🪦 `/cemetery` to reenter the realm of the living.",
                      color=discord.Color.dark_gold())
        embed.set_thumbnail(url=generate_urls("nero", "confused"))
        await ctx.respond(embed=embed, ephemeral=True)
        return

    # Check for battle flag and return if battling
    if player_data["location"] == "citadel":
        await CommonResponses.exit_citadel_response(ctx)
        return

    if player_data["location"] == "kraken" or player_data["location"] == "kraken_battle":
        await CommonResponses.during_kraken_battle_response(ctx)
        return

    # Check for battle flag and return if battling
    if player_data["location"] == "battle":
        await CommonResponses.ongoing_battle_response(ctx)
        return

    player_data["location"] = "battle"
    save_player_data(guild_id, player_id, player_data)

    zone_level = player.stats.zone_level
    monster = generate_monster_by_name(monster, zone_level)

    battle_embed = await send_message(ctx.channel,
                                      create_battle_embed(ctx.author, player, monster, footer_text_for_embed(ctx, monster, player=player), messages= ""))

    await ctx.respond(f"{ctx.author.mention} encounters a {monster.name}")

    def update_special_attack_buttons(context):
        if context.special_attack_options_view:
            context.special_attack_options_view.update_button_states()

    battle_context = BattleContext(ctx, ctx.author, player, monster, battle_embed, zone_level,
                                   update_special_attack_buttons)

    # Create the special attack options view without the messages first
    special_attack_options_view = SpecialAttackOptions(battle_context, None, None)

    # IMPORTANT: Set the special attack options view in the battle context immediately
    battle_context.special_attack_options_view = special_attack_options_view

    # Send the special attack message and store the reference
    special_attack_message = await ctx.send(view=special_attack_options_view)
    battle_context.special_attack_message = special_attack_message

    # Send the battle options message and store the reference
    battle_options_msg = await ctx.send(view=BattleOptions(ctx, player, player_data, battle_context, special_attack_options_view))
    battle_context.battle_options_msg = battle_options_msg

    # Now update the special attack options view with the message references
    special_attack_options_view.battle_options_msg = battle_options_msg
    special_attack_options_view.special_attack_message = special_attack_message

    # Start the monster attack task and receive its outcome
    battle_result = await monster_battle(battle_context, guild_id)

    if battle_result is None:
        # Save the player's current stats
        player_data["stats"]["stamina"] = player.stats.stamina
        player_data["stats"]["combat_level"] = player.stats.combat_level
        player_data["stats"]["combat_experience"] = player.stats.combat_experience
        player_data["stats"]["health"] = player.stats.health
        player_data["stats"]["damage_taken"] = player.stats.damage_taken
        player_data["stats"].update(player.stats.__dict__)

        save_player_data(guild_id, player_id ,player_data)

    # Process battle outcome
    else:
        # Unpack the battle outcome and loot messages
        battle_outcome, loot_messages = battle_result

        if battle_outcome[0]:

            # Define the maximum level for each zone
            zone_max_levels = {
                1: 20,
                2: 40,
                3: 60,
                4: 80,
            }

            # Check if the player is at or above the level cap for their current zone
            if zone_level in zone_max_levels and player.stats.combat_level >= zone_max_levels[zone_level]:
                # Player is at or has exceeded the level cap for their zone; set XP gain to 0
                experience_gained = 0
            else:
                # Player is below the level cap; award XP from the monster
                experience_gained = monster.experience_reward

            loothaven_effect = battle_outcome[5]  # Get the Loothaven effect status
            messages = await player.gain_experience(experience_gained, 'combat', ctx, player)

            # Ensure messages is iterable if it's None
            messages = messages or []

            for msg_embed in messages:
                await ctx.followup.send(embed=msg_embed, ephemeral=False)

            player_data["stats"]["stamina"] = player.stats.stamina
            player_data["stats"]["combat_level"] = player.stats.combat_level
            player_data["stats"]["combat_experience"] = player.stats.combat_experience
            player.stats.damage_taken = 0
            player_data["stats"].update(player.stats.__dict__)

            if player.stats.health <= 0:
                player.stats.health = player.stats.max_health

            # Increment the count of the defeated monster
            player_data["monster_kills"][monster.name] += 1

            # Save the player data after common actions
            save_player_data(guild_id, player_id, player_data)

            # Clear the previous views
            await battle_context.special_attack_message.delete()
            await battle_options_msg.delete()

            loot_view = LootOptions(ctx, player, monster, battle_embed, player_data, player_id, battle_outcome, loot_messages, guild_id, ctx, experience_gained, loothaven_effect, battle_context.rusty_spork_dropped)

            max_cap_message = ""
            if experience_gained == 0:
                max_cap_message = f"\n**(Max XP cap reached for Zone {player.stats.zone_level})**"

            # Construct the embed with the footer
            battle_outcome_embed = create_battle_embed(ctx.user, player, monster, footer_text_for_embed(ctx, monster),
                                                       f"You have **DEFEATED** the {monster.name}!\n"
                                                       f"You dealt **{battle_outcome[1]} damage** to the monster and took **{battle_outcome[2]} damage**. "
                                                       f"You gained {experience_gained} combat XP. {max_cap_message}\n"
                                                       f"\n\u00A0\u00A0")

            await battle_embed.edit(
                embed=battle_outcome_embed,
                view=loot_view
            )

        else:

            # The player is defeated
            player.stats.health = 0  # Set player's health to 0
            player_data["stats"]["health"] = 0

            # Create a new embed with the defeat message
            new_embed = create_battle_embed(ctx.user, player, monster, footer_text = "", messages =

            f"☠️ You have been **DEFEATED** by the **{monster.name}**!\n"
            f"{get_emoji('rip_emoji')} *Your spirit lingers, seeking renewal.* {get_emoji('rip_emoji')}\n\n"
            f"__**Options for Revival:**__\n"
            f"1. Use {get_emoji('Materium')} to revive without penalty.\n"
            f"2. Resurrect with 2.5% penalty to all skills."
            f"**Lose all items in inventory** (Keep equipped items, coppers, MTRM, potions, and charms)"                                )

            # Clear the previous BattleOptions view
            await battle_context.special_attack_message.delete()
            await battle_options_msg.delete()

            # Add the "dead.png" image to the embed
            new_embed.set_image(url=generate_urls("cemetery", "dead"))

            # Update the message with the new embed and view
            await battle_embed.edit(embed=new_embed, view=ResurrectOptions(ctx, player_data, player_id))

    # Clear the battle flag after the battle ends
    player_data["location"] = None
    save_player_data(guild_id, player_id, player_data)


@bot.slash_command(description="Visit the cemetery.")
async def cemetery(ctx):
    author_id = str(ctx.author.id)

    # Refresh player object from the latest player data
    player, player_data = await refresh_player_from_data(ctx)

    if not player_data:
        embed = Embed(title="Captain Ner0",
                      description="Arr! What be this? No record of yer adventures? Start a new game with `/newgame` before I make ye walk the plank.",
                      color=discord.Color.dark_gold())
        embed.set_thumbnail(url=generate_urls("nero", "confused"))
        await ctx.respond(embed=embed, ephemeral=True)
        return

    if player_data["location"] == "kraken" or player_data["location"] == "kraken_battle":
        await CommonResponses.during_kraken_battle_response(ctx)
        return

    cemetery_embed = discord.Embed()

    if player.stats.health <= 0:
        # Player is defeated, present resurrection options
        cemetery_embed.title = "You have been DEFEATED!"
        cemetery_embed.description = (
            f"☠️ Your spirit lingers, seeking renewal. ☠️\n\n"
            f"__**Options for Revival:**__\n"
            f"1. Use {get_emoji('Materium')} to revive without penalty.\n"
            f"2. Resurrect with 2.5% penalty to all skills. "
            f"**Lose all items in inventory** (Keep equipped items, coppers, MTRM, potions, and charms)"
        )
        cemetery_embed.set_image(url=generate_urls("cemetery", "dead"))
        resurrect_view = ResurrectOptions(ctx, player_data, author_id)
        view = resurrect_view

        # Send the message with the appropriate embed and view
        await ctx.respond(embed=cemetery_embed, view=view)

    else:
        # Player is alive, just visiting the cemetery
        cemetery_embed.title = "Cemetery"
        cemetery_embed.description = f"The Cemetery! ARRR! I love this place! It shivers me timbers! All to do here is drink Rum and dance on the graves of the elves! Care to dance, {ctx.author.mention}?\n\nFeel free to pay yer respects, but as ye're still among the livin', there's not much else here for ye, savvy?"
        cemetery_embed.set_image(url=generate_urls("cemetery", "dead"))
        cemetery_embed.set_thumbnail(url=generate_urls("nero", "evil"))
        view = None  # No view necessary for living players

        # Send the message with the appropriate embed and view
        await ctx.respond(embed=cemetery_embed, view=view)

@bot.slash_command(description="View game commands")
async def menu(ctx):
    embed = discord.Embed(
        title="🏴‍☠️ Welcome to the Command Deck 🏴‍☠️",
        description="Ye be ready to navigate through the seas of adventure? Here be the commands at yer disposal:\n\u200B",
        color=discord.Color.dark_gold()
    )
    embed.set_image(url=generate_urls('nero', 'welcome'))

    embed.add_field(name="💀 `/battle` Battle monsters", value="\u200B", inline=True)
    embed.add_field(name="🪓 `/chop` Chop wood", value="\u200B", inline=True)
    embed.add_field(name="⛏️ `/mine` Mine ore", value="\u200B", inline=True)
    embed.add_field(name="🏰 `/citadel` Explore the citadel", value="\u200B", inline=True)
    embed.add_field(name="🎒 `/backpack` Check your inventory", value="\u200B", inline=True)
    embed.add_field(name="🪦 `/cemetery` Revive at the cemetery", value="\u200B", inline=True)
    embed.add_field(name="📈 `/stats` Review your stats", value="\u200B", inline=True)
    embed.add_field(name="🏆 `/leaders` View leaderboard", value="\u200B", inline=True)
    embed.add_field(name="🆕 `/newgame` Begin a new adventure", value="\u200B", inline=True)

    await ctx.respond(embed=embed)

bot.run(os.environ["DISCORD_TOKEN"])