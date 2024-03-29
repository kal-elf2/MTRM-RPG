import discord
from utils import save_player_data, CommonResponses, refresh_player_from_data
from images.urls import generate_urls
from emojis import get_emoji
from nero.kraken import HuntKrakenButton

class ConfirmSellView(discord.ui.View, CommonResponses):
    def __init__(self, author_id, guild_id, player_data, total_coppers_earned):
        super().__init__()
        self.author_id = author_id
        self.guild_id = guild_id
        self.player_data = player_data
        self.total_coppers_earned = total_coppers_earned

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.blurple, custom_id="confirm_sell_yes")
    async def confirm_sell(self, button: discord.ui.Button, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            return await self.nero_unauthorized_user_response(interaction)

        # Provide feedback to the player
        sell_feedback_embed = discord.Embed(
            title="Ye Sold Yer Booty!",
            description=f"All loot sold for {self.total_coppers_earned:,} {get_emoji('coppers_emoji')}\n\n***Ye be ready to face the Kraken!***",
            color=discord.Color.dark_gold()
        )
        sell_feedback_embed.set_thumbnail(url=generate_urls("nero", "kraken"))
        view = discord.ui.View()
        view.add_item(HuntKrakenButton(self.guild_id, self.player_data, self.author_id))
        await interaction.response.edit_message(embed=sell_feedback_embed, view=view)

    @discord.ui.button(label="No", style=discord.ButtonStyle.grey, custom_id="confirm_sell_no")
    async def cancel_sell(self, button: discord.ui.Button, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            return await self.nero_unauthorized_user_response(interaction)

        cancel_embed = discord.Embed(
            title="Change of heart, matey?",
            description="Arr, looks like ye havin' second thoughts... Come back and see me when ye change yer mind.",
            color=discord.Color.dark_gold()
        )
        cancel_embed.set_thumbnail(url=generate_urls("nero", "confused"))
        await interaction.response.edit_message(embed=cancel_embed, view=None)

class SellAllButton(discord.ui.Button, CommonResponses):
    def __init__(self, label: str, author_id, guild_id, player_data, style=discord.ButtonStyle.blurple):
        super().__init__(style=style, label=label)
        self.author_id = author_id
        self.guild_id = guild_id
        self.player_data = player_data

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            return await self.nero_unauthorized_user_response(interaction)

        # Refresh player object from the latest player data
        player, self.player_data = await refresh_player_from_data(interaction)

        sellable_categories = ["weapons", "armors", "shields", "charms", "potions"]
        total_coppers_earned = 0

        # Iterate over each category and remove items, adding their value to total coppers earned
        for category_name in sellable_categories:
            category_items = getattr(player.inventory, category_name, [])
            for item in list(category_items):
                total_coppers_earned += item.value * item.stack
                category_items.remove(item)

        player.inventory.coppers += total_coppers_earned
        save_player_data(self.guild_id, self.author_id, self.player_data)

        # Confirmation message
        confirm_embed = discord.Embed(
            title="Confirm Sale",
            description=f"Are ye sure ye want to sell all yer loot for {total_coppers_earned:,}{get_emoji('coppers_emoji')}?\n\n***There ain't no going back after this, savvy?***",
            color=discord.Color.dark_gold()
        )
        confirm_embed.set_thumbnail(url=generate_urls("nero", "shop"))
        confirm_view = ConfirmSellView(self.author_id, self.guild_id, self.player_data, total_coppers_earned)
        await interaction.response.edit_message(embed=confirm_embed, view=confirm_view)