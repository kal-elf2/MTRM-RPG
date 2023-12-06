from discord import Embed
import discord
import json
from emojis import get_emoji
from utils import save_player_data, load_player_data
from images.urls import generate_urls

class LootOptions(discord.ui.View):
    def __init__(self, interaction, player, monster, battle_embed, player_data, author_id, battle_outcome,
                 loot_messages, guild_id, ctx, experience_gained, loothaven_effect):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.player = player
        self.monster = monster
        self.battle_embed = battle_embed
        self.player_data = player_data
        self.author_id = author_id
        self.battle_outcome = battle_outcome
        self.loot_messages = loot_messages
        self.guild_id = guild_id
        self.ctx = ctx
        self.experience_gained = experience_gained
        self.loothaven_effect = loothaven_effect

    @discord.ui.button(custom_id="loot", label="Loot", style=discord.ButtonStyle.blurple)
    async def collect_loot(self, button, interaction):

        from exemplars.exemplars import Exemplar

        # Reload the latest player data
        self.player_data = load_player_data(self.guild_id)
        self.player = Exemplar(self.player_data[self.author_id]["exemplar"],
                               self.player_data[self.author_id]["stats"],
                               self.player_data[self.author_id]["inventory"])

        # Extract loot items and messages from the battle outcome
        loot = self.battle_outcome[3]

        # Extract all item drops (excluding 'coppers', 'materium' as they don't occupy inventory slots)
        new_items = [item for loot_type, loot_items in loot if loot_type in ('herb', 'items', 'gem', 'loot')
                     for item in (loot_items if isinstance(loot_items, list) else [loot_items])]

        # Calculate the number of new inventory slots required
        required_slots = 0
        for item in new_items:
            if isinstance(item, tuple):  # This is for 'items' type which has (Item, quantity) structure
                item_name = item[0].name
            else:
                item_name = item.name

            if not self.player.inventory.has_item(item_name):
                required_slots += 1

        # If player's inventory doesn't have enough space for new non-stackable items
        available_slots = self.player.inventory.limit - self.player.inventory.total_items_count()
        if available_slots < required_slots:
            await interaction.response.send_message("Inventory is full. Please make some room before collecting loot.",
                                                    ephemeral=True)
            return

        for loot_type, loot_items in self.battle_outcome[3]:
            if loot_type == 'coppers':
                self.player.inventory.add_coppers(loot_items)
            elif loot_type == 'gem':
                self.player.inventory.add_item_to_inventory(loot_items)
            elif loot_type == 'herb':
                self.player.inventory.add_item_to_inventory(loot_items)
            elif loot_type == 'materium':
                self.player.inventory.add_item_to_inventory(loot_items)
            elif loot_type == 'loot':
                self.player.inventory.add_item_to_inventory(loot_items)
            elif loot_type == 'potion':
                self.player.inventory.add_item_to_inventory(loot_items)
            elif loot_type == 'items':  # For items with quantity
                for item, quantity in loot_items:
                    self.player.inventory.add_item_to_inventory(item, amount=quantity)

        self.player_data[self.author_id]["inventory"] = self.player.inventory.to_dict()

        loot_message_string = '\n'.join(self.loot_messages)
        # Incorporate Loothaven charm effect in the message
        loothaven_message = f"\n{get_emoji('Loothaven')} Your **Loothaven charm** is *glowing*!\n" if self.loothaven_effect else ""

        message_text = (
            f"You have **DEFEATED** the {self.monster.name}!\n"
            f"You dealt **{self.battle_outcome[1]} damage** to the monster and took **{self.battle_outcome[2]} damage**.\n"
            f"You gained {self.experience_gained} combat XP.\n"
            f"{loothaven_message}\n"
            f"__**Loot picked up:**__\n"
            f"{loot_message_string}"
        )

        final_embed = create_battle_embed(self.ctx.user, self.player, self.monster, footer_text_for_embed(self.ctx), message_text)

        save_player_data(self.guild_id, self.player_data)
        await interaction.message.edit(embed=final_embed, view=None)


def use_potion_logic(player, potion_name):
    """
    Handles the logic of using a potion.
    :param player: Exemplar object representing the player
    :param potion_name: Name of the potion being used
    """
    potion = next((p for p in player.inventory.potions if p.name == potion_name), None)
    if potion and potion.stack > 0:
        # Apply the potion effect
        if potion_name in ["Health Potion", "Super Health Potion"]:
            player.stats.health = min(player.stats.health + potion.effect_value, player.stats.max_health)
        elif potion_name in ["Stamina Potion", "Super Stamina Potion"]:
            player.stats.stamina = min(player.stats.stamina + potion.effect_value, player.stats.max_stamina)

        # Decrement the potion stack
        potion.stack -= 1
        return True
    return False


