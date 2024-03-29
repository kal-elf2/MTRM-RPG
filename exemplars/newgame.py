import discord
from utils import load_player_data, save_player_data, CommonResponses
from discord.ui import Select
from discord.components import SelectOption
from resources.inventory import Inventory
from emojis import get_emoji
from images.urls import generate_urls

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

        # Initialize BeginAdventureView with the adventure steps
        adventure_view = BeginAdventureView(author_id=self.author_id, adventure_steps_messages=adventure_steps)

        # Create the first adventure embed
        first_embed = adventure_view.create_adventure_embed(0)

        # Sending a new message (or you can use followup.send if you want it to be separate from the initial interaction)
        await interaction.followup.send(embed=first_embed, view=adventure_view)

adventure_steps = [
    {'title': 'Step 1: The Journey Begins', 'description': 'Your journey starts in a small town...', 'file': 'nero', 'image': 'journey_begins'},
    {'title': 'Step 2: The Dark Forest', 'description': 'You enter a dark forest, filled with unknown dangers...', 'file': 'nero', 'image': 'dark_forest'},
    # Add more steps as needed
]
class BeginAdventureView(discord.ui.View):
    def __init__(self, author_id, adventure_steps_messages):
        super().__init__(timeout=None)  # Consider adding a timeout as per your game design
        self.author_id = author_id
        self.adventure_steps_messages = adventure_steps_messages
        self.current_step = 0
        self.setup_button()
        self.right_arrow = None

    def setup_button(self):
        # Right arrow button for navigating the introduction
        self.right_arrow = discord.ui.Button(label='▶', style=discord.ButtonStyle.green)
        self.right_arrow.callback = self.next_step
        self.add_item(self.right_arrow)

    async def next_step(self, interaction):
        # Ensure only the initiating user can interact
        if str(interaction.user.id) != self.author_id:
            await interaction.response.send_message("You are not authorized to do this!", ephemeral=True)
            return

        self.current_step += 1

        if self.current_step < len(self.adventure_steps_messages):
            # Update the embed with the next step of the adventure
            embed = self.create_adventure_embed(self.current_step)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            # If it's the last step, you might want to disable the button or move to a different part of the game
            self.right_arrow.disabled = True
            await interaction.response.edit_message(view=self)
            # Here, you can call another method or class to continue the game flow

    def create_adventure_embed(self, step_index):
        step = self.adventure_steps_messages[step_index]
        embed = discord.Embed(
            title=step['title'],
            description=step['description'],
            color=discord.Color.blue()
        )
        # Use both `file` and `image` to generate the URL
        embed_image_url = generate_urls(step['file'], step['image'])
        embed.set_image(url=embed_image_url)
        return embed
