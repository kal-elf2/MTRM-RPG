import os
import json
import discord
from discord.ext import commands
from discord.commands import Option
from utils import load_player_data, save_player_data, send_message, CommonResponses
from discord.ui import Select, View
from discord.components import SelectOption
from exemplars.exemplars import create_exemplar, Exemplar
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
        from exemplars.exemplars import DiceStats, MonsterKills, Shipwreck

        # Check if the user who interacted is the same as the one who initiated the view
        if str(interaction.user.id) != self.author_id:
            await self.unauthorized_user_response(interaction)
            return

        guild_id = interaction.guild.id
        player_data = load_player_data(guild_id)

        if str(self.author_id) not in player_data:
            player_data[str(self.author_id)] = {}

        # Update the exemplar in player_data
        player_data[str(self.author_id)]["exemplar"] = self.values[0]

        # Initialize the character's stats
        exemplar_instance = create_exemplar(self.values[0])

        player_data[str(self.author_id)]["stats"] = {
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
        player_data[str(self.author_id)]["dice_stats"] = DiceStats().to_dict()
        player_data[str(self.author_id)]["monster_kills"] = MonsterKills().to_dict()
        player_data[str(self.author_id)]["inventory"] = Inventory().to_dict()
        player_data[str(self.author_id)]["shipwreck"] = Shipwreck().to_dict()
        player_data[str(self.author_id)]["in_battle"] = False

        # Generate embed with exemplar stats
        embed = self.generate_stats_embed(exemplar_instance)

        # Create the confirmation view with two buttons
        view = ConfirmExemplar(exemplar_instance, player_data, str(self.author_id), guild_id)

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

class ConfirmExemplar(discord.ui.View, CommonResponses):
    def __init__(self, exemplar_instance, player_data, author_id, guild_id):
        super().__init__(timeout=None)
        self.exemplar_instance = exemplar_instance
        self.player_data = player_data
        self.author_id = author_id
        self.guild_id = guild_id

        # Create the confirm button with a dynamic label
        self.confirm_button = discord.ui.Button(
            label=f"Select {self.exemplar_instance.name}",
            custom_id="confirm_yes",
            style=discord.ButtonStyle.blurple
        )
        self.confirm_button.callback = self.confirm_yes
        self.add_item(self.confirm_button)

        # Create the back button
        self.back_button = discord.ui.Button(
            label="Back",
            custom_id="confirm_no",
            style=discord.ButtonStyle.grey
        )
        self.back_button.callback = self.confirm_no
        self.add_item(self.back_button)

    async def confirm_yes(self, interaction):
        # Check if the user who interacted is the same as the one who initiated the view
        if str(interaction.user.id) != self.author_id:
            await self.unauthorized_user_response(interaction)
            return

        # Disable both buttons
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        # Save player data here
        save_player_data(self.guild_id, self.player_data)

        # Update the message with the disabled view
        await interaction.response.edit_message(
            content=f"Your selection of {self.exemplar_instance.name} Exemplar has been saved!", view=self)

    async def confirm_no(self, interaction):
        # Check if the user who interacted is the same as the one who initiated the view
        if str(interaction.user.id) != self.author_id:
            await self.unauthorized_user_response(interaction)
            return

        # Re-send the PickExemplars view
        view = PickExemplars(self.author_id)
        await interaction.response.send_message("Please choose your exemplar from the list below.", view=view, ephemeral=False)

def update_special_attack_options(battle_context):
    # Assuming battle_context has a reference to the special_attack_options_view
    if battle_context.special_attack_options_view:
        battle_context.special_attack_options_view.update_button_states()

@bot.slash_command(description="Battle a monster!")
async def battle(ctx, monster: Option(str, "Pick a monster to battle.", choices=generate_monster_list(), required=True)):
    from monsters.monster import BattleContext

    guild_id = ctx.guild.id
    author_id = str(ctx.author.id)

    player_data = load_player_data(guild_id)

    # Check if player data exists for the user
    if author_id not in player_data:
        embed = Embed(title="Captain Ner0",
                      description="Arr! What be this? No record of yer adventures? Start a new game with `/newgame` before I make ye walk the plank.",
                      color=discord.Color.dark_gold())
        embed.set_thumbnail(url=generate_urls("nero", "confused"))
        await ctx.respond(embed=embed, ephemeral=True)
        return

    player = Exemplar(player_data[author_id]["exemplar"],
                      player_data[author_id]["stats"],
                      player_data[author_id]["inventory"])

    # Check the player's health before starting a battle
    if player.stats.health <= 0:
        embed = Embed(title="Captain Ner0",
                      description="Ahoy! Ye can't do that ye bloody ghost! Ye must travel to the 🪦 `/cemetery` to reenter the realm of the living.",
                      color=discord.Color.dark_gold())
        embed.set_thumbnail(url=generate_urls("nero", "confused"))
        await ctx.respond(embed=embed, ephemeral=True)
        return

    # Initialize in_battle flag before starting the battle
    player_data[author_id].setdefault("in_battle", False)
    player_data[author_id]["in_battle"] = True
    save_player_data(guild_id, player_data)

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
        player_data[author_id]["stats"]["stamina"] = player.stats.stamina
        player_data[author_id]["stats"]["combat_level"] = player.stats.combat_level
        player_data[author_id]["stats"]["combat_experience"] = player.stats.combat_experience
        player_data[author_id]["stats"]["health"] = player.stats.health
        player_data[author_id]["stats"]["damage_taken"] = player.stats.damage_taken
        player_data[author_id]["stats"].update(player.stats.__dict__)

        save_player_data(guild_id, player_data)

    # Process battle outcome
    else:
        # Unpack the battle outcome and loot messages
        battle_outcome, loot_messages = battle_result

        if battle_outcome[0]:

            experience_gained = monster.experience_reward
            loothaven_effect = battle_outcome[5]  # Get the Loothaven effect status
            await player.gain_experience(experience_gained, 'combat', ctx, player)

            player_data[author_id]["stats"]["stamina"] = player.stats.stamina
            player_data[author_id]["stats"]["combat_level"] = player.stats.combat_level
            player_data[author_id]["stats"]["combat_experience"] = player.stats.combat_experience
            player.stats.damage_taken = 0
            player_data[author_id]["stats"].update(player.stats.__dict__)

            if player.stats.health <= 0:
                player.stats.health = player.stats.max_health

            # Increment the count of the defeated monster
            player_data[author_id]["monster_kills"][monster.name] += 1

            # Save the player data after common actions
            save_player_data(guild_id, player_data)

            # Clear the previous views
            await battle_context.special_attack_message.delete()
            await battle_options_msg.delete()

            loot_view = LootOptions(ctx, player, monster, battle_embed, player_data, author_id, battle_outcome, loot_messages, guild_id, ctx, experience_gained, loothaven_effect)

            # Construct the embed with the footer
            battle_outcome_embed = create_battle_embed(ctx.user, player, monster, footer_text_for_embed(ctx, monster),
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
            f"2. Resurrect with 2.5% penalty to all skills."
            f"**Lose all items in inventory** (Keep coppers, MTRM, potions, and charms)"                                )

            # Clear the previous BattleOptions view
            await battle_context.special_attack_message.delete()
            await battle_options_msg.delete()

            # Add the "dead.png" image to the embed
            new_embed.set_image(url=generate_urls("cemetery", "dead"))

            # Update the message with the new embed and view
            await battle_embed.edit(embed=new_embed, view=ResurrectOptions(ctx, player_data, author_id))

    # Clear the in_battle flag after the battle ends
    player_data[author_id]["in_battle"] = False
    save_player_data(guild_id, player_data)

@bot.slash_command(description="Start a new game.")
async def newgame(ctx):
    guild_id = ctx.guild.id
    author_id = str(ctx.author.id)
    player_data = load_player_data(guild_id)

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
            player_data[author_id] = {
                "exemplar": None,
                "stats": None,
                "inventory": Inventory().to_dict(),
            }
            save_player_data(guild_id, player_data)

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

    if author_id not in player_data:
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

    player_data = load_player_data(guild_id)

    # Check if player data exists for the user
    if author_id not in player_data:
        embed = Embed(title="Captain Ner0",
                      description="Arr! What be this? No record of yer adventures? Start a new game with `/newgame` before I make ye walk the plank.",
                      color=discord.Color.dark_gold())
        embed.set_thumbnail(url=generate_urls("nero", "confused"))
        await ctx.respond(embed=embed, ephemeral=True)
        return

    player = Exemplar(player_data[author_id]["exemplar"],
                      player_data[author_id]["stats"],
                      player_data[author_id]["inventory"])

    cemetery_embed = discord.Embed()

    if player.stats.health <= 0:
        # Player is defeated, present resurrection options
        cemetery_embed.title = "You have been DEFEATED!"
        cemetery_embed.description = (
            f"☠️ Your spirit lingers, seeking renewal. ☠️\n\n"
            f"__**Options for Revival:**__\n"
            f"1. Use {get_emoji('Materium')} to revive without penalty.\n"
            f"2. Resurrect with 2.5% penalty to all skills. "
            f"**Lose all items in inventory** (Keep coppers, MTRM, potions, and charms)"
        )
        cemetery_embed.set_image(url=generate_urls("cemetery", "dead"))
        resurrect_view = ResurrectOptions(ctx, player_data, author_id)
        view = resurrect_view

        # Send the message with the appropriate embed and view
        await ctx.respond(embed=cemetery_embed, view=view)

    else:
        # Player is alive, just visiting the cemetery
        cemetery_embed.title = "Cemetery"
        cemetery_embed.description = f"Are you here to count how many pointy-eared 'splars are buried here too, {ctx.author.mention}?\n\nFeel free to pay yer respects, but as ye're still among the livin', there's not much else here for ye, savvy?"
        cemetery_embed.set_image(url=generate_urls("cemetery", "dead"))
        cemetery_embed.set_thumbnail(url=generate_urls("nero", "confused"))
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
    embed.set_image(url=generate_urls('nero', 'leaderboard'))

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


