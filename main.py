import os
import json
import discord
from discord.ext import commands
from utils import load_player_data, save_player_data
from discord.ui import Select, View
from discord.components import SelectOption
from zones.zone import Zone
from exemplars.exemplars import create_exemplar, Exemplar
from monsters.monster import generate_monster, monster_battle, create_battle_embed
from discord import Embed, ui
from resources.inventory import Inventory

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

guild_data = {}

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command()
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

    await ctx.send(f'{ctx.channel.name} Channel set. Please type "!newgame" to start a new adventure! .')

# Exemplars class
class PickExemplars(Select):
    def __init__(self):
        options = [
            SelectOption(label='Human Exemplars', value='human',
                         emoji="<:human_seafarer:1052760015372562453>"),
            SelectOption(label='Dwarf Exemplars', value='dwarf',
                         emoji="<:dwarf_glimmeringclan:1052760138987098122>"),
            SelectOption(label='Orc Exemplars', value='orc',
                         emoji="<:orcsofthelonghunt:1052760210357375046>"),
            SelectOption(label='Halfling Exemplars', value='halfling',
                         emoji="<:halflinglongsong:1052760240954822678>"),
            SelectOption(label='Elf Exemplars', value='elf',
                         emoji="<:elf_darksun:1052760309875622009>")
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
            "zone_level": exemplar_instance.zone_level,
            "level": exemplar_instance.level,
            "experience": exemplar_instance.experience,
            "health": exemplar_instance.stats.health,
            "max_health": exemplar_instance.stats.max_health,
            "strength": exemplar_instance.stats.strength,
            "endurance": exemplar_instance.stats.endurance,
            "attack": exemplar_instance.stats.attack,  # Add this line
            "defense": exemplar_instance.stats.defense,  # Add this line
            "fishing_level": exemplar_instance.fishing_level,
            "fishing_experience": exemplar_instance.fishing_experience,
            "mining_level": exemplar_instance.mining_level,
            "mining_experience": exemplar_instance.mining_experience,
            "woodcutting_level": exemplar_instance.woodcutting_level,
            "woodcutting_experience": exemplar_instance.woodcutting_experience,
        }

        player_data[str(author_id)]["inventory"] = Inventory().to_dict()

        save_player_data(guild_id, player_data)

        await interaction.response.send_message(
            f'{interaction.user.mention}, you have chosen the {self.options_dict[self.values[0]]} Exemplar!',
            ephemeral=True)

async def send_message(ctx: commands.Context, embed):
    return await ctx.send(embed=embed)

class BattleOptions(Select):
    def __init__(self):
        options = [
            SelectOption(label="Search for monster", value="search_monster"),
            SelectOption(label="Enter nearby dungeon", value="enter_dungeon")
        ]
        super().__init__(placeholder="Choose an action", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        ctx = await bot.get_context(interaction.message)
        author_id = str(interaction.user.id)
        guild_id = interaction.guild.id
        player_data = load_player_data(guild_id)
        player = Exemplar(player_data[author_id]["exemplar"], player_data[author_id]["stats"], player_data[author_id]["inventory"])

        if self.values[0] == "search_monster":
            zone_level = player.zone_level
            monster = generate_monster(zone_level)
            battle_embed = await send_message(ctx.channel,
                                              create_battle_embed(interaction.user, player, monster))
            battle_outcome, loot_messages = await monster_battle(interaction.user, player, monster, zone_level,
                                                                 battle_embed)

            # Update the inventory
            if battle_outcome[0]:
                # Update player health based on damage received
                player.stats.health -= battle_outcome[1]
                for loot_type, loot_item in battle_outcome[3]:
                    if loot_type == 'gold':
                        player.inventory.add_gold(loot_item)
                    else:
                        player.inventory.add_item_to_inventory(loot_item)  # Use this line for all other item types
                player_data[author_id]["inventory"] = player.inventory.to_dict()

                experience_gained = zone_level * 10
                player.stats.experience += experience_gained
                player_data[author_id]["stats"][
                    "experience"] = player.stats.experience  # Add this line to update experience in the player_data dictionary
                player_data[author_id]["stats"].update(player.stats.__dict__)

                await battle_embed.edit(
                    embed=create_battle_embed(interaction.user, player, monster,
                                              f"You have defeated the {monster.name}! "
                                              f"You dealt {battle_outcome[2]} total damage to the monster and took {battle_outcome[1]} total damage. "
                                              f"You gained {experience_gained} experience points.\n{' '.join(loot_messages)}")
                )
            else:
                player.stats.health = player.stats.max_health
                player_data[author_id]["stats"].update(player.stats.__dict__)

                await battle_embed.edit(
                    embed=create_battle_embed(interaction.user, player, monster,
                                              f"You have been defeated by the {monster.name}. Your health has been restored."))

            save_player_data(guild_id, player_data)
        elif self.values[0] == "enter_dungeon":
            # Handle entering the dungeon
            await interaction.followup.send(
                f"{interaction.user.mention}, you entered the dungeon! (Feature not implemented yet)")


@bot.command()
async def newgame(ctx: commands.Context):
    guild_id = ctx.guild.id
    author_id = ctx.author.id
    player_data = load_player_data(guild_id)

    if str(author_id) not in player_data:
        view = View()
        view.add_item(PickExemplars())
        await ctx.send(f"{ctx.author.mention}, please choose your exemplar from the list below.", view=view)
    else:
        def check(m):
            return m.author.id == author_id and m.channel.id == ctx.channel.id

        await ctx.send(f"{ctx.author.mention}, you already have a game in progress. Do you want to erase your progress and start a new game? Type 'yes' to confirm or 'no' to cancel.")
        response = await bot.wait_for("message", check=check)

        if response.content.lower() == "yes":
            del player_data[str(author_id)]
            save_player_data(guild_id, player_data)
            view = View()
            view.add_item(PickExemplars())
            await ctx.send(f"{ctx.author.mention}, your progress has been erased. Please choose your exemplar from the list below.", view=view)
        else:
            await ctx.send(f"{ctx.author.mention}, your progress has not been erased. Continue your adventure!")

@bot.command()
async def battle(ctx: commands.Context):
    # Create and send the Select menu
    view=ui.View(timeout=None)
    view.add_item(BattleOptions())
    await ctx.send("What would you like to do?", view=view)

# Add this function after the newgame command definition
@bot.command()
async def menu(ctx: commands.Context):
    embed = Embed(title="Main Menu", description="Here are the available commands:", color=0x00ff00)
    embed.add_field(name="!battle", value="💀 Fight monsters or search for dungeons", inline=False)
    embed.add_field(name="!gather", value="🎣 Gather resources", inline=False)
    embed.add_field(name="!crafting", value="🛡️ Craft items", inline=False)
    embed.add_field(name="!travel", value="🐴 Travel towns or different zones", inline=False)
    embed.add_field(name="!inventory", value="💰 Check your inventory", inline=False)
    embed.add_field(name="!equip", value="🗡️ Equip or unequip items", inline=False)
    embed.add_field(name="!stats", value="📊 Check your character's stats", inline=False)

    await ctx.send(embed=embed)

zone_names = ['Forest of Shadows', 'Desert of Doom', 'Icy Tundra', 'Volcanic Wasteland', 'Tower of Eternity']
zones = [Zone(name, level) for level, name in enumerate(zone_names, 1)]

bot.run(os.environ["DISCORD_TOKEN"])
