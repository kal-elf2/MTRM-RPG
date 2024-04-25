import discord
from probabilities import buyback_cost
from utils import save_player_data, load_player_data, CommonResponses
from images.urls import generate_urls
from emojis import get_emoji

class NeroView(discord.ui.View, CommonResponses):
    def __init__(self, interaction, player_data, author_id, player, saved_inventory):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.player_data = player_data
        self.author_id = author_id
        self.player = player
        self.saved_inventory = saved_inventory
        self.total_item_value = self.calculate_total_inventory_value(saved_inventory)
        self.cost = min(self.total_item_value / 2, buyback_cost * self.player.stats.zone_level)

    @staticmethod
    def calculate_total_inventory_value(inventory):
        sellable_categories = ["weapons", "armors", "shields", "charms", "potions"]
        total_value = 0
        for category in sellable_categories:
            category_items = getattr(inventory, category, [])
            for item in category_items:
                total_value += item.value * item.stack
        print(total_value)
        return total_value

    async def handle_buy_back(self, player_inventory, inventory_slots):
        player_inventory.coppers -= self.cost  # Deduct the correct cost

        # Proceed with merging items back to the inventory
        self.merge_items_from_saved_inventory(player_inventory, inventory_slots)
        self.player_data['inventory'] = player_inventory
        save_player_data(self.interaction.guild.id, self.author_id, self.player_data)

        formatted_cost = f"{self.cost:,}"  # Use the previously determined cost
        return f"Ha! Well done! I added a bottle of Rum too! Wait, I drank that. Never mind! Thanks for the **{formatted_cost}** {get_emoji('coppers_emoji')}, matey.\n\n**Your items have been restored.** Check yer pockets!"

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.primary)
    async def yes_button(self, button, interaction):

        # Check if the user who interacted is the same as the one who initiated the view
        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        from exemplars.exemplars import Exemplar

        # Reinitialize the player object with the current state from player_data
        guild_id = interaction.guild.id
        current_player_data = load_player_data(guild_id, self.author_id)
        self.player = Exemplar(current_player_data["exemplar"],
                               current_player_data["stats"],
                               current_player_data["inventory"])

        # Check available space and coppers before proceeding with buyback
        player_inventory = self.player.inventory
        inventory_slots = ["items", "trees", "herbs", "ore", "armors", "weapons", "shields"]
        available_space = player_inventory.limit - self.calculate_current_inventory_count(player_inventory,
                                                                                          inventory_slots)
        required_space = self.calculate_required_space_for_saved_inventory(player_inventory, inventory_slots)

        if required_space > available_space:
            additional_slots_needed = required_space - available_space
            slots_message = "slot" if additional_slots_needed == 1 else "slots"

            # Create the embed
            thumbnail_url = generate_urls("nero", "confused")
            nero_embed = discord.Embed(
                title="Captain Ner0",
                description=f"Ye be encumbered, matey! Free up at least {additional_slots_needed} more {slots_message} so I can secure ye loot!",
                color=discord.Color.dark_gold()
            )
            nero_embed.set_thumbnail(url=thumbnail_url)

            # Send the embed as an ephemeral message
            await interaction.response.send_message(embed=nero_embed, ephemeral=True)
            return

        if player_inventory.coppers < self.cost:
            # Create the embed
            thumbnail_url = generate_urls("nero", "confused")
            nero_embed = discord.Embed(
                title="Captain Ner0",
                description="Arr, ye be short on coppers! Can't make a deal without the coin. If ye happen to find some, return here and try again.",
                color=discord.Color.dark_gold()
            )
            nero_embed.set_thumbnail(url=thumbnail_url)

            # Send the embed as an ephemeral message
            await interaction.response.send_message(embed=nero_embed, ephemeral=True)
            return

        # Reinitialize the player object with the current state from player_data
        guild_id = interaction.guild.id
        current_player_data = load_player_data(guild_id, self.author_id)
        self.player = Exemplar(current_player_data["exemplar"],
                               current_player_data["stats"],
                               current_player_data["inventory"])

        # Now handle the buyback with the updated player object
        message = await self.handle_buy_back(player_inventory, inventory_slots)
        thumbnail_url = generate_urls("nero", "cemetery")
        nero_embed = discord.Embed(
            title="Captain Ner0",
            description=f"{message}",
            color=discord.Color.dark_gold()
        )
        nero_embed.set_thumbnail(url=thumbnail_url)
        await interaction.message.edit(embed=nero_embed, view=None)

    @discord.ui.button(label="No", style=discord.ButtonStyle.secondary)
    async def no_button(self, button, interaction):

        # Check if the user who interacted is the same as the one who initiated the view
        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Edit the original captain's message to show refusal and remove the buttons
        thumbnail_url = generate_urls("nero", "cemetery")
        nero_embed = discord.Embed(
            title="Captain Ner0",
            description=f"Arr, {interaction.user.mention}! Fine, stay ashore, but without yer precious loot! May the goblins have their way with ye.",
            color=discord.Color.dark_gold()
        )
        nero_embed.set_thumbnail(url=thumbnail_url)
        await interaction.message.edit(embed=nero_embed, view=None)

    def calculate_current_inventory_count(self, inventory, categories):
        total_count = 0
        for category in categories:
            category_items = getattr(inventory, category)
            category_count = len(category_items)  # Counts the number of lists/slots, not the quantity in stacks
            total_count += category_count
        return total_count

    def calculate_required_space_for_saved_inventory(self, inventory, categories):
        required_space = 0
        for category in categories:
            saved_category_items = getattr(self.saved_inventory, category)
            current_category_items = getattr(inventory, category)
            for saved_item in saved_category_items:
                if not self.find_existing_item_in_inventory(saved_item, current_category_items):
                    required_space += 1
        return required_space

    def merge_items_from_saved_inventory(self, inventory, categories):
        for category in categories:
            saved_category_items = getattr(self.saved_inventory, category)
            current_category_items = getattr(inventory, category)
            for saved_item in saved_category_items:
                existing_item = self.find_existing_item_in_inventory(saved_item, current_category_items)
                if existing_item:
                    existing_item.stack += saved_item.stack
                else:
                    current_category_items.append(saved_item)

    def find_existing_item_in_inventory(self, item_to_check, items_list):
        for item in items_list:
            from citadel.crafting import Weapon, Armor, Shield
            if isinstance(item, type(item_to_check)) and item.name == item_to_check.name:
                # Check for zone_level in case of Weapon, Armor, and Shield
                if isinstance(item, (Weapon, Armor, Shield)) and item.zone_level != item_to_check.zone_level:
                    continue
                return item
        return None

