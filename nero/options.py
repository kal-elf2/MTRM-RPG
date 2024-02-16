import discord
from emojis import get_emoji
from utils import CommonResponses
from images.urls import generate_gif_urls

class JollyRogerView(discord.ui.View):
    def __init__(self, player, player_data, author_id):
        super().__init__()
        self.add_item(TravelSelectDropdown(player, player_data, author_id))

class TravelSelectDropdown(discord.ui.Select, CommonResponses):
    ship_names = {1: "Picard", 2: "Crayer", 3: "Hoy", 4: "Carrack", 5: "Caravel"}
    def __init__(self, player, player_data, author_id):
        self.player = player
        self.player_data = player_data
        self.author_id = author_id
        zone_level = player.stats.zone_level


        options = [
            discord.SelectOption(label="Shop", value="shop", emoji=f"{get_emoji('coppers_emoji')}")
        ]

        # Check for "Rusty Spork" in the player's inventory with at least 1 in stack
        if any(item.name == "Rusty Spork" and item.stack >= 1 for item in player.inventory.items):
            options.append(
                discord.SelectOption(label="What is this Rusty Spork?", value="spork",
                                     emoji=f"{get_emoji('Rusty Spork')}"))

        # Dynamic requirements based on zone level
        required_amount = 25 * zone_level
        poplar_strip = self.player_data.get("shipwreck", {}).get("Poplar Strip", 0)
        cannonball = self.player_data.get("shipwreck", {}).get("Cannonball", 0)


        # Conditionally add dynamic label based on zone level
        if poplar_strip >= required_amount and cannonball >= required_amount:
            options.append(discord.SelectOption(label="Hunt Kraken", value="kraken", emoji="🦑"))
        else:
            ship_name = self.ship_names.get(zone_level, "Ship")
            options.append(discord.SelectOption(label=f"Stock {ship_name}", value="supplies", emoji=f"{get_emoji('Cannonball')}"))

        # Add "Got any hints?"
        options.append(discord.SelectOption(label="Uncover Secrets", value="hints", emoji="🗝️"))

        super().__init__(placeholder="Choose your action", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        await interaction.response.defer()

        # Handle the selection here
        selected_option = self.values[0]
        zone_level = self.player.stats.zone_level
        color_mapping = {
            1: 0x969696,
            2: 0x15ce00,
            3: 0x0096f1,
            4: 0x9900ff,
            5: 0xfebd0d
        }
        embed_color = color_mapping.get(zone_level)

        if selected_option == "shop":
            from nero.shop import ShopCategorySelect
            self.view.clear_items()  # Clear existing items
            self.view.add_item(ShopCategorySelect(interaction.guild_id, self.author_id, self.player_data, self.player))
            self.view.add_item(ResetButton(self.author_id))  # Keep the Reset button
            await interaction.edit_original_response(content="Select a category to browse:", view=self.view)

        elif selected_option == "kraken":
            pass
        # Handle Fight Kraken action

        elif selected_option == "supplies":
            from nero.supplies import DepositButton
            ship_name = self.ship_names.get(zone_level)
            ship_gif_url = generate_gif_urls("ships", ship_name)

            poplar_strip_inventory = self.player.inventory.get_item_quantity('Poplar Strip')
            cannonball_inventory = self.player.inventory.get_item_quantity('Cannonball')
            poplar_strip_shipwreck = self.player_data['shipwreck'].get('Poplar Strip', 0)
            cannonball_shipwreck = self.player_data['shipwreck'].get('Cannonball', 0)

            # Define required amount based on zone level, no max for zone 5
            if zone_level < 5:
                required_amount = 25 * zone_level
                max_deposit_text = f"(Need {required_amount})"
            else:
                required_amount = float('inf')  # Effectively no maximum
                max_deposit_text = f"(Minimum: {zone_level * 25})"

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
                value=f"{get_emoji('Poplar Strip')} **{poplar_strip_shipwreck}**\n{get_emoji('Cannonball')} **{cannonball_shipwreck}**",
                inline=True
            )

            # Adjust conditions for button enable/disable
            has_poplar_strips = poplar_strip_inventory >= 1 and (
                        poplar_strip_shipwreck < required_amount or zone_level == 5)
            has_cannonballs = cannonball_inventory >= 1 and (cannonball_shipwreck < required_amount or zone_level == 5)
            has_5_poplar_strips = poplar_strip_inventory >= 5 and (
                        poplar_strip_shipwreck + 5 <= required_amount or zone_level == 5)
            has_5_cannonballs = cannonball_inventory >= 5 and (
                        cannonball_shipwreck + 5 <= required_amount or zone_level == 5)

            # Create and add buttons to the view, adjusting for zone 5's no max limit
            poplar_strip_button_1 = DepositButton(get_emoji('Poplar Strip'), "Poplar Strip", 1, self.player,
                                                  self.player_data, self.author_id, discord.ButtonStyle.green,
                                                  disabled=not has_poplar_strips)
            poplar_strip_button_5 = DepositButton(get_emoji('Poplar Strip'), "Poplar Strip", 5, self.player,
                                                  self.player_data, self.author_id, discord.ButtonStyle.green,
                                                  disabled=not has_5_poplar_strips)
            cannonball_button_1 = DepositButton(get_emoji('Cannonball'), "Cannonball", 1, self.player, self.player_data,
                                                self.author_id, discord.ButtonStyle.grey, disabled=not has_cannonballs)
            cannonball_button_5 = DepositButton(get_emoji('Cannonball'), "Cannonball", 5, self.player, self.player_data,
                                                self.author_id, discord.ButtonStyle.grey,
                                                disabled=not has_5_cannonballs)

            view = discord.ui.View()
            view.add_item(poplar_strip_button_1)
            view.add_item(poplar_strip_button_5)
            view.add_item(cannonball_button_1)
            view.add_item(cannonball_button_5)

            await interaction.followup.send(embed=embed, view=view)

        elif selected_option == "hints":
            pass
        # Handle Got any hints? action

        elif selected_option == "spork":
            pass
        # Handle Rusty Spork action

        # Check if ResetButton is already in the view
        reset_button_exists = any(isinstance(item, ResetButton) for item in self.view.children)

        # If not, add the ResetButton to the view
        if not reset_button_exists:
            self.view.add_item(ResetButton(self.author_id))

        # Since you're using defer earlier, you should use edit_original_response here
        await interaction.edit_original_response(view=self.view)

class ResetButton(discord.ui.Button, CommonResponses):
    def __init__(self, author_id):
        super().__init__(label="Reset", style=discord.ButtonStyle.secondary, custom_id="reset_jolly_roger")

        self.author_id = author_id

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        from exemplars.exemplars import Exemplar
        from utils import load_player_data

        # Fetch updated player data
        guild_id = interaction.guild.id
        player_data = load_player_data(guild_id, self.author_id)

        # Reinitialize player with the fresh data
        player = Exemplar(player_data["exemplar"],
                          player_data["stats"],
                          player_data["inventory"])

        # Reset the Jolly Roger view
        self.view.clear_items()
        self.view.add_item(TravelSelectDropdown(player, player_data, self.author_id))
        await interaction.response.edit_message(view=self.view)
