import discord
from emojis import get_emoji
from utils import CommonResponses, load_player_data
from images.urls import generate_urls

class JollyRogerView(discord.ui.View):
    def __init__(self, guild_id, player, player_data, author_id):
        super().__init__()
        self.add_item(TravelSelectDropdown(guild_id, player, player_data, author_id))
        self.author_id = author_id

    def ensure_reset_button(self):
        # Check if ResetButton is already in the view
        reset_button_exists = any(isinstance(item, ResetButton) for item in self.children)
        # If not, add the ResetButton to the view
        if not reset_button_exists:
            self.add_item(ResetButton(self.author_id))

class TravelSelectDropdown(discord.ui.Select, CommonResponses):
    ship_names = {1: "Picard", 2: "Crayer", 3: "Hoy", 4: "Carrack", 5: "Caravel"}
    def __init__(self, guild_id, player, player_data, author_id):
        self.guild_id = guild_id
        self.player = player
        self.player_data = player_data
        self.author_id = author_id

        zone_level = player.stats.zone_level

        options = [
            discord.SelectOption(label="Sell Booty", value="shop", emoji=f"{get_emoji('coppers_emoji')}")
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
        options.append(discord.SelectOption(label="Got Any Hints? ", value="hints", emoji="🗝️"))

        super().__init__(placeholder="Choose your action", options=options, min_values=1, max_values=1)

    async def refresh_player_from_data(self):
        from exemplars.exemplars import Exemplar
        """Refresh the player object from the latest player data."""
        self.player_data = load_player_data(self.guild_id, self.author_id)
        self.player = Exemplar(self.player_data["exemplar"],
                               self.player_data["stats"],
                               self.player_data["inventory"])


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

            # Refresh player object from the latest player data
            await self.refresh_player_from_data()

            # Check if there are any items across all categories
            has_items = any(getattr(self.player.inventory, category) for category in
                            ["weapons", "armors", "shields", "charms", "potions"])

            if not has_items:
                # Send a pirate-themed message if no items are available
                pirate_embed = discord.Embed(
                    title="Yarr, No Booty to Barter!",
                    description="Shiver me timbers! Ye hold be as empty as a deserted isle. Gather some loot before ye come to trade, ye scurvy dog!",
                    color=discord.Color.dark_gold()
                )
                pirate_thumbnail_url = generate_urls("nero", "confused")
                pirate_embed.set_thumbnail(url=pirate_thumbnail_url)
                await interaction.followup.send(embed=pirate_embed, ephemeral=True)
            else:
                self.view.clear_items()  # Clear existing items
                self.view.add_item(ShopCategorySelect(interaction.guild_id, self.author_id, self.player_data, self.player))
                self.view.add_item(ResetButton(self.author_id))  # Keep the Reset button
                await interaction.edit_original_response(content="Select a category to browse:", view=self.view)

        elif selected_option == "kraken":
            # Refresh player object from the latest player data
            await self.refresh_player_from_data()
            self.view.ensure_reset_button()

            required_level = zone_level * 20
            if zone_level == 5:
                required_level = 99
            requirements_met = True
            requirements_status = []

            check_mark_emoji = "✅"
            cross_mark_emoji = "❌"

            for skill_name, skill_level in [("combat", self.player.stats.combat_level),
                                            ("woodcutting", self.player.stats.woodcutting_level),
                                            ("mining", self.player.stats.mining_level)]:

                if skill_level < required_level:
                    requirements_met = False
                    status_emoji = cross_mark_emoji
                else:
                    status_emoji = check_mark_emoji
                requirements_status.append(
                    f"{status_emoji} {skill_name.capitalize()} Level: {skill_level}/{required_level}")

            goblin_crown_owned = self.player.inventory.get_item_quantity("Goblin Crown") > 0
            if goblin_crown_owned:
                requirements_status.append(f"{check_mark_emoji} Goblin Crown {get_emoji('goblin_crown_emoji')}")
            else:
                requirements_met = False
                requirements_status.append(f"{cross_mark_emoji} Goblin Crown {get_emoji('goblin_crown_emoji')}")

            requirements_message = "\n".join(requirements_status)


            if not requirements_met:
                message_title = "Ye be lackin' in preparation, matey!"
                message_description = f"Before ye can take on the Kraken, ye must meet these conditions:\n\n{requirements_message}\n\n'Tis risky business, Kraken huntin'. I'll be needin one of them **Goblin Crowns** as payment for the journey. I'll keep the ship ready for yer return."

                # Create and send the embed without the button as requirements are not met
                embed = discord.Embed(title=message_title, description=message_description,
                                      color=discord.Color.dark_gold())
                embed.set_thumbnail(url=generate_urls("nero", "confused"))
                await interaction.followup.send(embed=embed, ephemeral=True)

            else:
                from nero.kraken import HuntKrakenButton, SellAllButton
                from nero.supplies import StockCaravelButton

                # Player meets the requirements
                message_title = "Ready the Cannons!"
                message_description = f"Ye be ready to face the Kraken {interaction.user.mention}!\n\n{requirements_message}\n\nGood luck, matey!"

                # Create the embed and view with the "Hunt Kraken" button
                embed = discord.Embed(title=message_title, description=message_description,
                                      color=discord.Color.dark_gold())
                embed.set_thumbnail(url=generate_urls("nero", "kraken"))

                view = discord.ui.View()
                view.add_item(HuntKrakenButton(self.guild_id, self.player_data, self.author_id))

                # New: Check inventory and offer "Sell All" if in zones 1-4
                if zone_level < 5:
                    sellable_items_exist = any(getattr(self.player.inventory, category) for category in
                                               ["weapons", "armors", "shields", "charms", "potions"])
                    if sellable_items_exist:
                        # Send a message offering to sell all items
                        nero_thumbnail_url = generate_urls("nero", "shop")
                        sell_offer_embed = discord.Embed(
                            title="Ye Can't Take It With Ye!",
                            description="Arr, matey! There be no room on the ship for extra plunder whilst we set sail to battle the Kraken. Ye must part with yer goods, keeping only yer **Equipped Gear**, **Coppers**, and **Materium**.",
                            color=discord.Color.dark_gold()
                        )
                        sell_offer_embed.set_thumbnail(url=nero_thumbnail_url)
                        sell_all_view = discord.ui.View()
                        sell_all_view.add_item(SellAllButton("Sell Yer Loot", self.author_id, self.guild_id, self.player_data))
                        self.view.ensure_reset_button()
                        await interaction.followup.send(embed=sell_offer_embed, view=sell_all_view, ephemeral=True)
                        return

                # If in zone level 5, add the StockCaravelButton to the view
                if self.player.stats.zone_level == 5:
                    stock_caravel_button = StockCaravelButton(
                        guild_id=self.guild_id,
                        player=self.player,
                        player_data=self.player_data,
                        author_id=self.author_id
                    )
                    view.add_item(stock_caravel_button)

                await interaction.followup.send(embed=embed, view=view, ephemeral=False)

        elif selected_option == "supplies":
            from nero.supplies import StockSupplies

            stock_supplies = StockSupplies(self.guild_id, self.player, self.player_data, self.author_id)
            await stock_supplies.display_supplies(interaction, self.player.stats.zone_level, embed_color)

        elif selected_option == "hints":
            from nero.hints import create_nero_embed

            # Refresh player object from the latest player data
            await self.refresh_player_from_data()

            embed, view = create_nero_embed(self.player)
            self.view.ensure_reset_button()
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        elif selected_option == "spork":
            from nero.spork import RustySporkDialogView

            # Refresh player object from the latest player data
            await self.refresh_player_from_data()

            # Initialize the RustySporkDialogView with the first offer index (0 by default)
            view = RustySporkDialogView(self.player, self.author_id, self.player_data, 0)

            # Modify the initial embed to include the first offer
            first_offer_amount = "{:,.0f}".format(view.offers[0])
            nero_embed = discord.Embed(
                title="Captain Nero's Offer",
                description=f"Arrr, what's this? A **Rusty Spork** ye say? Looks like a piece o' junk to me.\n\n**But I suppose I could take it off yer hands for {first_offer_amount}{get_emoji('coppers_emoji')}...**",
                color=discord.Color.dark_gold()
            )

            nero_embed.set_thumbnail(url=generate_urls("nero", "shop"))
            self.view.ensure_reset_button()
            # Send the initial message with the view (RustySporkDialogView)
            await interaction.followup.send(embed=nero_embed, view=view, ephemeral=True)

        # Check if ResetButton is already in the view
        reset_button_exists = any(isinstance(item, ResetButton) for item in self.view.children)

        # If not, add the ResetButton to the view
        if not reset_button_exists:
            self.view.add_item(ResetButton(self.author_id))

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
        self.view.add_item(TravelSelectDropdown(guild_id, player, player_data, self.author_id))
        await interaction.response.edit_message(view=self.view)
