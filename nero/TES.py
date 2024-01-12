import discord
from images.urls import generate_urls
from utils import load_player_data, CommonResponses
from exemplars.exemplars import Exemplar
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests


class TavernSpecialItem:
    def __init__(self):
        self.name = "Three Eyed Snake"

async def handle_three_eyed_snake_selection(interaction: discord.Interaction):
    nero_embed = discord.Embed(
        title="Captain Ner0",
        description=f"Ahoy! Let's play some **Three-Eyed-Snake**, {interaction.user.mention}!",
        color=discord.Color.dark_gold()
    )
    nero_embed.set_image(url=generate_urls("nero", "dice"))

    view = discord.ui.View()
    view.add_item(PlayButton(label="Play", custom_id="play_3es"))
    view.add_item(RulesButton(label="Rules", custom_id="rules_3es"))
    await interaction.response.send_message(embed=nero_embed, view=view, ephemeral=True)


class PlayButton(discord.ui.Button):
    def __init__(self, label, custom_id):
        super().__init__(label=label, custom_id=custom_id, style=discord.ButtonStyle.blurple)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.disabled = True

        # Create a new view and add both the disabled 'Play' button and the active 'Rules' button
        new_view = discord.ui.View()
        new_view.add_item(self)  # Disabled 'Play' button
        new_view.add_item(RulesButton(label="Rules", custom_id="rules_3es"))  # Active 'Rules' button

        player_data = load_player_data(interaction.guild.id)
        player = Exemplar(player_data[str(interaction.user.id)]["exemplar"],
                          player_data[str(interaction.user.id)]["stats"],
                          player_data[str(interaction.user.id)]["inventory"])

        discord_file = await generate_game_image(player.name)
        # Pass the player object to GameView
        game_view = GameView(author_id=str(interaction.user.id), player=player)

        game_embed = discord.Embed(title="Your Game", color=discord.Color.blue())
        game_embed.set_image(url="attachment://table.png")

        # Send the game embed in a new message
        await interaction.followup.send(embed=game_embed, file=discord_file, view=game_view, ephemeral=False)

        # Update the original message with the new view
        await interaction.edit_original_response(view=new_view)


class RulesButton(discord.ui.Button):
    def __init__(self, label, custom_id):
        super().__init__(label=label, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):

        # Construct the embed with rules information
        rules_embed = discord.Embed(
            title="Three-Eyes-Snake Rules",
            description=f"Ahoy! Heed these rules for Three Eyed Snake {interaction.user.mention}. No blubberin' later if ye be outplayed!",
            color=discord.Color.dark_gold()
        )
        rules_embed.set_thumbnail(url=generate_urls("nero", "dice"))
        rules_embed.set_image(url=generate_urls("3ES", "rules"))

        # Send the embed as an ephemeral message
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)

class BetModal(discord.ui.Modal):
    def __init__(self, author_id, player, game_view, *args, **kwargs):
        super().__init__(title="Place Your Bet", *args, **kwargs)
        self.author_id = author_id
        self.player = player
        self.game_view = game_view
        self.bet = discord.ui.InputText(label="How many Coppers would you like to wager?", style=discord.InputTextStyle.short)
        self.add_item(self.bet)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        bet_amount = int(self.bet.value)
        if self.player.inventory.coppers >= bet_amount * 10:
            discord_file = await generate_game_image(self.player.name, bet_amount=bet_amount, round1=True)

            # Create a new embed with the updated image
            game_embed = discord.Embed(title="Your Game", color=discord.Color.blue())
            game_embed.set_image(url="attachment://table.png")

            # Enable the "Roll" button in the GameView
            for item in self.game_view.children:
                if isinstance(item, RollButton):
                    item.disabled = False

            # Edit the original message with the new embed and enabled "Roll" button
            await interaction.edit_original_response(embed=game_embed, view=self.game_view, files=[discord_file])
        else:
            # Send a nero embed if not enough coppers
            thumbnail_url = generate_urls("nero", "confused")
            nero_embed = discord.Embed(
                title="Captain Ner0",
                description="Arr, ye be short on coppers! Can't make a deal without the coin. If ye happen to find some, return here and try again.",
                color=discord.Color.dark_gold()
            )
            nero_embed.set_thumbnail(url=thumbnail_url)
            await interaction.followup.send(embed=nero_embed, ephemeral=True)


