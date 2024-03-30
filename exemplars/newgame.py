import discord
from utils import load_player_data, save_player_data, remove_player_data, CommonResponses
from discord.ui import Select
from discord.components import SelectOption
from resources.inventory import Inventory
from emojis import get_emoji
from images.urls import generate_urls

from discord.ext import commands
from discord.ui import View

class NewGameCog(commands.Cog, CommonResponses):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Start a new game.")
    async def newgame(self, ctx):
        guild_id = ctx.guild.id
        author_id = str(ctx.author.id)
        player_data = load_player_data(guild_id, author_id)

        if not player_data:
            view = View()
            view.add_item(PickExemplars(author_id))
            await ctx.respond(f"{ctx.author.mention}, please choose your exemplar from the list below.", view=view)
        else:
            view = NewGameView(author_id)
            await ctx.respond(
                f"You already have a game in progress, {ctx.author.mention}. Are you sure you want to erase all progress and start a new game?\n\n### 🚨🚨 **Please note: This action cannot be undone.** 🚨🚨",
                view=view)

class NewGameView(discord.ui.View, CommonResponses):
    def __init__(self, author_id=None):
        super().__init__(timeout=None)
        self.author_id = author_id

    @discord.ui.button(label="New Game", custom_id="new_game", style=discord.ButtonStyle.blurple)
    async def button1(self, button, interaction):
        if str(interaction.user.id) != self.author_id:
            await self.unauthorized_user_response(interaction)
            return

        remove_player_data(interaction.guild_id, self.author_id)

        button.disabled = True
        await interaction.message.edit(view=self)

        view = View()
        view.add_item(PickExemplars(author_id=self.author_id))
        await interaction.response.send_message(
            f"{interaction.user.mention}, your progress has been erased. Please choose your exemplar from the list below.",
            view=view)

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
        from exemplars.exemplars import DiceStats, MonsterKills, Shipwreck, BattleActions, create_exemplar

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
            "zone_level": exemplar_instance.stats.zone_level,
        }
        player_data["inventory"] = Inventory().to_dict()
        player_data["dice_stats"] = DiceStats().to_dict()
        player_data["monster_kills"] = MonsterKills().to_dict()
        player_data["shipwreck"] = Shipwreck().to_dict()
        player_data["battle_actions"] = BattleActions().to_dict()
        player_data["location"] = None

        # Generate and send the confirmation message
        embed = self.generate_stats_embed(exemplar_instance)
        view = ConfirmExemplar(exemplar_instance, player_data, player_id, guild_id)
        await interaction.response.send_message(
            f'{interaction.user.mention}, verify your selection of {self.options_dict[self.values[0]]} Exemplar below!',
            embed=embed,
            view=view,
            ephemeral=True)

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
        self.left_arrow = None
        self.confirm_button = None
        self.right_arrow = None
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
        if str(interaction.user.id) != self.author_id:
            await self.unauthorized_user_response(interaction)
            return

        # Save player data here
        save_player_data(self.guild_id, self.author_id, self.player_data)

        # Determine the image and the specific part of the message based on the exemplar selection
        if self.player_data["exemplar"] == "elf":
            image_file, image_name = "nero", "disgust"
            exemplar_message = "### Bleh...**Another damn elf!?**\n\nWell I suppose I can still use ye...and I won't feel too bad when ye get lost to the sea.\n\nYe got any spine in there, Elf? I sure hope so...Yer gonna need it. Ye have quite the adventure ahead of ye..."
        else:
            image_file, image_name = "nero", "welcome"
            exemplar_message = f"Welcome aboard, {interaction.user.mention}! Hope yer blade is sharp and yer wits are sharper.\n\nYe have quite the adventure ahead of ye..."

        # Combine the specific part with the base part for the full message
        welcome_message = f"{exemplar_message}"

        # Dynamic initialization of adventure steps with optional thumbnails
        adventure_steps = [
            {
                'title': "A Grand Adventure",
                'description': welcome_message,
                'main_image_file': image_file,
                'main_image_name': image_name,
                'thumbnail_file': 'optional_thumbnail_directory',
                'thumbnail_image': 'optional_thumbnail_filename'
            },
            {
                'title': "Captain Ner0",
                'description': f"My name be Captain Ner0. I'll be adventurin' alongside ye in the world of Mirandus and doin' me best to keep ye out of the cemetery. \n\nNo promises though, {self.player_data['exemplar'].capitalize()}...This world is dangerous and death lurks around every corner.",
                'main_image_file': 'nero',
                'main_image_name': 'welcome',
                'thumbnail_file': 'nero',
                'thumbnail_image': 'pfp'
            },
            {
                'title': "The Kraken's Wrath",
                'description': "Besides booty and plunder, our grand quest be revenge on the monstrous Kraken that attacked me ship, swallowed it whole, and took me precious lantern.\n\nIt's no ordinary beast; it's a terror of the deep, it is! To stand a chance, ye'll need to **gather loot**, **craft mighty weapons**, and **level up**.\n\nOnly the bravest and strongest can face such a foe and live to tell the tale.",
                'main_image_file': 'nero',
                'main_image_name': 'kraken',
                'thumbnail_file': 'Icons',
                'thumbnail_image': 'Lantern of the Sun'
            },
            {
                'title': "Charting Yer Course",
                'description': "Navigatin' this world requires more than just a sturdy ship and a keen eye. Ye'll be needin' resources...and plenty of 'em.\n\nUse `/mine` to dig for precious ores, `/chop` for timber, and `/battle` to test yer mettle against the creatures of this land.\n\nGather loot, craft gear, and prepare yerself. It's a pirate's life, savvy? And it's full of danger and glory.",
                'main_image_file': 'nero',
                'main_image_name': 'cemetery',
            },
            {
                'title': "Ready for Adventure",
                 'description': f"That's about all the info ye need {interaction.user.mention}... Don't just stand there...get to lootin'!\n\nI'll be at the Jolly Roger drinkin' me rum if ye need anythin'.\n\n### **Use `/menu` to see all the commands available to ye.**",
                'main_image_file': 'nero',
                'main_image_name': 'welcome',
            },
            {
                'title': "The Lantern's Secret",
                'description': "*Beyond the sea's wrath and the Kraken's dark maw, a light unyielding, in shadow's claw. Its brilliance sealed by ancient decree, in sunken depths waits a key. A prize of old, bound by the tide, where darkness and light in silence collide.\n\nYe who seeks glory, take heed and make haste, for the **Lantern of the Sun** in cryptic waters is placed. Its secret guarded, its power confined, within a vault of numbers entwined. First to conquer, first to claim, a treasure in ethers, and eternal fame.\n\nSolve me this, brave souls of the sea: When darkness devours, where will light be? In the grasp of the Kraken, or the heart of the brave, lies the path to the lantern, through the deepest wave.*",
                'main_image_file': 'Icons',
                'main_image_name': 'Lantern of the Sun',

            }
        ]

        # Initialize BeginAdventureView with the dynamic adventure steps
        adventure_view = BeginAdventureView(self.author_id, adventure_steps)

        # Disable all buttons as the selection has been made and saved
        self.left_arrow.disabled = True
        self.confirm_button.disabled = True
        self.right_arrow.disabled = True
        await interaction.response.edit_message(view=self)

        # Create the first adventure embed and send it
        first_embed = adventure_view.create_adventure_embed(0)
        await interaction.followup.send(embed=first_embed, view=adventure_view)

