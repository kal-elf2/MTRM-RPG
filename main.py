import os
import json
import discord
from discord.ext import commands
from discord.commands import Option
from utils import load_player_data, save_player_data, send_message, CommonResponses
from discord.ui import Select, View
from discord.components import SelectOption
from exemplars.exemplars import Exemplar
from monsters.monster import generate_monster_list, generate_monster_by_name, monster_battle, create_battle_embed, footer_text_for_embed
from discord import Embed
from resources.inventory import Inventory
from stats import ResurrectOptions
from monsters.battle import BattleOptions, LootOptions, SpecialAttackOptions
from emojis import get_emoji
from images.urls import generate_urls

bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())
# Add the cogs to your bot
bot.load_extension("stats")
bot.load_extension("resources.woodcutting")
bot.load_extension("resources.mining")
bot.load_extension("resources.backpack")
bot.load_extension("citadel.buttons")
bot.load_extension("nero.kraken")

guild_data = {}

@bot.event
async def on_ready():
    # await bot.sync_commands()
    print(f'We have logged in as {bot.user}')

@bot.slash_command()
async def setchannel(ctx):
    guild_id = ctx.guild.id

    if guild_id not in guild_data:
        guild_data[guild_id] = {
            "channel_id": ctx.channel.id,
            "player_data": {}
        }

        with open(f'server/player_data_{guild_id}.json', 'w') as f:
            json.dump(guild_data[guild_id]["player_data"], f)
    else:
        guild_data[guild_id]["channel_id"] = ctx.channel.id

    await ctx.respond(f'{ctx.channel.name} Channel set. Please use "newgame" command to start a new adventure! .')

# Exemplars class
class PickExemplars(Select, CommonResponses):

    def __init__(self, author_id):
        self.author_id = author_id
        options = [
            SelectOption(label='Human Exemplar', value='human',
                         emoji=f'{get_emoji("human_exemplar_emoji")}'),
            SelectOption(label='Dwarf Exemplar', value='dwarf',
                         emoji=f'{get_emoji("dwarf_exemplar_emoji")}'),
            SelectOption(label='Orc Exemplar', value='orc',
                         emoji=f'{get_emoji("orc_exemplar_emoji")}'),
            SelectOption(label='Halfling Exemplar', value='halfling',
                         emoji=f'{get_emoji("halfling_exemplar_emoji")}'),
            SelectOption(label='Elf Exemplar', value='elf',
                         emoji=f'{get_emoji("elf_exemplar_emoji")}')
        ]
        super().__init__(placeholder='Exemplar', options=options)
        self.options_dict = {
            'human': 'Human',
            'dwarf': 'Dwarf',
            'orc': 'Orc',
            'halfling': 'Halfling',
            'elf': 'Elf'
        }

    async def callback(self, interaction: discord.Interaction):
        from exemplars.exemplars import DiceStats, MonsterKills, Shipwreck, create_exemplar

        # Ensure the correct user is interacting
        if str(interaction.user.id) != self.author_id:
            await self.unauthorized_user_response(interaction)
            return

        guild_id = interaction.guild.id
        player_id = str(interaction.user.id)

        # Attempt to load the player's data; initialize as empty dict if not found
        player_data = load_player_data(guild_id, player_id) or {}

        # Update the exemplar in player_data
        player_data["exemplar"] = self.values[0]

        # Initialize or reset the character's stats based on the chosen exemplar
        exemplar_instance = create_exemplar(self.values[0])
        player_data["stats"] = {
            "zone_level": exemplar_instance.stats.zone_level,
            "health": exemplar_instance.stats.health,
            "max_health": exemplar_instance.stats.max_health,
            "strength": exemplar_instance.stats.strength,
            "stamina": exemplar_instance.stats.stamina,
            "max_stamina": exemplar_instance.stats.max_stamina,
            "attack": exemplar_instance.stats.attack,
            "damage": exemplar_instance.stats.damage,
            "defense": exemplar_instance.stats.defense,
            "armor": exemplar_instance.stats.armor,
            "combat_level": exemplar_instance.stats.combat_level,
            "combat_experience": exemplar_instance.stats.combat_experience,
            "mining_level": exemplar_instance.stats.mining_level,
            "mining_experience": exemplar_instance.stats.mining_experience,
            "woodcutting_level": exemplar_instance.stats.woodcutting_level,
            "woodcutting_experience": exemplar_instance.stats.woodcutting_experience,
        }
        player_data["dice_stats"] = DiceStats().to_dict()
        player_data["monster_kills"] = MonsterKills().to_dict()
        player_data["inventory"] = Inventory().to_dict()
        player_data["shipwreck"] = Shipwreck().to_dict()
        player_data["location"] = None

        # Generate and send the confirmation message
        embed = self.generate_stats_embed(exemplar_instance)
        view = ConfirmExemplar(exemplar_instance, player_data, player_id, guild_id)
        await interaction.response.send_message(
            f'{interaction.user.mention}, verify your selection of {self.options_dict[self.values[0]]} Exemplar below!',
            embed=embed,
            view=view,
            ephemeral=False)

    @staticmethod
    def generate_stats_embed(exemplar_instance):
        stats = exemplar_instance.stats

        # Assigning weapon specialties based on exemplar
        weapon_specialty = {
            "human": "Sword",
            "elf": "Bow",
            "orc": "Spear",
            "dwarf": "Hammer",
            "halfling": "Sword"
        }
        specialty = weapon_specialty.get(exemplar_instance.name.lower())
        embed = discord.Embed(color=discord.Color.blue(), title=f"{exemplar_instance.name} Exemplar Stats")

        # Assuming there's a function to generate URLs for exemplars' thumbnails
        embed.set_image(url=generate_urls("exemplars", exemplar_instance.name))

        embed.add_field(name="⚔️ Combat Level", value=str(stats.combat_level), inline=True)
        embed.add_field(name=f"{get_emoji('heart_emoji')} Health", value=str(stats.health), inline=True)
        embed.add_field(name=f"{get_emoji('strength_emoji')} Strength", value=str(stats.strength), inline=True)
        embed.add_field(name=f"{get_emoji('stamina_emoji')} Stamina", value=str(stats.stamina), inline=True)
        embed.add_field(name="🗡️ Attack", value=str(stats.attack), inline=True)
        embed.add_field(name="🛡️ Defense", value=str(stats.defense), inline=True)
        embed.add_field(name="⛏️ Mining Level", value=str(stats.mining_level), inline=True)
        embed.add_field(name="🪓 Woodcutting Level", value=str(stats.woodcutting_level), inline=True)
        embed.set_footer(text=f"Weapon bonus: {specialty}")

        return embed