class BattleOptions(discord.ui.View):
    def __init__(self, interaction, player, battle_context):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.player = player
        self.battle_context = battle_context

        # Initialize buttons with potion stack counts in the labels
        self.stamina_button = self.create_potion_button("Stamina Potion", self.stamina_button_callback)
        self.super_stamina_button = self.create_potion_button("Super Stamina Potion", self.super_stamina_button_callback)
        self.health_button = self.create_potion_button("Health Potion", self.health_button_callback)
        self.super_health_button = self.create_potion_button("Super Health Potion", self.super_health_button_callback)

        # Add buttons to the view
        self.add_item(self.stamina_button)
        self.add_item(self.super_stamina_button)
        self.add_item(self.health_button)
        self.add_item(self.super_health_button)

    def create_potion_button(self, potion_name, callback):
        stack_count = self.player.get_potion_stack(potion_name)
        emoji_str = get_emoji(potion_name)
        emoji_id = int(emoji_str.split(':')[2].strip('>'))
        emoji = discord.PartialEmoji(name=potion_name, id=emoji_id)
        button_label = f" {stack_count}" if stack_count else ""
        button = discord.ui.Button(
            label=button_label,
            custom_id=potion_name.lower().replace(" ", "_"),
            style=discord.ButtonStyle.blurple,
            emoji=emoji,
            disabled=self.is_potion_disabled(potion_name)
        )
        button.callback = callback
        return button

    def update_potion_button_label(self, button, potion_name):
        stack_count = self.player.get_potion_stack(potion_name)
        button.label = f"{stack_count}" if stack_count else ""

    async def stamina_button_callback(self, interaction):
        await self.use_potion("Stamina Potion", interaction, self.stamina_button)

    async def super_stamina_button_callback(self, interaction):
        await self.use_potion("Super Stamina Potion", interaction, self.super_stamina_button)

    async def health_button_callback(self, interaction):
        await self.use_potion("Health Potion", interaction, self.health_button)

    async def super_health_button_callback(self, interaction):
        await self.use_potion("Super Health Potion", interaction, self.super_health_button)

    def is_potion_disabled(self, potion_name):
        potion = next((item for item in self.player.inventory.potions if item.name == potion_name), None)
        return potion is None or potion.stack <= 0

    async def use_potion(self, potion_name, interaction, button):
        potion_used = use_potion_logic(self.player, potion_name)

        if potion_used:
            # Update the button label to show new stack count
            self.update_potion_button_label(button, potion_name)

            # Check if the potion is now disabled (e.g., stack is 0 or max stat reached)
            button.disabled = self.is_potion_disabled(potion_name)

            # Generate and append the potion usage message
            potion = next((p for p in self.player.inventory.potions if p.name == potion_name), None)
            if potion:
                emoji_str = get_emoji(potion_name)
                potion_message = f"{emoji_str} **{potion_name} restores {potion.effect_value} {potion.effect_stat}**"
                await self.battle_context.add_battle_message(potion_message)

            # Update battle embed with new footer text and messages
            updated_footer_text = footer_text_for_embed(self.interaction)
            battle_embed = create_battle_embed(
                self.interaction.user, self.player, self.battle_context.monster, updated_footer_text,
                self.battle_context.battle_messages
            )
            await self.battle_context.message.edit(embed=battle_embed)

            # Update the Discord view
            await interaction.response.edit_message(view=self)


class SpecialAttackOptions(discord.ui.View):

    def __init__(self, battle_context):
        super().__init__(timeout=None)
        self.battle_context = battle_context
        # Access attributes from battle_context
        self.ctx = battle_context.ctx
        self.player = battle_context.player
        self.monster = battle_context.monster
        self.battle_embed_message = battle_context.message
        self.author_id = battle_context.user.id
        self.battle_messages = battle_context.battle_messages

        self.equip_weapon = self.player.inventory.equipped_weapon
        self.special_attack = self.equip_weapon.special_attack if self.equip_weapon else 0

        # Determine the maximum special attack level based on player's special_attack
        self.max_special_attack_level = min(4, self.special_attack)

        # Create buttons based on the maximum special attack level
        self.create_buttons()

    def create_buttons(self):
        attack_emojis = ["left_click", "right_click", "q", "e"]  # Define the appropriate emoji names here

        for i in range(1, self.max_special_attack_level + 1):
            emoji = get_emoji(attack_emojis[i - 1])
            custom_id = f"attack_{i}"

            # Create a button for the current special attack level
            button = discord.ui.Button(style=discord.ButtonStyle.blurple, custom_id=custom_id, emoji=emoji, disabled=False)
            button.callback = self.on_button_click  # Assigning the callback function

            # Add the button to the view
            self.add_item(button)

        # Add the unarmed button if no weapon is equipped
        if not self.equip_weapon:
            button = discord.ui.Button(style=discord.ButtonStyle.blurple, custom_id="unarmed", emoji="👊🏽", disabled=False)
            button.callback = self.on_button_click  # Assigning the callback function
            self.add_item(button)

    async def on_button_click(self, interaction: discord.Interaction):

        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("This is not your battle!", ephemeral=True)

        # Acknowledge the interaction to prevent "interaction failed" message
        await interaction.response.defer()

        # Parse the custom_id to determine the attack level
        custom_id = interaction.data["custom_id"]
        attack_level = 1 if custom_id == "unarmed" else int(custom_id.split("_")[-1])

        # Call handle_attack with the attack level
        await self.handle_attack(interaction, attack_level)

    async def handle_attack(self, interaction, attack_level):
        from monsters.monster import player_attack_task

        # Use the existing battle_context
        await player_attack_task(self.battle_context, attack_level)