async def generate_game_image(player_exemplar, bet_amount=None, round1=False):
    if round1:
        round1_image_url = generate_urls("3ES", "round1")
        round1_image_response = requests.get(round1_image_url)
        table_image = Image.open(BytesIO(round1_image_response.content))
    else:
        table_image_url = generate_urls("3ES", "table")
        table_image_response = requests.get(table_image_url)
        table_image = Image.open(BytesIO(table_image_response.content))

    draw = ImageDraw.Draw(table_image)
    font_size = 70
    font = ImageFont.truetype("arial.ttf", font_size)

    # Load player's exemplar image
    exemplar_image_url = generate_urls("3ES", player_exemplar)
    exemplar_image_response = requests.get(exemplar_image_url)
    exemplar_image = Image.open(BytesIO(exemplar_image_response.content))

    # Resize and position the exemplar image
    exemplar_image = exemplar_image.resize((300, 300))  # Resize as needed
    x_offset = 0  # Adjust this to move left (-) or right (+)
    y_offset = -15  # Adjust this to move up (-) or down (+)
    exemplar_x = table_image.width // 2 - exemplar_image.width // 2 + x_offset
    exemplar_y = table_image.height - exemplar_image.height + y_offset
    table_image.paste(exemplar_image, (exemplar_x, exemplar_y), exemplar_image)

    if bet_amount:
        text = f"WAGER "
        text_width, _ = draw.textsize(text, font=font)
        coppers_url = generate_urls("Icons", "Coppers")
        coppers_response = requests.get(coppers_url)

        coppers_image = Image.open(BytesIO(coppers_response.content))
        coppers_image = coppers_image.resize((75, 75))  # Resize as needed
        bet_text = f" {bet_amount}"
        bet_text_width, _ = draw.textsize(bet_text, font=font)

        x_text = table_image.width - text_width - bet_text_width - 85  # 85 accounts for coppers image width and padding
        y = 10
        draw.text((x_text, y), text, fill="white", font=font)
        table_image.paste(coppers_image, (x_text + text_width + 5, y), coppers_image)
        draw.text((x_text + text_width + 80, y), bet_text, fill="white", font=font)

    # Convert PIL image to Discord file and send it
    with BytesIO() as image_binary:
        table_image.save(image_binary, 'PNG')
        image_binary.seek(0)
        discord_file = discord.File(fp=image_binary, filename='table.png')
    return discord_file

class GameView(discord.ui.View, CommonResponses):
    def __init__(self, author_id, player, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.author_id = author_id
        self.player = player
        self.current_round = 0
        self.round_number = 0

        # Create the 'Bet' button and pass the game_view instance
        self.bet_button = BetButton(label="Bet", style=discord.ButtonStyle.blurple, custom_id="bet_3es", player=self.player, game_view=self)

        # Add the 'Bet' button to the view
        self.add_item(self.bet_button)

        # Add dice buttons with unique custom_ids (pre-disabled)
        dice_emoji = "\U0001F3B2"  # Unicode for dice emoji
        for i in range(3):
            dice_id = f"dice_3es_{i}"  # unique custom_id for each dice button
            dice_button = DiceButton(label=dice_emoji, custom_id=dice_id)
            dice_button.disabled = True  # Set the button as disabled
            self.add_item(dice_button)

        # Add 'Roll' button (pre-disabled)
        roll_button = RollButton(label="Roll", style=discord.ButtonStyle.green, custom_id="roll_3es")
        roll_button.disabled = True  # Set the button as disabled initially for round 0
        self.add_item(roll_button)

    def update_buttons_for_round(self):
        # This function will be used to update button states based on the current round
        for item in self.children:
            if isinstance(item, RollButton):
                item.disabled = False if self.current_round > 0 else True  # Enable "Roll" button for rounds 1 and 2
            elif isinstance(item, BetButton):
                item.disabled = False if self.current_round == 0 or self.current_round == 2 else True  # Enable "Bet" button for round 0 and round 2
            elif isinstance(item, DiceButton):
                item.disabled = False if self.current_round == 1 else True  # Enable dice buttons for round 1
    def toggle_round(self):
        # This function will toggle between rounds (0, 1, 2)
        if self.current_round == 0:
            self.current_round = 1
        elif self.current_round == 1:
            self.current_round = 2
        else:
            self.current_round = 1  # Re-enter round 1 after round 2
        print(f"Current Round: {self.current_round}")  # Print current round for troubleshooting

class BetButton(discord.ui.Button, CommonResponses):
    def __init__(self, label, custom_id, player, game_view, *args, **kwargs):
        super().__init__(label=label, custom_id=custom_id, *args, **kwargs)
        self.player = player
        self.game_view = game_view

    async def callback(self, interaction: discord.Interaction):
        # Authorization check
        if str(interaction.user.id) != self.view.author_id:
            await self.view.nero_unauthorized_user_response(interaction)
            return

        # Create and send the bet modal
        bet_modal = BetModal(author_id=self.view.author_id, player=self.player, game_view=self.game_view)

        await interaction.response.send_modal(bet_modal)

class DiceButton(discord.ui.Button, CommonResponses):
    def __init__(self, label, custom_id, style=discord.ButtonStyle.grey):
        super().__init__(label=label, custom_id=custom_id, style=style)

    async def callback(self, interaction: discord.Interaction):
        # Authorization check
        if str(interaction.user.id) != self.view.author_id:
            await self.view.nero_unauthorized_user_response(interaction)
            return
        # Logic for dice button


class RollButton(discord.ui.Button, CommonResponses):
    def __init__(self, label, custom_id, style=discord.ButtonStyle.green):
        super().__init__(label=label, custom_id=custom_id, style=style)

    async def callback(self, interaction: discord.Interaction):
        # Authorization check
        if str(interaction.user.id) != self.view.author_id:
            await self.view.nero_unauthorized_user_response(interaction)
            return

        # Toggle rounds
        self.view.toggle_round()

        # Update button states based on the current round
        self.view.update_buttons_for_round()

        # Logic for roll button (you can implement your logic here)

        # Update the message with the modified view
        await interaction.response.edit_message(view=self.view)




