import os
import json
import discord
from discord.ext import commands
from discord.commands import Option
from utils import load_player_data, save_player_data
from discord.ui import Select, View
from discord.components import SelectOption
from zones.zone import Zone
from exemplars.exemplars import create_exemplar, Exemplar
from monsters.monster import generate_monster_list, generate_monster_by_name, monster_battle, create_battle_embed
from discord import Embed
from resources.inventory import Inventory

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

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
            "health": exemplar_instance.stats.health,
            "max_health": exemplar_instance.stats.max_health,
            "strength": exemplar_instance.stats.strength,
            "endurance": exemplar_instance.stats.endurance,
            "attack": exemplar_instance.stats.attack,
            "defense": exemplar_instance.stats.defense,
            "combat_level": exemplar_instance.stats.combat_level,
            "combat_experience": exemplar_instance.stats.combat_experience,
            "fishing_level": exemplar_instance.stats.fishing_level,
            "fishing_experience": exemplar_instance.stats.fishing_experience,
            "mining_level": exemplar_instance.stats.mining_level,
            "mining_experience": exemplar_instance.stats.mining_experience,
            "woodcutting_level": exemplar_instance.stats.woodcutting_level,
            "woodcutting_experience": exemplar_instance.stats.woodcutting_experience
        }

        player_data[str(author_id)]["inventory"] = Inventory().to_dict()

        save_player_data(guild_id, player_data)

        await interaction.response.send_message(
            f'{interaction.user.mention}, you have chosen the {self.options_dict[self.values[0]]} Exemplar!',
            ephemeral=False)

async def send_message(ctx: commands.Context, embed):
    return await ctx.send(embed=embed)

@bot.slash_command(description="Battle a monster!")
async def battle(ctx, monster: Option(str, "Pick a monster to battle.", choices=generate_monster_list(), required=False, default='')):
    if not monster:
        await ctx.respond("Choosing a monster is required to start a battle.", ephemeral=True)
        return

    guild_id = ctx.guild.id
    author_id = str(ctx.author.id)

    player_data = load_player_data(guild_id)
    in_battle = player_data[author_id].get("in_battle", False)

    if in_battle:
        await ctx.respond("You are already in a battle!")
        return

    player = Exemplar(player_data[author_id]["exemplar"],
                      player_data[author_id]["stats"],
                      player_data[author_id]["inventory"])

    # Initialize in_battle flag before starting the battle
    player_data[author_id].setdefault("in_battle", False)
    player_data[author_id]["in_battle"] = True
    save_player_data(guild_id, player_data)

    zone_level = player.zone_level
    monster = generate_monster_by_name(monster, zone_level)

    battle_embed = await send_message(ctx.channel,
                                      create_battle_embed(ctx.author, player, monster))
    await ctx.respond(f"{ctx.author.mention} encounters a {monster.name}")
    await ctx.send(view=BattleOptions(ctx))

    battle_outcome, loot_messages = await monster_battle(ctx.author, player, monster, zone_level, battle_embed)
    if battle_outcome[0]:
        # Update player health based on damage received
        for loot_type, loot_items in battle_outcome[3]:
            if loot_type == 'gold':
                player.inventory.add_gold(loot_items)
            elif loot_type == 'items':
                # Check if loot_items is a list of tuples (meaning it's a list of (item, quantity) pairs)
                if isinstance(loot_items, list) and all(isinstance(i, tuple) for i in loot_items):
                    for item, quantity in loot_items:
                        for _ in range(quantity):
                            player.inventory.add_item_to_inventory(item)
                elif isinstance(loot_items, list):  # If it's just a list of items
                    for item in loot_items:
                        player.inventory.add_item_to_inventory(item)
                else:  # If loot_items is a single object
                    player.inventory.add_item_to_inventory(loot_items)
            else:
                if isinstance(loot_items, list) and all(isinstance(i, tuple) for i in loot_items):
                    for item, quantity in loot_items:
                        for _ in range(quantity):
                            player.inventory.add_item_to_inventory(item)
                elif isinstance(loot_items, list):  # If it's just a list of items
                    for item in loot_items:
                        player.inventory.add_item_to_inventory(item)
                else:  # If loot_items is a single object
                    player.inventory.add_item_to_inventory(loot_items)
        player_data[author_id]["inventory"] = player.inventory.to_dict()

        experience_gained = monster.experience_reward
        await player.gain_experience(experience_gained, 'combat', ctx)

        player_data[author_id]["stats"]["combat_level"] = player.stats.combat_level
        player_data[author_id]["stats"]["combat_experience"] = player.stats.combat_experience
        player.stats.damage_taken = 0
        # update experience in the player_data dictionary
        player_data[author_id]["stats"].update(player.stats.__dict__)

        if player.stats.health <= 0:
            player.stats.health = player.stats.max_health

        loot_message_string = '\n'.join(loot_messages)

        await battle_embed.edit(
            embed=create_battle_embed(ctx.user, player, monster,
                                      f"You have **DEFEATED** the {monster.name}!\n\n"
                                      f"You dealt **{battle_outcome[1]} damage** to the monster and took **{battle_outcome[2]} damage**. "
                                      f"You gained {experience_gained} combat XP.\n"
                                      f"\n"
                                      f"__**Loot picked up:**__\n"
                                      f"```{loot_message_string}```")
        )



    else:
        player.stats.health = player.stats.max_health
        player.stats.damage_taken = 0
        player_data[author_id]["stats"].update(player.stats.__dict__)

        await battle_embed.edit(
            embed=create_battle_embed(ctx.user, player, monster,
                                      f"You have been defeated by the {monster.name}. Your health has been restored."))

    # Clear the in_battle flag after the battle ends
    player_data[author_id]["in_battle"] = False
    save_player_data(guild_id, player_data)

