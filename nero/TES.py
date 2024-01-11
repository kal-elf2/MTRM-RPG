import discord
from images.urls import generate_urls
from utils import load_player_data, CommonResponses
from exemplars.exemplars import Exemplar


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

        from PIL import Image
        from io import BytesIO
        import requests

        # Load player data
        guild_id = interaction.guild.id
        author_id = str(interaction.user.id)
        player_data = load_player_data(guild_id)
        player = Exemplar(player_data[author_id]["exemplar"],
                          player_data[author_id]["stats"],
                          player_data[author_id]["inventory"])

        # Generate base table image
        table_image_url = generate_urls("3ES", "table")
        table_image_response = requests.get(table_image_url)
        table_image = Image.open(BytesIO(table_image_response.content))

        # Load player's exemplar image
        exemplar_image_url = generate_urls("3ES", player.name)
        exemplar_image_response = requests.get(exemplar_image_url)
        exemplar_image = Image.open(BytesIO(exemplar_image_response.content))

        # Resize and position the exemplar image
        exemplar_image = exemplar_image.resize((300, 300))  # Resize as needed

        # Manual offset adjustments
        x_offset = 0  # Adjust this to move left (-) or right (+)
        y_offset = -15  # Adjust this to move up (-) or down (+)

        # Calculate the position for exemplar image
        exemplar_x = table_image.width // 2 - exemplar_image.width // 2 + x_offset
        exemplar_y = table_image.height - exemplar_image.height + y_offset

        # Paste the exemplar image onto the table image
        table_image.paste(exemplar_image, (exemplar_x, exemplar_y), exemplar_image)

        # Convert PIL image to Discord file
        with BytesIO() as image_binary:
            table_image.save(image_binary, 'PNG')
            image_binary.seek(0)
            discord_file = discord.File(fp=image_binary, filename='table.png')

        # Disable this button and create a new view with it
        self.disabled = True
        new_view = discord.ui.View()
        new_view.add_item(self)  # Add the disabled PlayButton to the new view
        new_view.add_item(RulesButton(label="Rules", custom_id="rules_3es"))  # Assuming RulesButton exists

        # Update the original message with the new view
        await interaction.edit_original_response(view=new_view)

        # Send the generated image in a follow-up message
        game_view = GameView(author_id=str(interaction.user.id))
        await interaction.followup.send(file=discord_file, view=game_view, ephemeral=False)


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
    def __init__(self, *args, **kwargs):
        super().__init__(title="Place Your Bet", *args, **kwargs)

        self.bet = discord.ui.InputText(label="How many Coppers would you like to wager?", style=discord.InputTextStyle.short)
        self.add_item(self.bet)

    async def callback(self, interaction: discord.Interaction):
        from exemplars.exemplars import Exemplar

        # Load player data
        guild_id = interaction.guild.id
        author_id = str(interaction.user.id)
        player_data = load_player_data(guild_id)
        player = Exemplar(player_data[author_id]["exemplar"],
                          player_data[author_id]["stats"],
                          player_data[author_id]["inventory"])

        # Validate and handle the bet
        bet_amount = int(self.bet.value)
        if player.inventory.coppers >= bet_amount:
            # Proceed with the game logic
            pass
        else:
            # Inform the player they don't have enough coppers
            pass

class GameView(discord.ui.View, CommonResponses):
    def __init__(self, author_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.author_id = author_id

        self.add_item(BetButton(label="Bet", style=discord.ButtonStyle.blurple, custom_id="bet_3es"))

        # Add dice buttons with unique custom_ids
        dice_emoji = "\U0001F3B2"  # Unicode for dice emoji
        for i in range(3):
            dice_id = f"dice_3es_{i}"  # unique custom_id for each dice button
            self.add_item(ToggleButton(label=dice_emoji, custom_id=dice_id))

        # Add 'Roll' button
        self.add_item(RollButton(label="Roll", style=discord.ButtonStyle.green, custom_id="roll_3es"))

class BetButton(discord.ui.Button, CommonResponses):
    async def callback(self, interaction: discord.Interaction):
        # Check authorization
        if str(interaction.user.id) != self.view.author_id:
            await self.view.nero_unauthorized_user_response(interaction)
            return

        bet_modal = BetModal()
        await interaction.response.send_modal(bet_modal)

class ToggleButton(discord.ui.Button, CommonResponses):
    def __init__(self, label, custom_id, style=discord.ButtonStyle.grey):
        super().__init__(label=label, custom_id=custom_id, style=style)

    async def callback(self, interaction: discord.Interaction):
        # Check authorization
        if str(interaction.user.id) != self.view.author_id:
            await self.view.nero_unauthorized_user_response(interaction)
            return
        # Future logic for toggle button
        pass

class RollButton(discord.ui.Button, CommonResponses):
    def __init__(self, label, custom_id, style=discord.ButtonStyle.green):
        super().__init__(label=label, custom_id=custom_id, style=style)

    async def callback(self, interaction: discord.Interaction):
        # Check authorization
        if str(interaction.user.id) != self.view.author_id:
            await self.view.nero_unauthorized_user_response(interaction)
            return
        # Placeholder for future logic
        pass




