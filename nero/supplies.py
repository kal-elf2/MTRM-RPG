import discord
from utils import save_player_data, CommonResponses, refresh_player_from_data, get_server_setting
from emojis import get_emoji
from images.urls import generate_gif_urls, generate_urls

class StockCaravelButton(discord.ui.Button, CommonResponses):
    def __init__(self, guild_id, player, player_data, author_id):
        # Initialize the button, set label and style as needed
        super().__init__(label="Stock Caravel", style=discord.ButtonStyle.secondary, emoji=f"{get_emoji('Cannonball')}")
        self.guild_id = guild_id
        self.player = player
        self.player_data = player_data
        self.author_id = author_id

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        if self.player_data["location"] == "kraken":
            await CommonResponses.during_kraken_battle_response(interaction)
            return

        if self.player_data["location"] == "kraken":
            await CommonResponses.during_kraken_battle_response(interaction)
            return

        await interaction.response.defer()

        stock_supplies = StockSupplies(guild_id=self.guild_id, player=self.player,
                                       player_data=self.player_data, author_id=self.author_id)

        # Directly calling the display method of StockSupplies class
        await stock_supplies.display_supplies(interaction=interaction, zone_level=self.player.stats.zone_level,
                                              embed_color=discord.Color.dark_gold())

class StockSupplies:
    def __init__(self, guild_id, player, player_data, author_id):
        self.guild_id = guild_id
        self.player = player
        self.player_data = player_data
        self.author_id = author_id

    async def display_supplies(self, interaction, zone_level, embed_color):
        from nero.options import TravelSelectDropdown

        ship_name = TravelSelectDropdown.ship_names.get(zone_level)
        ship_gif_url = generate_gif_urls("ships", ship_name)

        poplar_strip_inventory = self.player.inventory.get_item_quantity('Poplar Strip')
        cannonball_inventory = self.player.inventory.get_item_quantity('Cannonball')
        poplar_strip_shipwreck = self.player_data['shipwreck'].get('Poplar Strip', 0)
        cannonball_shipwreck = self.player_data['shipwreck'].get('Cannonball', 0)

        if zone_level < 5:
            required_amount = get_server_setting(interaction.guild_id, 'base_zone_supply_requirement') * zone_level
            max_deposit_text = f"({required_amount} Required)"
        else:
            required_amount = float('inf')  # Effectively no maximum
            max_deposit_text = f"(Minimum: {zone_level * get_server_setting(interaction.guild_id, 'base_zone_supply_requirement')})"

        embed = discord.Embed(
            title=f"{ship_name} Supplies",
            color=embed_color
        )
        embed.set_image(url=ship_gif_url)
        embed.add_field(
            name="Backpack",
            value=f"{get_emoji('Poplar Strip')} **{poplar_strip_inventory}**\n{get_emoji('Cannonball')} **{cannonball_inventory}**",
            inline=True
        )
        embed.add_field(
            name=f"Deposited: {max_deposit_text}",
            value=f"{get_emoji('Poplar Strip')} **{poplar_strip_shipwreck}** Poplar Strips\n{get_emoji('Cannonball')} **{cannonball_shipwreck}** Cannonballs",
            inline=True
        )

        # Adjust conditions for button enable/disable based on inventory
        has_poplar_strips = poplar_strip_inventory >= 1 and (
                poplar_strip_shipwreck < required_amount or zone_level == 5)
        has_cannonballs = cannonball_inventory >= 1 and (cannonball_shipwreck < required_amount or zone_level == 5)
        has_5_poplar_strips = poplar_strip_inventory >= 5 and (
                poplar_strip_shipwreck + 5 <= required_amount or zone_level == 5)
        has_5_cannonballs = cannonball_inventory >= 5 and (
                cannonball_shipwreck + 5 <= required_amount or zone_level == 5)

        # Create and add buttons to the view, adjusting for zone 5's no max limit
        poplar_strip_button_1 = DepositButton(get_emoji('Poplar Strip'), "Poplar Strip", 1, self.player,
                                              self.player_data, self.author_id, self.guild_id, discord.ButtonStyle.green,
                                              disabled=not has_poplar_strips)
        poplar_strip_button_5 = DepositButton(get_emoji('Poplar Strip'), "Poplar Strip", 5, self.player,
                                              self.player_data, self.author_id, self.guild_id, discord.ButtonStyle.green,
                                              disabled=not has_5_poplar_strips)
        cannonball_button_1 = DepositButton(get_emoji('Cannonball'), "Cannonball", 1, self.player, self.player_data,
                                            self.author_id, self.guild_id, discord.ButtonStyle.grey, disabled=not has_cannonballs)
        cannonball_button_5 = DepositButton(get_emoji('Cannonball'), "Cannonball", 5, self.player, self.player_data,
                                            self.author_id, self.guild_id, discord.ButtonStyle.grey,
                                            disabled=not has_5_cannonballs)

        view = discord.ui.View()
        view.add_item(poplar_strip_button_1)
        view.add_item(poplar_strip_button_5)
        view.add_item(cannonball_button_1)
        view.add_item(cannonball_button_5)

        await interaction.followup.send(embed=embed, view=view)