@bot.slash_command(description="Start a new game.")
async def newgame(ctx):
    guild_id = ctx.guild.id
    author_id = ctx.author.id
    player_data = load_player_data(guild_id)

    class NewGame(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(label="New Game", custom_id="new_game", style=discord.ButtonStyle.blurple)
        async def button1(self, button, interaction):
            del player_data[str(author_id)]
            save_player_data(guild_id, player_data)
            view = View()
            view.add_item(PickExemplars())
            await interaction.response.send_message(
                f"{ctx.author.mention}, your progress has been erased. Please choose your exemplar from the list below.",
                view=view)


    if str(author_id) not in player_data:
        view = View()
        view.add_item(PickExemplars())
        await ctx.respond(f"{ctx.author.mention}, please choose your exemplar from the list below.", view=view)
    else:
        def check(m):
            return m.author.id == author_id and m.channel.id == ctx.channel.id

        view = NewGame()
        await ctx.respond(
            f"{ctx.author.mention}, you already have a game in progress. Do you want to erase your progress and start a new game?",
            view=view)

class BattleOptions(discord.ui.View):
    def __init__(self, interaction):
        super().__init__(timeout=None)
        self.interaction = interaction

    @discord.ui.button(custom_id="attack", style=discord.ButtonStyle.blurple, emoji = '⚔️')
    async def special_attack(self, button, interaction):
        pass
    @discord.ui.button(custom_id="health", style=discord.ButtonStyle.blurple, emoji='<:potion_red:1133946477463482458>')
    async def health_potion(self, button, interaction):
        pass
    @discord.ui.button(custom_id="stamina", style=discord.ButtonStyle.blurple, emoji="<:potion_yellow:1133946478386221237>")
    async def stamina_potion(self, button, interaction):
        pass
    @discord.ui.button(label="Run", custom_id="run", style=discord.ButtonStyle.blurple)
    async def run_button(self, button, interaction):
        pass

@bot.slash_command()
async def menu(ctx):
    embed = Embed(title="Main Menu", description="Here are the available commands:", color=0x00ff00)
    embed.add_field(name="!battle", value="💀 Fight monsters or search for dungeons", inline=False)
    embed.add_field(name="!gather", value="🎣 Gather resources", inline=False)
    embed.add_field(name="!crafting", value="🛡️ Craft items", inline=False)
    embed.add_field(name="!travel", value="🐴 Travel towns or different zones", inline=False)
    embed.add_field(name="!inventory", value="💰 Check your inventory", inline=False)
    embed.add_field(name="!equip", value="🗡️ Equip or unequip items", inline=False)
    embed.add_field(name="!stats", value="📊 Check your character's stats", inline=False)

    await ctx.respond(embed=embed)

zone_names = ['Forest of Shadows', 'Desert of Doom', 'Icy Tundra', 'Volcanic Wasteland', 'Tower of Eternity']
zones = [Zone(name, level) for level, name in enumerate(zone_names, 1)]

bot.run(os.environ["DISCORD_TOKEN"])