class BeginAdventureView(discord.ui.View):
    def __init__(self, author_id, adventure_steps_messages):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.adventure_steps_messages = adventure_steps_messages
        self.current_step = 0
        self.setup_button()

    def setup_button(self):
        self.right_arrow = discord.ui.Button(style=discord.ButtonStyle.blurple, label='▶')
        self.right_arrow.callback = self.next_step
        self.add_item(self.right_arrow)

    async def next_step(self, interaction):
        if str(interaction.user.id) != self.author_id:
            await interaction.response.send_message("You are not authorized to do this!", ephemeral=True)
            return

        # Increment the current step
        self.current_step += 1

        # Check if we are now on the last message
        if self.current_step == len(self.adventure_steps_messages) - 1:
            # This is the last step, so disable the right arrow button for the next interaction
            self.right_arrow.disabled = True
            # Display the last step as an embed without waiting for another button press
            embed = self.create_adventure_embed(self.current_step)
            await interaction.response.edit_message(embed=embed, view=self)
        elif self.current_step < len(self.adventure_steps_messages):
            # There are more messages to display, so show the next step
            embed = self.create_adventure_embed(self.current_step)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            # If the button is somehow clicked beyond the last message, just disable it without changing the message
            await interaction.response.edit_message(view=self)

    def create_adventure_embed(self, step_index):
        step = self.adventure_steps_messages[step_index]
        embed = discord.Embed(
            title=step['title'],
            description=step['description'],
            color=discord.Color.blue()
        )

        # Set main image
        if 'main_image_file' in step and 'main_image_name' in step:
            main_image_url = generate_urls(step['main_image_file'], step['main_image_name'])
            embed.set_image(url=main_image_url)

        # Conditionally add a thumbnail if specified
        if 'thumbnail_file' in step and 'thumbnail_image' in step:
            thumbnail_url = generate_urls(step['thumbnail_file'], step['thumbnail_image'])
            embed.set_thumbnail(url=thumbnail_url)

        return embed


def setup(bot):
    bot.add_cog(NewGameCog(bot))