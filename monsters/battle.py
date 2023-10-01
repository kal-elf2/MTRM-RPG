from discord import Embed
from emojis import heart_emoji
import discord
import json
from emojis import potion_red_emoji, potion_yellow_emoji, uncommon_emoji, common_emoji, rare_emoji, epic_emoji, legendary_emoji
from utils import save_player_data, load_player_data
from images.urls import generate_urls

class LootOptions(discord.ui.View):
    def __init__(self, interaction, player, monster, battle_embed, player_data, author_id, battle_outcome,
                 loot_messages, guild_id, ctx, experience_gained):
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

    @discord.ui.button(custom_id="loot", label="Loot", style=discord.ButtonStyle.blurple)
    async def collect_loot(self, button, interaction):

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

        message_text = (
            f"You have **DEFEATED** the {self.monster.name}!\n"
            f"You dealt **{self.battle_outcome[1]} damage** to the monster and took **{self.battle_outcome[2]} damage**.\n"
            f"You gained {self.experience_gained} combat XP.\n\n" 
            f"__**Loot picked up:**__\n"
            f"{loot_message_string}\n\n"
        )

        final_embed = create_battle_embed(self.ctx.user, self.player, self.monster, footer_text_for_embed(self.ctx), message_text)

        save_player_data(self.guild_id, self.player_data)
        await interaction.message.edit(embed=final_embed, view=None)

class BattleOptions(discord.ui.View):
    def __init__(self, interaction):
        super().__init__(timeout=None)
        self.interaction = interaction

    @discord.ui.button(custom_id="attack", style=discord.ButtonStyle.blurple, emoji = '⚔️')
    async def special_attack(self, button, interaction):
        pass
    @discord.ui.button(custom_id="health", style=discord.ButtonStyle.blurple, emoji=f'{potion_red_emoji}')
    async def health_potion(self, button, interaction):
        pass
    @discord.ui.button(custom_id="stamina", style=discord.ButtonStyle.blurple, emoji=f'{potion_yellow_emoji}')
    async def stamina_potion(self, button, interaction):
        pass
    @discord.ui.button(label="Run", custom_id="run", style=discord.ButtonStyle.blurple)
    async def run_button(self, button, interaction):
        pass
def create_health_bar(current, max_health):
    bar_length = 12  # Fixed bar length
    health_percentage = current / max_health
    filled_length = round(bar_length * health_percentage)

    # Calculate how many '▣' symbols to display
    filled_symbols = '◼' * filled_length

    # Calculate how many '-' symbols to display
    empty_symbols = '◻' * (bar_length - filled_length)
    return filled_symbols + empty_symbols

def create_battle_embed(user, player, monster, footer_text, messages=None):
    player_health_bar = create_health_bar(player.health, player.stats.max_health)
    monster_health_bar = create_health_bar(monster.health, monster.max_health)

    zone_level = player.stats.zone_level

    # Emojis for each zone
    zone_emoji_mapping = {
        1: common_emoji,
        2: uncommon_emoji,
        3: rare_emoji,
        4: epic_emoji,
        5: legendary_emoji
    }

    color_mapping = {
        1: 0x969696,
        2: 0x15ce00,
        3: 0x0096f1,
        4: 0x9900ff,
        5: 0xfebd0d
    }

    # Get the appropriate emoji for the current zone
    zone_emoji = zone_emoji_mapping.get(zone_level)
    embed_color = color_mapping.get(zone_level)

    # Replace spaces with '%20' for URL compatibility
    monster_name_url = monster.name.replace(" ", "%20")
    # Construct image URL
    image_url = generate_urls("monsters", monster_name_url)

    if isinstance(messages, list):
        messages = "\n".join(messages)
    elif isinstance(messages, str):
        messages = messages

    embed = Embed(title=f"{zone_emoji} {monster.name}", color=embed_color)
    embed.add_field(name="Battle Outcome", value=messages, inline=False)
    embed.add_field(name=f"{heart_emoji}  {user.name}'s Health", value=f"{player.health}/{player.stats.max_health}\n{player_health_bar}", inline=True)
    embed.add_field(name=f"{monster.name}'s Health", value=f"{monster.health}/{monster.max_health}\n{monster_health_bar}", inline=True)

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

    # Determine the footer text based on combat level
    if next_combat_level >= 100:
        footer_text = f"⚔️ Combat Level:\u00A0\u00A0{current_combat_level}\u00A0\u00A0\u00A0\u00A0|\u00A0\u00A0\u00A0\u00A0📊 Max Level!\u00A0\u00A0{current_combat_experience} XP"
    else:
        next_level_experience_needed = LEVEL_DATA.get(str(current_combat_level), {}).get("total_experience")
        footer_text = f"⚔️ Combat Level:\u00A0\u00A0{current_combat_level}\u00A0\u00A0\u00A0\u00A0|\u00A0\u00A0\u00A0\u00A0📊 XP to Level {next_combat_level}:\u00A0\u00A0{next_level_experience_needed - current_combat_experience}"

    return footer_text
