import discord
from utils import CommonResponses, save_player_data
from emojis import get_emoji
from images.urls import generate_urls
class RustySporkDialogView(discord.ui.View):
    def __init__(self, player, author_id, player_data, current_offer=0):
        super().__init__()
        self.player = player
        self.author_id = author_id
        self.player_data = player_data
        self.current_offer = current_offer
        self.offers = [1000, 5000, 10000, 100000]
        self.dialogues = [
            "Arrr, what's this? A **Rusty Spork** ye say? Looks like a piece o' junk to me. But I suppose I could take it off yer hands for a few coppers...",
            "Hmmm, on second thought, maybe there's some value to it... How's about I up me offer?",
            "Ye drive a hard bargain! How about we make it even more interesting?",
            "Avast! Ye've twisted me arm! I'll offer ye a fortune for it!"
        ]
        self.context_messages = [
            "(*Nero interrupts eagerly*)",
            "(*Doesn't wait for your answer*)",
            "(*Cuts you off, more excited*)",
            "(*Ignores your response, shouting*)"
        ]
        self.add_buttons()

    def update_embed_for_offer(self, embed, offer_index):
        # Format the offer amount with commas
        offer_formatted = "{:,.0f}".format(self.offers[offer_index])
        # Prepend the context message to the embed's description
        context_message = self.context_messages[min(offer_index, len(self.context_messages) - 1)]
        updated_description = f"{context_message}\n\n{self.dialogues[offer_index]} \n\nWhat do ye say... {offer_formatted} {get_emoji('coppers_emoji')} for it?"
        embed.description = updated_description
        return embed

    def add_buttons(self):
        self.clear_items()  # Clear existing buttons
        if self.current_offer < len(self.offers) - 1:
            # Add Yes and No buttons to progress the conversation
            self.add_item(
                RustySporkOfferButton("Yes", self.player, self.author_id, self.player_data, self.current_offer + 1,
                                      self.context_messages))
            self.add_item(
                RustySporkOfferButton("No", self.player, self.author_id, self.player_data, self.current_offer + 1,
                                      self.context_messages))
        else:
            # Add a final accept button
            self.add_item(
                RustySporkFinalAcceptButton(f"Accept Offer", self.player, self.author_id,
                                            self.player_data))

class RustySporkOfferButton(discord.ui.Button, CommonResponses):
    def __init__(self, label, player, author_id, player_data, next_offer, context_messages):
        super().__init__(style=discord.ButtonStyle.blurple, label=label)
        self.player = player
        self.author_id = author_id
        self.player_data = player_data
        self.next_offer = next_offer
        self.context_messages = context_messages

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        new_view = RustySporkDialogView(self.player, self.author_id, self.player_data, self.next_offer)
        new_embed = interaction.message.embeds[0]
        # Getting the appropriate context message
        context_message = self.context_messages[min(self.next_offer - 1, len(self.context_messages) - 1)]

        # Prepend the context message to the embed's description
        updated_description = f"{context_message}\n\n{new_embed.description}"
        new_embed.description = updated_description

        # Update the embed for the next offer
        updated_embed = new_view.update_embed_for_offer(new_embed, self.next_offer)

        await interaction.response.edit_message(embed=updated_embed, view=new_view)

class RustySporkFinalAcceptButton(discord.ui.Button, CommonResponses):
    def __init__(self, label, player, author_id, player_data):
        super().__init__(style=discord.ButtonStyle.blurple, label=label)
        self.player = player
        self.author_id = author_id
        self.player_data = player_data

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        successful_sell = self.player.inventory.sell_item("Rusty Spork", 1)
        if successful_sell:
            self.player.inventory.add_coppers(100000)
            save_player_data(interaction.guild_id, self.author_id, self.player_data)
            confirmation_embed = discord.Embed(
                title="Transaction Complete",
                description=f"Captain Nero gleefully snatches the {get_emoji('Rusty Spork')} Rusty Spork and tosses you a hefty bag of 100,000 {get_emoji('coppers_emoji')}",
                color=discord.Color.dark_gold()
            )
            pirate_thumbnail_url = generate_urls("nero", "shop")
            confirmation_embed.set_thumbnail(url=pirate_thumbnail_url)

        else:
            confirmation_embed = discord.Embed(
                title="Transaction Failed",
                description="Something went awry, and the transaction couldn't be completed.",
                color=discord.Color.red()
            )

        await interaction.response.edit_message(embed=confirmation_embed, view=None)