class ConfirmExemplar(discord.ui.View, CommonResponses):
    def __init__(self, exemplar_instance, player_data, author_id, guild_id):
        super().__init__(timeout=None)
        self.exemplar_list = ['Human', 'Dwarf', 'Orc', 'Halfling', 'Elf']  # List of exemplars
        self.current_exemplar_index = self.exemplar_list.index(exemplar_instance.name)  # Get index of current exemplar
        self.player_data = player_data
        self.author_id = author_id
        self.guild_id = guild_id
        self.exemplar_instance = exemplar_instance

        # Initially set up the button layout with the Select button in the middle
        self.setup_buttons()

    def setup_buttons(self):
        # Left arrow button
        self.left_arrow = discord.ui.Button(label='◀', style=discord.ButtonStyle.grey)
        self.left_arrow.callback = self.prev_exemplar

        # Confirm/Select button with dynamic label for the selected exemplar
        current_exemplar = self.exemplar_list[self.current_exemplar_index]
        self.confirm_button = discord.ui.Button(label=f"Select {current_exemplar}", style=discord.ButtonStyle.blurple)
        self.confirm_button.callback = self.confirm_yes

        # Right arrow button
        self.right_arrow = discord.ui.Button(label='▶', style=discord.ButtonStyle.grey)
        self.right_arrow.callback = self.next_exemplar

        # Add items in the specific order to ensure the Select button appears in the middle
        self.add_item(self.left_arrow)
        self.add_item(self.confirm_button)
        self.add_item(self.right_arrow)

    async def prev_exemplar(self, interaction):
        # Ensure only the initiating user can interact
        if str(interaction.user.id) != self.author_id:
            await self.unauthorized_user_response(interaction)
            return

        self.current_exemplar_index = (self.current_exemplar_index - 1) % len(self.exemplar_list)
        await self.update_view(interaction)

    async def next_exemplar(self, interaction):
        # Ensure only the initiating user can interact
        if str(interaction.user.id) != self.author_id:
            await self.unauthorized_user_response(interaction)
            return

        self.current_exemplar_index = (self.current_exemplar_index + 1) % len(self.exemplar_list)
        await self.update_view(interaction)

    async def update_view(self, interaction):
        from exemplars.exemplars import create_exemplar
        # Update the exemplar instance based on the new index
        exemplar_name = self.exemplar_list[self.current_exemplar_index].lower()
        self.exemplar_instance = create_exemplar(exemplar_name)
        self.player_data["exemplar"] = exemplar_name
        # Update stats and the confirm button label to reflect the new selection
        embed = PickExemplars.generate_stats_embed(self.exemplar_instance)
        self.confirm_button.label = f"Select {self.exemplar_list[self.current_exemplar_index]}"
        await interaction.response.edit_message(embed=embed, view=self)

    async def confirm_yes(self, interaction):
        # Ensure only the initiating user can interact
        if str(interaction.user.id) != self.author_id:
            await self.unauthorized_user_response(interaction)
            return

        # Save player data here
        save_player_data(self.guild_id, self.author_id, self.player_data)

        # Disable all buttons
        self.left_arrow.disabled = True
        self.confirm_button.disabled = True
        self.right_arrow.disabled = True

        # Update the message to reflect the selection has been saved and disable the buttons
        await interaction.response.edit_message(
            content=f"Your selection of {self.exemplar_instance.name} Exemplar has been saved!", view=self)