def create_health_bar(current, max_health):
    bar_length = 25  # Fixed bar length
    health_percentage = current / max_health
    filled_length = round(bar_length * health_percentage)

    # Calculate how many '▣' symbols to display
    filled_symbols = '◼' * filled_length

    # Calculate how many '-' symbols to display
    empty_symbols = '◻' * (bar_length - filled_length)
    return filled_symbols + empty_symbols

def create_monster_health_bar(current, max_health):
    bar_length = 25  # Fixed bar length
    health_percentage = current / max_health
    filled_length = round(bar_length * health_percentage)

    # Calculate how many '▣' symbols to display
    filled_symbols = '◼' * filled_length

    # Calculate how many '-' symbols to display
    empty_symbols = '◻' * (bar_length - filled_length)
    return filled_symbols + empty_symbols

def create_stamina_bar(current, max_stamina):
    bar_length = 25  # Fixed bar length
    stamina_percentage = current / max_stamina
    filled_length = round(bar_length * stamina_percentage)

    # Calculate how many '◼' symbols to display
    filled_symbols = '◼' * filled_length

    # Calculate how many '◻' symbols to display
    empty_symbols = '◻' * (bar_length - filled_length)
    return filled_symbols + empty_symbols

def create_battle_embed(user, player, monster, footer_text, messages=None):

    player_health_bar = create_health_bar(player.stats.health, player.stats.max_health)
    player_stamina_bar = create_stamina_bar(player.stats.stamina, player.stats.max_stamina)
    monster_health_bar = create_monster_health_bar(monster.health, monster.max_health)

    zone_level = player.stats.zone_level

    # Emojis for each zone
    zone_emoji_mapping = {
        1: 'common_emoji',
        2: 'uncommon_emoji',
        3: 'rare_emoji',
        4: 'epic_emoji',
        5: 'legendary_emoji'
    }

    color_mapping = {
        1: 0x969696,
        2: 0x15ce00,
        3: 0x0096f1,
        4: 0x9900ff,
        5: 0xfebd0d
    }

    # Get the appropriate emoji for the current zone
    zone_emoji = get_emoji(zone_emoji_mapping.get(zone_level))
    embed_color = color_mapping.get(zone_level)

    # Replace spaces with '%20' for URL compatibility
    monster_name_url = monster.name.replace(" ", "%20")
    # Construct image URL
    image_url = generate_urls("monsters", monster_name_url)

    if isinstance(messages, list):
        messages = "\n".join(messages)
    elif isinstance(messages, str):
        messages = messages
    else:
        messages = ""

    embed = Embed(title=f"{zone_emoji} {monster.name}", color=embed_color)

    # Add Battle Messages
    embed.add_field(name="Battle Outcome", value=messages, inline=False)

    # Add an extra blank space before the player's health and stamina bars
    embed.add_field(name='', value='', inline=False)

    # Add Health and Stamina Bars
    embed.add_field(name=user.name,
                    value=f"{get_emoji('heart_emoji')} {player.stats.health}/{player.stats.max_health}\n{player_health_bar}",
                    inline=False)
    embed.add_field(name="",
                    value=f"{get_emoji('stamina_emoji')} {player.stats.stamina}/{player.stats.max_stamina}\n{player_stamina_bar}",
                    inline=False)
    embed.add_field(name=f"{monster.name}",
                    value=f"{get_emoji('heart_emoji')} {monster.health}/{monster.max_health}\n{monster_health_bar}",
                    inline=False)

    # Add image to embed
    embed.set_image(url=image_url)
    # Set the footer for the embed
    embed.set_footer(text=footer_text)

    return embed

def footer_text_for_embed(ctx):
    with open("level_data.json", "r") as f:
        LEVEL_DATA = json.load(f)

    guild_id = ctx.guild.id
    author_id = str(ctx.user.id)
    player_data = load_player_data(guild_id)

    current_combat_level = player_data[author_id]["stats"]["combat_level"]
    next_combat_level = current_combat_level + 1
    current_combat_experience = player_data[author_id]["stats"]["combat_experience"]

    # Generate base footer text based on combat level
    if next_combat_level >= 100:
        footer_text = f"⚔️ Combat Level: {current_combat_level} | 📊 Max Level! {current_combat_experience} XP"
    else:
        next_level_experience_needed = LEVEL_DATA.get(str(current_combat_level), {}).get("total_experience")
        footer_text = f"⚔️ Combat Level: {current_combat_level} | 📊 XP to Level {next_combat_level}: {next_level_experience_needed - current_combat_experience}"

    return footer_text

