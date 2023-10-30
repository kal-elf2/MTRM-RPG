import os
import json
import discord
from discord.ext import commands
from discord.commands import Option
from utils import load_player_data, save_player_data, send_message
from discord.ui import Select, View
from discord.components import SelectOption
from zones.zone import Zone
from exemplars.exemplars import create_exemplar, Exemplar
from monsters.monster import generate_monster_list, generate_monster_by_name, monster_battle, create_battle_embed, footer_text_for_embed
from discord import Embed
from resources.inventory import Inventory
from stats import ResurrectOptions
from monsters.battle import BattleOptions, LootOptions
from emojis import get_emoji
from images.urls import generate_urls

bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())
# Add the cog to your bot
bot.load_extension("stats")
bot.load_extension("resources.woodcutting")
bot.load_extension("resources.mining")
bot.load_extension("resources.backpack")
bot.load_extension("citadel.buttons")

guild_data = {}

@bot.event
async def on_ready():
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
class PickExemplars(Select):

    def __init__(self):
        options = [
            SelectOption(label='Human Exemplars', value='human',
                         emoji=f'{get_emoji("human_exemplar_emoji")}'),
            SelectOption(label='Dwarf Exemplars', value='dwarf',
                         emoji=f'{get_emoji("dwarf_exemplar_emoji")}'),
            SelectOption(label='Orc Exemplars', value='orc',
                         emoji=f'{get_emoji("orc_exemplar_emoji")}'),
            SelectOption(label='Halfling Exemplars', value='halfling',
                         emoji=f'{get_emoji("halfling_exemplar_emoji")}'),
            SelectOption(label='Elf Exemplars', value='elf',
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
        author_id = interaction.user.id
        guild_id = interaction.guild.id
        player_data = load_player_data(guild_id)

        if str(author_id) not in player_data:
            player_data[str(author_id)] = {}

        # Update the exemplar in player_data
        player_data[str(author_id)]["exemplar"] = self.values[0]

        # Initialize the character's stats
        exemplar_instance = create_exemplar(self.values[0])
        player_data[str(author_id)]["stats"] = {
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

        player_data[str(author_id)]["inventory"] = Inventory().to_dict()
        # Set 'in_battle' field to False
        player_data[str(author_id)]["in_battle"] = False

        # Generate embed with exemplar stats
        embed = self.generate_stats_embed(exemplar_instance)

        # Create the confirmation view with two buttons
        view = ConfirmExemplar(exemplar_instance, player_data, str(author_id), guild_id)

        await interaction.response.send_message(
            f'{interaction.user.mention}, verify your selection of {self.options_dict[self.values[0]]} Exemplar below!',
            embed=embed,
            view=view,
            ephemeral=False)

    def generate_stats_embed(self, exemplar_instance):
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

class ConfirmExemplar(discord.ui.View):
    def __init__(self, exemplar_instance, player_data, author_id, guild_id):
        super().__init__(timeout=None)
        self.exemplar_instance = exemplar_instance
        self.player_data = player_data
        self.author_id = author_id
        self.guild_id = guild_id

    @discord.ui.button(label="Start", custom_id="confirm_yes", style=discord.ButtonStyle.blurple)
    async def confirm_yes(self, button, interaction):
        # Save player data here
        save_player_data(self.guild_id, self.player_data)
        await interaction.response.send_message(f"Your selection of {self.exemplar_instance.name} Exemplar has been saved!", ephemeral=False)

    @discord.ui.button(label="Back", custom_id="confirm_no", style=discord.ButtonStyle.grey)
    async def confirm_no(self, button, interaction):
        # Re-send the PickExemplars view
        view = discord.ui.View()
        view.add_item(PickExemplars())
        await interaction.response.send_message("Please choose your exemplar from the list below.", view=view, ephemeral=False)


@bot.slash_command(description="Battle a monster!")
async def battle(ctx, monster: Option(str, "Pick a monster to battle.", choices=generate_monster_list(), required=True, default='')):
    if not monster:
        await ctx.respond("Please pick a monster to battle.", ephemeral=True)
        return

    with open("level_data.json", "r") as f:
        LEVEL_DATA = json.load(f)

    guild_id = ctx.guild.id
    author_id = str(ctx.author.id)

    player_data = load_player_data(guild_id)

    player = Exemplar(player_data[author_id]["exemplar"],
                      player_data[author_id]["stats"],
                      player_data[author_id]["inventory"])

    # Check the player's health before starting a battle
    if player.stats.health <= 0:
        # Direct them to resurrection options instead of starting a new battle
        await ctx.respond("⚰️ You must first ***/travel***  to the nearest 🪦 cemetery to reenter the realm of the living. ⚰️")
        return

    # Initialize in_battle flag before starting the battle
    player_data[author_id].setdefault("in_battle", False)
    player_data[author_id]["in_battle"] = True
    save_player_data(guild_id, player_data)

    zone_level = player.stats.zone_level
    monster = generate_monster_by_name(monster, zone_level)

    battle_embed = await send_message(ctx.channel,
                                      create_battle_embed(ctx.author, player, monster, footer_text_for_embed(ctx), messages= ""))

    await ctx.respond(f"{ctx.author.mention} encounters a {monster.name}")

    # Store the message object that is sent
    battle_options_msg = await ctx.send(view=BattleOptions(ctx))

    battle_outcome, loot_messages = await monster_battle(ctx, ctx.author, player, monster, zone_level, battle_embed)

    if battle_outcome[0]:

        experience_gained = monster.experience_reward
        await player.gain_experience(experience_gained, 'combat', ctx)
        player_data[author_id]["stats"]["combat_level"] = player.stats.combat_level
        player_data[author_id]["stats"]["combat_experience"] = player.stats.combat_experience
        player.stats.damage_taken = 0
        player_data[author_id]["stats"].update(player.stats.__dict__)

        if player.stats.health <= 0:
            player.stats.health = player.stats.max_health

        # Save the player data after common actions
        save_player_data(guild_id, player_data)

        # Clear the previous BattleOptions view
        await battle_options_msg.delete()
        loot_view = LootOptions(ctx, player, monster, battle_embed, player_data, author_id, battle_outcome, loot_messages, guild_id, ctx, experience_gained)

        # Construct the embed with the footer
        battle_outcome_embed = create_battle_embed(ctx.user, player, monster, footer_text_for_embed(ctx),
                                                   f"You have **DEFEATED** the {monster.name}!\n"
                                                   f"You dealt **{battle_outcome[1]} damage** to the monster and took **{battle_outcome[2]} damage**. "
                                                   f"You gained {experience_gained} combat XP.\n"
                                                   f"\n\u00A0\u00A0")

        await battle_embed.edit(
            embed=battle_outcome_embed,
            view=loot_view
        )


    else:

        # The player is defeated
        player.stats.health = 0  # Set player's health to 0
        player_data[author_id]["stats"]["health"] = 0

        # Create a new embed with the defeat message
        new_embed = create_battle_embed(ctx.user, player, monster, footer_text = "", messages =

        f"☠️ You have been **DEFEATED** by the **{monster.name}**!\n"
        f"{get_emoji('rip_emoji')} *Your spirit lingers, seeking renewal.* {get_emoji('rip_emoji')}\n\n"
        f"__**Options for Revival:**__\n"
        f"1. Use {get_emoji('Materium')} to revive without penalty.\n"
        f"2. Resurrect with 2.5% penalty to all skills.")

        # Clear the previous BattleOptions view
        await battle_options_msg.delete()

        # Add the "dead.png" image to the embed
        new_embed.set_image(url=generate_urls("cemetery", "dead"))

        # Update the message with the new embed and view
        await battle_embed.edit(embed=new_embed, view=ResurrectOptions(ctx, player_data, author_id, new_embed))

    # Clear the in_battle flag after the battle ends
    player_data[author_id]["in_battle"] = False
    save_player_data(guild_id, player_data)

@bot.slash_command(description="Start a new game.")
async def newgame(ctx):
    guild_id = ctx.guild.id
    author_id = str(ctx.author.id)  # Keep the types consistent
    player_data = load_player_data(guild_id)

    class NewGame(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(label="New Game", custom_id="new_game", style=discord.ButtonStyle.blurple)
        async def button1(self, button, interaction):
            # Explicitly remove and re-initialize player data
            player_data[author_id] = {
                "exemplar": None,
                "stats": None,
                "inventory": Inventory().to_dict(),
            }
            save_player_data(guild_id, player_data)
            view = View()
            view.add_item(PickExemplars())
            await interaction.response.send_message(
                f"{ctx.author.mention}, your progress has been erased. Please choose your exemplar from the list below.",
                view=view)

    if author_id not in player_data:
        view = View()
        view.add_item(PickExemplars())
        await ctx.respond(f"{ctx.author.mention}, please choose your exemplar from the list below.", view=view)
    else:
        view = NewGame()
        await ctx.respond(
            f"{ctx.author.mention}, you have a game in progress. Do you want to erase your progress and start a new game?",
            view=view)


@bot.slash_command()
async def menu(ctx):
    embed = Embed(title="Main Menu", description="Here are the available commands:", color=0x00ff00)
    embed.add_field(name="!battle", value="💀 Fight monsters or search for dungeons", inline=False)
    embed.add_field(name="!gather", value="🎣 Gather resources", inline=False)
    embed.add_field(name="!citadel", value="🛡️ Craft items", inline=False)
    embed.add_field(name="!travel", value="🐴 Travel towns or different zones", inline=False)
    embed.add_field(name="!inventory", value="💰 Check your inventory", inline=False)
    embed.add_field(name="!equip", value="🗡️ Equip or unequip items", inline=False)
    embed.add_field(name="!stats", value="📊 Check your character's stats", inline=False)

    await ctx.respond(embed=embed)

zone_names = ['Forest of Shadows', 'Desert of Doom', 'Icy Tundra', 'Volcanic Wasteland', 'Tower of Eternity']
zones = [Zone(name, level) for level, name in enumerate(zone_names, 1)]

bot.run(os.environ["DISCORD_TOKEN"])