def update_special_attack_options(battle_context):
    # Assuming battle_context has a reference to the special_attack_options_view
    if battle_context.special_attack_options_view:
        battle_context.special_attack_options_view.update_button_states()

@bot.slash_command(description="Battle a monster!")
async def battle(ctx, monster: Option(str, "Pick a monster to battle.", choices=generate_monster_list(), required=True)):
    from monsters.monster import BattleContext
    from utils import CommonResponses

    guild_id = ctx.guild.id
    player_id = str(ctx.author.id)

    # Load only the specific player's data
    player_data = load_player_data(guild_id, player_id)

    if not player_data:
        embed = Embed(title="Captain Ner0",
                      description="Arr! What be this? No record of yer adventures? Start a new game with `/newgame` before I make ye walk the plank.",
                      color=discord.Color.dark_gold())
        embed.set_thumbnail(url=generate_urls("nero", "confused"))
        await ctx.respond(embed=embed, ephemeral=True)
        return

    player = Exemplar(player_data["exemplar"],
                      player_data["stats"],
                      player_data["inventory"])

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

    if player_data["location"] == "kraken":
        await CommonResponses.during_kraken_battle_response(ctx)
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
    battle_options_msg = await ctx.send(view=BattleOptions(ctx, player, battle_context, special_attack_options_view))
    battle_context.battle_options_msg = battle_options_msg

    # Now update the special attack options view with the message references
    special_attack_options_view.battle_options_msg = battle_options_msg
    special_attack_options_view.special_attack_message = special_attack_message

    # Start the monster attack task and receive its outcome
    battle_result = await monster_battle(battle_context)

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

@bot.slash_command(description="Start a new game.")
async def newgame(ctx):
    guild_id = ctx.guild.id
    author_id = str(ctx.author.id)
    player_data = load_player_data(guild_id, author_id)

    class NewGame(discord.ui.View, CommonResponses):
        def __init__(self, author_id=None):
            super().__init__(timeout=None)
            self.author_id = author_id

        @discord.ui.button(label="New Game", custom_id="new_game", style=discord.ButtonStyle.blurple)
        async def button1(self, button, interaction):
            # Check if the user who interacted is the same as the one who initiated the view
            # Inherited from CommonResponses class from utils
            if str(interaction.user.id) != self.author_id:
                await self.unauthorized_user_response(interaction)
                return

            # Explicitly remove and re-initialize player data
            player_data = {
                "exemplar": None,
                "stats": None,
                "inventory": Inventory().to_dict(),
            }
            save_player_data(guild_id, author_id, player_data)

            # Disable the button
            button.disabled = True

            # Update the message with the disabled button
            await interaction.message.edit(view=self)

            # Proceed with the rest of your logic
            view = View()
            view.add_item(PickExemplars(author_id))
            await interaction.response.send_message(
                f"{ctx.author.mention}, your progress has been erased. Please choose your exemplar from the list below.",
                view=view)

    if not player_data:
        view = View()
        view.add_item(PickExemplars(author_id))
        await ctx.respond(f"{ctx.author.mention}, please choose your exemplar from the list below.", view=view)
    else:
        view = NewGame(author_id)
        await ctx.respond(
            f"{ctx.author.mention}, you have a game in progress. Do you want to erase your progress and start a new game?",
            view=view)

@bot.slash_command(description="Visit the cemetery.")
async def cemetery(ctx):
    guild_id = ctx.guild.id
    author_id = str(ctx.author.id)

    player_data = load_player_data(guild_id, author_id)

    if not player_data:
        embed = Embed(title="Captain Ner0",
                      description="Arr! What be this? No record of yer adventures? Start a new game with `/newgame` before I make ye walk the plank.",
                      color=discord.Color.dark_gold())
        embed.set_thumbnail(url=generate_urls("nero", "confused"))
        await ctx.respond(embed=embed, ephemeral=True)
        return

    if player_data["location"] == "kraken":
        await CommonResponses.during_kraken_battle_response(ctx)
        return

    player = Exemplar(player_data["exemplar"],
                      player_data["stats"],
                      player_data["inventory"])

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


