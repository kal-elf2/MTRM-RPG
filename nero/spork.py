import discord
from utils import CommonResponses, save_player_data, refresh_player_from_data, get_server_setting
from emojis import get_emoji
from images.urls import generate_urls
from discord.ext import commands
from discord import Embed, ButtonStyle

class RustySporkDialogView(discord.ui.View):
    def __init__(self, player, author_id, player_data, current_offer=0):
        super().__init__()
        self.player = player
        self.author_id = author_id
        self.player_data = player_data
        self.current_offer = current_offer
        self.offers = [1000, 5000, 10000, 100000]
        self.dialogues = [
            f"Arrr, what's this? A {get_emoji('Rusty Spork')}**Rusty Spork** ye say? Seems fit only for the fish, but... for a few coppers, I might just find a nook for it among me oddities...",
            "Hold fast, me hearties! What if... aye, what if this spork were the very thing to scratch that spot on me back no hand nor hook could reach? Worth a bit more gold to ponder its possibilities...",
            "Ye've sparked me curiosity! Imagine, this spork as the master key to the legendary locker of Davy Jones, or perhaps a utensil fit for the merfolk's feast. 'Tis a fancy worth a few more coins...",
            "Avast, me pondering's turned to a fever! This spork, worthless to most, might just be the crowning jewel of me collection of naval nonsense. A king's ransom for it, and not a copper less!"
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
        updated_description = f"{context_message}\n\n{self.dialogues[offer_index]} \n\n### **What do ye say... {offer_formatted}{get_emoji('coppers_emoji')} for it?!**"
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
                RustySporkFinalAcceptButton(f"Accept Coppers", self.player, self.author_id,
                                            self.player_data))
            self.add_item(
                RustySporkGiveForFreeButton("Give it for Free", self.player, self.author_id, self.player_data))

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
            self.player.inventory.add_coppers(get_server_setting(interaction.guild_id, 'spork_value'))
            save_player_data(interaction.guild_id, self.author_id, self.player_data)
            formatted_spork_value = "{:,.0f}".format(get_server_setting(interaction.guild_id, 'spork_value'))
            confirmation_embed = discord.Embed(
                title="Transaction Complete",
                description=f"Ahoy! A treasure beyond measure! I know just where this will fit on me ship.\n\nCaptain Nero gleefully snatches the {get_emoji('Rusty Spork')} Rusty Spork and **tosses you a hefty bag of {formatted_spork_value}{get_emoji('coppers_emoji')}**",
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

class RustySporkGiveForFreeButton(discord.ui.Button, CommonResponses):
    def __init__(self, label, player, author_id, player_data):
        super().__init__(style=discord.ButtonStyle.grey, label=label)
        self.player = player
        self.author_id = author_id
        self.player_data = player_data

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Display the generosity confirmation dialog
        generosity_embed = discord.Embed(
            title="By the stars, ye're a generous soul!",
            description="Ye're set on givin' it away without takin' a single Copper? A rare heart ye have, indeed! Are ye certain, matey?",
            color=discord.Color.gold()
        )
        generosity_embed.set_image(url=generate_urls('nero', 'confused'))
        generosity_view = RustySporkGenerosityConfirmationView(self.player, self.author_id, self.player_data)
        await interaction.response.edit_message(embed=generosity_embed, view=generosity_view)

class RustySporkGenerosityConfirmationView(discord.ui.View):
    def __init__(self, player, author_id, player_data):
        super().__init__()
        self.player = player
        self.author_id = author_id
        self.player_data = player_data
        self.add_item(RustySporkGenerosityYesButton(self.player, self.author_id, self.player_data))
        self.add_item(RustySporkGenerosityNoButton(self.player, self.author_id, self.player_data))

class RustySporkGenerosityYesButton(discord.ui.Button, CommonResponses):
    def __init__(self, player, author_id, player_data):
        super().__init__(style=discord.ButtonStyle.blurple, label="Yes")
        self.player = player
        self.author_id = author_id
        self.player_data = player_data

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Remove the Rusty Spork from the inventory
        self.player.inventory.remove_item("Rusty Spork", 1)

        # Set parchment_received to True in the player_data
        self.player_data['battle_actions']['parchment_received'] = True

        # Update player data to reflect changes in inventory
        save_player_data(interaction.guild_id, self.author_id, self.player_data)

        # Show the final message from Captain Nero about receiving the special item
        generosity_confirmed_embed = discord.Embed(
            title="Aye, I'll take this curious piece off yer hands...",
            description=(
                "In the spirit of yer grand heartiness, take this parchment in return. It's no treasure to me eyes, but perhaps ye'll find its secrets worth more than gold.\n\n***Type `/secret` to inspect further.***"),
            color=discord.Color.dark_gold()
        )
        generosity_confirmed_embed.set_thumbnail(url=generate_urls("nero", "cryptic"))
        await interaction.response.edit_message(embed=generosity_confirmed_embed, view=None)

class RustySporkGenerosityNoButton(discord.ui.Button, CommonResponses):
    def __init__(self, player, author_id, player_data):
        super().__init__(style=discord.ButtonStyle.secondary, label="No")
        self.player = player
        self.author_id = author_id
        self.player_data = player_data

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Emotional refusal message from Captain Nero
        refusal_embed = discord.Embed(
            title="Stop Playin' with Me Emotions!",
            description=("Yarrr, ye be a real jester, eh? Comin' here, makin' generous offers, then pullin' "
                         "them back like the sea's tide. Come back and see me when yer feelin' like makin' a trade, "
                         "lest ye be walkin' the plank for playin' with me heart."),
            color=discord.Color.dark_gold()
        )
        refusal_embed.set_thumbnail(url=generate_urls("nero", "mad"))

        # Close the view (remove all buttons)
        for item in self.view.children:
            item.disabled = True

        await interaction.response.edit_message(embed=refusal_embed, view=self.view)

class RustySporkCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Reveal secrets that have been gathered.")
    async def secret(self, ctx):

        # Refresh player object from the latest player data
        player, player_data = await refresh_player_from_data(ctx)

        # Check if player data exists for the user
        if not player_data:
            embed = Embed(title="Captain Ner0",
                          description="Arr! What be this? No record of yer adventures? Start a new game with `/newgame` before I make ye walk the plank.",
                          color=discord.Color.dark_gold())
            embed.set_thumbnail(url=generate_urls("nero", "confused"))
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if not player_data['battle_actions'].get('parchment_received', False):
            embed = Embed(title="Captain Ner0",
                          description="Yarrr, it seems ye haven't got any secrets to unveil just yet. Perhaps there's something ye've missed along the way?",
                          color=discord.Color.dark_gold())
            embed.set_thumbnail(url=generate_urls("nero", "confused"))
            await ctx.respond(embed=embed, ephemeral=True)
            return

        # Display parchment with unveil option if materium is sufficient
        embed = Embed(title="Parchment",
                      description=f"The parchment glows faintly, hinting at secrets untold.\n\n**{get_emoji('Materium')} 20 Materium will unveil its mysteries...**",
                      color=discord.Color.dark_gold())
        embed.set_image(url=generate_urls("nero", "cryptic"))

        # Check if parchment already unveiled
        if player_data['battle_actions'].get('parchment_unveiled', False):
            secrets = [
                player_data['battle_actions']['grab_action'],
                player_data['battle_actions']['mast_action'],
                player_data['battle_actions']['swallow_action'],
            ]
            secret_message = '... '.join(secrets)

            # Craft a reminder of the unveiled secrets
            reminder_message = Embed(
                title="Whispers of Fate Resound",
                description=(
                    f"*The secrets once veiled by shadow and time have been laid bare, their power entrusted to you. "
                    f"As the tides of destiny converge, remember the words that pierce the darkness:\n## **{secret_message}**\n\n "
                    f"These are not merely words, but keys to the final lock, the last stand against the abyssal maw. "
                    f"The Kraken waits in the deep, its challenge unending. "
                    f"Arm yourself with this knowledge, for the storm's eye watches, and the final battle draws near.*"
                ),
                color=discord.Color.dark_gold()
            )
            reminder_message.set_thumbnail(
                url=generate_urls("nero", "cryptic"))

            await ctx.respond(embed=reminder_message, ephemeral=True)

        else:
            view = UnveilParchmentView(player, player_data, str(ctx.author.id), ctx.guild.id)
            await ctx.respond(embed=embed, view=view, ephemeral=True)

class UnveilParchmentView(discord.ui.View):
    def __init__(self, player, player_data, author_id, guild_id):
        super().__init__()
        self.player = player
        self.player_data = player_data
        self.author_id = author_id
        self.guild_id = guild_id

        enough_materium = player.inventory.materium >= 20

        # Initialize the button with the correct attributes
        self.unveil_button = discord.ui.Button(
            label="Reveal Secret",
            style=ButtonStyle.blurple,
            emoji=get_emoji('Materium'),
            custom_id="unveil_parchment",
            disabled=not enough_materium
        )
        # Link the callback function directly using a method reference
        self.unveil_button.callback = self.unveil_parchment_callback
        self.add_item(self.unveil_button)

    async def unveil_parchment_callback(self, interaction: discord.Interaction):
        # Deduct Materium and update the battle actions
        self.player.inventory.materium -= 20
        self.player_data['battle_actions']['parchment_unveiled'] = True

        secrets = [
            self.player_data['battle_actions'].get('grab_action'),
            self.player_data['battle_actions'].get('mast_action'),
            self.player_data['battle_actions'].get('swallow_action'),
        ]
        secret_message = '... '.join(secrets)

        save_player_data(self.guild_id, self.author_id, self.player_data)

        # Disable the button after use
        self.unveil_button.disabled = True

        # Ensure the view reflects the button's new state
        await interaction.response.edit_message(view=self)

        embed = Embed(
            title="The Echoes of the Deep",
            description=(
                f"*As the ink fades and the truths emerge, the shadows whisper of a force beneath the waves. "
                f"In the abyss where darkness dwells, the Kraken stirs, its eyes like voids. "
                f"The secret to quell the beast lies within:\n## **{secret_message}**\n\n"
                f"Three keys to bind the tempest's might, whispered by the ancients, now yours to wield. "
                f"Use them when the sea turns wrathful, for only then can the storm be silenced.*\n\n"
                f"*Revisit at any time with `/secret`.*"
            ),
            color=discord.Color.dark_gold()
        )
        embed.set_thumbnail(url=generate_urls("nero", "cryptic"))

        # Send the embed in a follow-up message
        await interaction.followup.send(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(RustySporkCog(bot))