class DepositButton(discord.ui.Button, CommonResponses):
    def __init__(self, emoji, item_name, amount, player, player_data, author_id, guild_id, style, disabled=False):
        super().__init__(style=style, label=f"x {amount}", emoji=emoji, disabled=disabled)
        self.item_name = item_name
        self.amount = amount
        self.player = player
        self.player_data = player_data
        self.author_id = author_id
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        from nero.options import TravelSelectDropdown
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player object from the latest player data
        self.player, self.player_data = await refresh_player_from_data(interaction)

        if self.player_data["location"] == "kraken":
            await self.during_kraken_battle_response(interaction)
            return

        # Initial shipwreck counts before updating to not send multiple embeds after reaching minimum in zone 5
        initial_poplar_count_shipwreck = self.player_data['shipwreck'].get('Poplar Strip', 0)
        initial_cannonball_count_shipwreck = self.player_data['shipwreck'].get('Cannonball', 0)

        zone_level = self.player.stats.zone_level
        required_minimum = get_server_setting(interaction.guild_id, 'base_zone_supply_requirement') * zone_level
        ship_name = TravelSelectDropdown.ship_names.get(zone_level, "Ship")
        ship_gif_url = generate_gif_urls("ships", ship_name)

        # Check initial inventory against the target before deposit
        initial_above_minimum_poplar = initial_poplar_count_shipwreck >= required_minimum
        initial_above_minimum_cannonball = initial_cannonball_count_shipwreck >= required_minimum

        color_mapping = {
            1: 0x969696,
            2: 0x15ce00,
            3: 0x0096f1,
            4: 0x9900ff,
            5: 0xfebd0d
        }
        embed_color = color_mapping.get(zone_level)

        current_amount = self.player_data.get('shipwreck', {}).get(self.item_name, 0)
        required_amount = get_server_setting(interaction.guild_id, 'base_zone_supply_requirement') * zone_level if zone_level < 5 else float('inf')

        # Check if adding the items exceeds the maximum allowed
        if current_amount + self.amount > required_amount and zone_level < 5:
            nero_embed = discord.Embed(
                title=f"{self.item_name.title()}s Full",
                description=f"Yarr! Ye be trying to sink us? The limit is {required_amount}. Maybe ye need to reset yer buttons.",
                color=discord.Color.dark_gold()
            )
            nero_embed.set_thumbnail(url=generate_urls("nero", "gun"))
            await interaction.followup.send(embed=nero_embed, ephemeral=True)
            return

        # Proceed with updating the shipwreck inventory and player's inventory
        self.player.inventory.remove_item(self.item_name, self.amount)
        self.player_data['shipwreck'][self.item_name] = current_amount + self.amount

        # Save the updated player data (Implement the `save_player_data` logic as needed)
        save_player_data(interaction.guild.id, self.author_id, self.player_data)

        # After recalculating the updated counts from shipwreck and inventory
        poplar_count_shipwreck = self.player_data['shipwreck'].get('Poplar Strip', 0)
        cannonball_count_shipwreck = self.player_data['shipwreck'].get('Cannonball', 0)
        poplar_count_inventory = self.player.inventory.get_item_quantity('Poplar Strip')
        cannonball_count_inventory = self.player.inventory.get_item_quantity('Cannonball')

        # Initialize nero_embed_sent to False at the start
        nero_embed_sent = False
        nero_message = ""

        # Adjust the Nero message as follows for Zone levels below 5
        if zone_level < 5 and poplar_count_shipwreck >= required_amount and cannonball_count_shipwreck >= required_amount:
            nero_message = f"Yarr! The ship is full to the brim {interaction.user.mention}! Come **visit me again at the Jolly Roger** when yer ready hunt down that Kraken!"
            nero_embed_sent = True

        if zone_level == 5:
            # Determine if both resources are now above the minimum
            both_above_minimum = poplar_count_shipwreck >= required_minimum and cannonball_count_shipwreck >= required_minimum

            # Only proceed if we haven't already marked the player as ready for battle
            if both_above_minimum and not (initial_above_minimum_poplar and initial_above_minimum_cannonball):
                # Send "Ready for Battle!" message only if we are transitioning from below to above the minimum for both resources
                nero_message = f"Hoist the colors {interaction.user.mention}! Ye've stocked enough to challenge the depths herself. Though the Kraken awaits, more supplies mean a stronger fight. Keep 'em coming, for glory and treasure!"
                nero_embed = discord.Embed(
                    title="Ready for Battle!",
                    description=nero_message,
                    color=discord.Color.dark_gold()
                )
                nero_embed.set_image(
                    url=generate_urls("nero", "kraken"))
                await interaction.followup.send(embed=nero_embed, ephemeral=False)

            elif any([
                initial_poplar_count_shipwreck < required_minimum <= poplar_count_shipwreck,
                initial_cannonball_count_shipwreck < required_minimum <= cannonball_count_shipwreck
            ]):
                # Send the "Ye Be On Course!" message only if one of the resources crosses the threshold
                nero_message = f"Arrr! **Ye've hoarded enough {get_emoji(self.item_name)} {self.item_name}s** to set sail against the Kraken beastie {interaction.user.mention}, but don't ye be stoppin'! The seas are harsh and unforgiving. Gather all ye can to ensure victory!"
                nero_embed = discord.Embed(
                    title="Ye Be On Course!",
                    description=nero_message,
                    color=discord.Color.dark_gold()
                )
                nero_embed.set_thumbnail(url=generate_urls("nero", "kraken"))
                await interaction.followup.send(embed=nero_embed, ephemeral=False)

        # Send the Nero message if needed
        if nero_embed_sent:
            nero_embed = discord.Embed(
                title="A Message from Captain Ner0",
                description=nero_message,
                color=discord.Color.dark_gold()
            )
            nero_embed.set_image(url=generate_urls("nero", "kraken"))
            await interaction.followup.send(embed=nero_embed, ephemeral=False)

        # Proceed with updating the supply counts and button states
        max_deposit_text = f"(Minimum: {zone_level * get_server_setting(interaction.guild_id, 'base_zone_supply_requirement')})" if zone_level == 5 else f"({required_amount} Required)"
        embed = discord.Embed(title=f"{ship_name} Supplies", color=embed_color)
        embed.set_image(url=ship_gif_url)
        embed.add_field(
            name="Backpack",
            value=f"{get_emoji('Poplar Strip')} **{poplar_count_inventory}**\n{get_emoji('Cannonball')} **{cannonball_count_inventory}**",
            inline=True
        )
        embed.add_field(
            name=f"Deposited: {max_deposit_text}",
            value=f"{get_emoji('Poplar Strip')} **{poplar_count_shipwreck}** Poplar Strips\n{get_emoji('Cannonball')} **{cannonball_count_shipwreck}** Cannonballs",
            inline=True
        )

        # Dynamically adjust the buttons based on the new item counts
        view = self.view
        for item in view.children:
            if isinstance(item, DepositButton):
                item_quantity = self.player.inventory.get_item_quantity(item.item_name)
                shipwreck_quantity = self.player_data['shipwreck'].get(item.item_name, 0)
                item.disabled = item_quantity < item.amount or (
                            shipwreck_quantity + item.amount > required_amount and zone_level < 5)

        await interaction.edit_original_response(embed=embed, view=view)


