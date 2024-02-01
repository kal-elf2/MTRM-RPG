import discord
from emojis import get_emoji
from utils import CommonResponses
from images.urls import generate_urls, generate_gif_urls
class TravelSelect(discord.ui.Select, CommonResponses):
    ship_names = {1: "Picard", 2: "Crayer", 3: "Hoy", 4: "Carrack", 5: "Caravel"}
    def __init__(self, player, player_data, author_id):
        self.player = player
        self.player_data = player_data
        self.author_id = author_id
        zone_level = player.stats.zone_level

        options = [
            discord.SelectOption(label="Shop", value="shop", emoji=f"{get_emoji('coppers_emoji')}")
        ]

        # Dynamic requirements based on zone level
        required_amount = 25 * zone_level
        poplar_strip = self.player_data.get("shipwreck", {}).get("poplar_strip", 0)
        cannonball = self.player_data.get("shipwreck", {}).get("cannonball", 0)


        # Conditionally add dynamic label based on zone level
        if poplar_strip >= required_amount and cannonball >= required_amount:
            options.append(discord.SelectOption(label="Fight Kraken", value="kraken", emoji="🦑"))
        else:
            ship_name = self.ship_names.get(zone_level, "Ship")
            options.append(discord.SelectOption(label=f"Store supplies on {ship_name}", value="supplies", emoji=f"{get_emoji('Cannonball')}"))

        # Add "Got any hints?"
        options.append(discord.SelectOption(label="Uncover Secrets", value="hints", emoji="🗝️"))

        # Check for "Rusty Spork" in the player's inventory with at least 1 in stack
        if any(item.name == "Rusty Spork" and item.stack >= 1 for item in player.inventory.items):
            options.append(
                discord.SelectOption(label="What is a Rusty Spork used for?", value="spork", emoji=f"{get_emoji('Rusty Spork')}"))

        super().__init__(placeholder="Choose your action", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

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
        embed_color = color_mapping.get(zone_level, 0x969696)  # Default color if zone level is not in mapping

        # Create embed message
        embed = discord.Embed(
            title=f"Selected: {selected_option}",
            description=f"You are currently in zone level {zone_level}.",
            color=embed_color
        )

        if selected_option == "shop":
            pass
        # Handle Shop action
        # Update embed description or other embed properties as needed

        elif selected_option == "kraken":
            pass
        # Handle Fight Kraken action
        # Update embed description or other embed properties as needed

        if selected_option == "supplies":
            from nero.supplies import DepositButton
            ship_name = TravelSelect.ship_names.get(zone_level, "Ship")
            ship_gif_url = generate_gif_urls("ships", ship_name)
            embed.description = f"You are repairing a {ship_name}."
            embed.set_image(url=ship_gif_url)

            # Add buttons for depositing poplar strips
            poplar_strip_button_1 = DepositButton(get_emoji('Poplar Strip'), "poplar_strip", 1, self.player,
                                                  self.player_data, discord.ButtonStyle.green)
            poplar_strip_button_5 = DepositButton(get_emoji('Poplar Strip'), "poplar_strip", 5, self.player,
                                                  self.player_data, discord.ButtonStyle.green)

            # Add buttons for depositing cannonballs
            cannonball_button_1 = DepositButton(get_emoji('Cannonball'), "cannonball", 1, self.player, self.player_data,
                                                discord.ButtonStyle.grey)
            cannonball_button_5 = DepositButton(get_emoji('Cannonball'), "cannonball", 5, self.player, self.player_data,
                                                discord.ButtonStyle.grey)

            # Add buttons to the view
            view = discord.ui.View()
            view.add_item(poplar_strip_button_1)
            view.add_item(poplar_strip_button_5)
            view.add_item(cannonball_button_1)
            view.add_item(cannonball_button_5)

            # Respond to interaction with embed and buttons
            await interaction.response.send_message(embed=embed, view=view)

        elif selected_option == "hints":
            pass
        # Handle Got any hints? action
        # Update embed description or other embed properties as needed

        elif selected_option == "spork":
            pass
        # Handle Rusty Spork action
        # Update embed description or other embed properties as needed


class JollyRogerView(discord.ui.View):
    def __init__(self, player, player_data, author_id):
        super().__init__()
        self.add_item(TravelSelect(player, player_data, author_id))
