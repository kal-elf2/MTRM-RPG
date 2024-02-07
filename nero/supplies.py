import discord
from utils import save_player_data, CommonResponses
from emojis import get_emoji
from images.urls import generate_gif_urls, generate_urls

class DepositButton(discord.ui.Button, CommonResponses):
    def __init__(self, emoji, item_name, amount, player, player_data, author_id, style, disabled=False):
        super().__init__(style=style, label=f"x {amount}", emoji=emoji, disabled=disabled)
        self.item_name = item_name
        self.amount = amount
        self.player = player
        self.player_data = player_data
        self.author_id = author_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        from nero.options import TravelSelect
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        zone_level = self.player.stats.zone_level
        ship_name = TravelSelect.ship_names.get(zone_level, "Ship")
        ship_gif_url = generate_gif_urls("ships", ship_name)
        color_mapping = {
            1: 0x969696,
            2: 0x15ce00,
            3: 0x0096f1,
            4: 0x9900ff,
            5: 0xfebd0d
        }
        embed_color = color_mapping.get(zone_level)

        # Deduct from player's inventory
        self.player.inventory.remove_item(self.item_name, self.amount)

        # Update shipwreck quantities
        current_amount = self.player_data.get('shipwreck', {}).get(self.item_name, 0)
        self.player_data['shipwreck'][self.item_name] = current_amount + self.amount

        # Save the updated player data
        save_player_data(interaction.guild.id, self.author_id, self.player_data)

        # Define required_amount for max limit check
        required_amount = 25 * zone_level if zone_level < 5 else float('inf')

        # Recalculate the updated counts from shipwreck and inventory AFTER updating
        poplar_count_shipwreck = self.player_data['shipwreck'].get('Poplar Strip', 0)
        cannonball_count_shipwreck = self.player_data['shipwreck'].get('Cannonball', 0)
        poplar_count_inventory = self.player.inventory.get_item_quantity('Poplar Strip')
        cannonball_count_inventory = self.player.inventory.get_item_quantity('Cannonball')

        nero_embed_sent = False
        nero_message = ""

        # Adjust the Nero message as follows
        if zone_level < 5 and poplar_count_shipwreck >= required_amount and cannonball_count_shipwreck >= required_amount:
            nero_message = "Yarr! The ship is full to the brim! Come visit me again at the Jolly Roger to hunt down that kraken!"
            nero_embed_sent = True
        elif zone_level == 5 and (
                poplar_count_shipwreck >= required_amount or cannonball_count_shipwreck >= required_amount):
            nero_message = "Aye! Ye've gathered enough to face the kraken, but the sea be treacherous! Stock up as much as ye can carry!"
            nero_embed_sent = True

        # Update the part where you decide to send the Nero message or update the embed
        if nero_embed_sent:
            nero_embed = discord.Embed(
                title="Captain Ner0",
                description=nero_message,
                color=discord.Color.dark_gold()
            )
            nero_embed.set_thumbnail(url=generate_urls("nero", "welcome"))
            await interaction.followup.send(embed=nero_embed, ephemeral=True)

        # Proceed with updating the supply counts and button states
        max_deposit_text = f"(Minimum: {zone_level * 25})" if zone_level == 5 else f"(Required: {required_amount})"
        embed = discord.Embed(title=f"{ship_name} Supplies", color=embed_color)
        embed.set_image(url=ship_gif_url)
        embed.add_field(
            name="Backpack",
            value=f"{get_emoji('Poplar Strip')} **{poplar_count_inventory}**\n{get_emoji('Cannonball')} **{cannonball_count_inventory}**",
            inline=True
        )
        embed.add_field(
            name=f"Deposited: {max_deposit_text}",
            value=f"{get_emoji('Poplar Strip')} **{poplar_count_shipwreck}**\n{get_emoji('Cannonball')} **{cannonball_count_shipwreck}**",
            inline=True
        )

        # Dynamically adjust the buttons based on the new item counts
        view=self.view

        for item in view.children:
            if isinstance(item, DepositButton):
                item_quantity = self.player.inventory.get_item_quantity(item.item_name)
                shipwreck_quantity = self.player_data['shipwreck'].get(item.item_name, 0)
                item.disabled = item_quantity < item.amount or (
                            shipwreck_quantity + item.amount > required_amount and zone_level < 5)

        await interaction.edit_original_response(embed=embed, view=self.view)


