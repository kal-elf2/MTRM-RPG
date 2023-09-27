from discord import Embed
from emojis import heart_emoji
import discord
from emojis import potion_red_emoji, potion_yellow_emoji
from utils import save_player_data
class LootOptions(discord.ui.View):
    def __init__(self, interaction, player, monster, battle_embed, player_data, author_id, battle_outcome,
                 loot_messages, guild_id, ctx, experience_gained):
        super().__init__(timeout=None)
        self.interaction_ = interaction
        self.player_ = player
        self.monster_ = monster
        self.battle_embed_ = battle_embed
        self.player_data_ = player_data
        self.author_id_ = author_id
        self.battle_outcome_ = battle_outcome
        self.loot_messages_ = loot_messages
        self.guild_id_ = guild_id
        self.ctx_ = ctx
        self.experience_gained = experience_gained

    @discord.ui.button(custom_id="loot", label="Loot", style=discord.ButtonStyle.blurple)
    async def collect_loot(self, button, interaction):

        for loot_type, loot_items in self.battle_outcome_[3]:
            if loot_type == 'coppers':
                self.player_.inventory.add_coppers(loot_items)
            elif loot_type == 'gem':
                self.player_.inventory.add_item_to_inventory(loot_items)
            elif loot_type == 'herb':
                self.player_.inventory.add_item_to_inventory(loot_items)
            elif loot_type == 'materium':
                self.player_.inventory.add_item_to_inventory(loot_items)
            elif loot_type == 'loot':
                self.player_.inventory.add_item_to_inventory(loot_items)
            elif loot_type == 'potion':
                self.player_.inventory.add_item_to_inventory(loot_items)
            elif loot_type == 'items':  # For items with quantity
                for item, quantity in loot_items:
                    self.player_.inventory.add_item_to_inventory(item, amount=quantity)

        self.player_data_[self.author_id_]["inventory"] = self.player_.inventory.to_dict()

        loot_message_string = '\n'.join(self.loot_messages_)

        message_text = (
            f"You have **DEFEATED** the {self.monster_.name}!\n"
            f"You dealt **{self.battle_outcome_[1]} damage** to the monster and took **{self.battle_outcome_[2]} damage**.\n"
            f"You gained {self.experience_gained} combat XP.\n\n" 
            f"__**Loot picked up:**__\n"
            f"{loot_message_string}"
        )

        final_embed = create_battle_embed(self.ctx_.user, self.player_, self.monster_, message_text)

        save_player_data(self.guild_id_, self.player_data_)
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

def create_battle_embed(user, player, monster, messages):
    player_health_bar = create_health_bar(player.health, player.stats.max_health)
    monster_health_bar = create_health_bar(monster.health, monster.max_health)

    # Replace spaces with '%20' for URL compatibility
    monster_name_url = monster.name.replace(" ", "%20")
    # Construct image URL
    image_url = f"https://raw.githubusercontent.com/kal-elf2/MTRM-RPG/master/images/monsters/{monster_name_url}.png"

    if isinstance(messages, list):
        messages = "\n".join(messages)
    elif isinstance(messages, str):
        messages = messages

    embed = Embed()
    embed.add_field(name="Battle", value=messages, inline=False)
    embed.add_field(name=f"{heart_emoji}  {user.name}'s Health", value=f"{player.health}/{player.stats.max_health}\n{player_health_bar}", inline=True)
    embed.add_field(name=f"{monster.name}'s Health", value=f"{monster.health}/{monster.max_health}\n{monster_health_bar}", inline=True)

    # Add image to embed
    embed.set_image(url=image_url)

    return embed