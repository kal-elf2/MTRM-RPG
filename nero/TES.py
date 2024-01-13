import discord
from images.urls import generate_urls
from utils import load_player_data, CommonResponses
from exemplars.exemplars import Exemplar
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
import random


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

        discord_file = await generate_game_image(interaction, player)
        # Pass the player object to GameView
        game_view = GameView(author_id=str(interaction.user.id), player=player, player_data=player_data)

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

        bet_value = self.bet.value.strip()
        if not bet_value.isdigit() or int(bet_value) <= 0:
            # Create the embed
            embed = discord.Embed(
                title="Captain Ner0",
                description="Arr! Enter a positive whole number of coppers for yer wager, savvy?",
                color=discord.Color.dark_gold()
            )

            # Set the thumbnail
            thumbnail_url = generate_urls("nero", "confused")
            embed.set_thumbnail(url=thumbnail_url)

            # Send an ephemeral message if the bet is not a positive whole number
            return await interaction.followup.send(
                embed=embed,
                ephemeral=True
            )

        bet_amount = int(bet_value)
        if self.player.inventory.coppers >= bet_amount * 30:
            discord_file = await generate_game_image(interaction, self.player, bet_amount=bet_amount, current_round=0)

            # Update the game view with the bet amount
            self.game_view.bet_amount = bet_amount

            # Create a new embed with the updated image
            game_embed = discord.Embed(title="Your Game", color=discord.Color.blue())
            game_embed.set_image(url="attachment://table.png")

            print(self.game_view)
            print(game_embed)

            # Initialize GameView with embed and discord_file
            self.game_view.embed = game_embed
            self.game_view.discord_file = discord_file
            self.game_view.original_interaction = interaction

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
                description="Arr, ye be short on coppers! This be a high stakes table. Ye need 20x the wager to play. If ye happen to find some, return here and try again.",
                color=discord.Color.dark_gold()
            )
            nero_embed.set_thumbnail(url=thumbnail_url)
            await interaction.followup.send(embed=nero_embed, ephemeral=True)

async def generate_game_image(interaction, player, bet_amount=None, current_round=0):
    base_image_url = generate_urls("3ES", "table")
    base_image_response = requests.get(base_image_url)
    table_image = Image.open(BytesIO(base_image_response.content))
    draw = ImageDraw.Draw(table_image)

    # Font for Captain Ner0 and player name
    font_size_small = 45
    font_small = ImageFont.truetype("arial.ttf", font_size_small)

    # Font for WAGER text
    font_size_large = 60
    font_large = ImageFont.truetype("arial.ttf", font_size_large)

    # Load player's exemplar image
    exemplar_image_url = generate_urls("3ES", player.name)
    exemplar_image_response = requests.get(exemplar_image_url)
    exemplar_image = Image.open(BytesIO(exemplar_image_response.content))

    # Resize and position the exemplar image
    exemplar_image = exemplar_image.resize((300, 300))  # Resize as needed
    x_offset = 0  # Adjust this to move left (-) or right (+)
    y_offset = -15  # Adjust this to move up (-) or down (+)
    exemplar_x = table_image.width // 2 - exemplar_image.width // 2 + x_offset
    exemplar_y = table_image.height - exemplar_image.height + y_offset
    table_image.paste(exemplar_image, (exemplar_x, exemplar_y), exemplar_image)

    # Positioning and adding "Captain Ner0" at the top
    captain_text = "Captain Ner0"
    captain_text_width, _ = draw.textsize(captain_text, font=font_small)
    captain_text_x = table_image.width // 2 - captain_text_width // 2
    captain_text_y = 258  # Adjust as needed for top positioning
    draw.text((captain_text_x, captain_text_y), captain_text, fill="white", font=font_small)

    # Positioning and adding interaction.user at the bottom
    player_text = interaction.user.display_name
    player_text_width, _ = draw.textsize(player_text, font=font_small)
    player_text_x = table_image.width // 2 - player_text_width // 2
    player_text_y = table_image.height - 87  # Adjust as needed for bottom positioning
    draw.text((player_text_x, player_text_y), player_text, fill="white", font=font_small)

    # Formatting coppers amount with commas
    coppers_text = "{:,}".format(player.inventory.coppers)
    coppers_text_width, _ = draw.textsize(coppers_text, font=font_small)
    coppers_text_x = player_text_x + player_text_width + 175  # 175 pixels to the right of player's name
    coppers_text_y = player_text_y  # Vertically align with player's name

    # Load and resize the coppers icon
    coppers_icon_url = generate_urls("Icons", "Coppers")
    coppers_icon_response = requests.get(coppers_icon_url)
    coppers_icon_image = Image.open(BytesIO(coppers_icon_response.content))
    coppers_icon_image = coppers_icon_image.resize((75, 75))

    # Paste the coppers icon and add the text
    icon_x_position = coppers_text_x - 75  # Adjust the icon position to be to the left of the text
    icon_y_position = coppers_text_y - 15  # Move the icon up by 15 pixels
    table_image.paste(coppers_icon_image, (icon_x_position, icon_y_position), coppers_icon_image)
    draw.text((coppers_text_x, coppers_text_y), coppers_text, fill="white", font=font_small)

    # Font for the round text
    font_size_round = 60
    font_round = ImageFont.truetype("arial.ttf", font_size_round)

    round_text = f"Round {current_round}" if current_round in [1, 2] else ""
    if round_text:
        round_text_x, round_text_y = 20, 20  # Top-left corner
        draw.text((round_text_x, round_text_y), round_text, fill="white", font=font_round)

    if bet_amount:
        text = f"Wager "
        text_width, _ = draw.textsize(text, font=font_large)
        coppers_url = generate_urls("Icons", "Coppers")
        coppers_response = requests.get(coppers_url)

        coppers_image = Image.open(BytesIO(coppers_response.content))
        coppers_image = coppers_image.resize((75, 75))  # Resize as needed
        bet_text = f" {bet_amount}"
        bet_text_width, _ = draw.textsize(bet_text, font=font_large)

        x_text = table_image.width - text_width - bet_text_width - 85  # 85 accounts for coppers image width and padding
        y = 10
        draw.text((x_text, y), text, fill="white", font=font_large)
        table_image.paste(coppers_image, (x_text + text_width + 5, y), coppers_image)
        draw.text((x_text + text_width + 80, y), bet_text, fill="white", font=font_large)

    # Convert PIL image to Discord file and send it
    with BytesIO() as image_binary:
        table_image.save(image_binary, 'PNG')
        image_binary.seek(0)
        discord_file = discord.File(fp=image_binary, filename='table.png')
    return discord_file

class GameView(discord.ui.View, CommonResponses):
    def __init__(self, author_id, player, player_data, bet_amount=0, embed=None, discord_file=None, original_interaction=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.author_id = author_id
        self.player = player
        self.bet_amount = bet_amount
        self.embed = embed
        self.discord_file = discord_file
        self.original_interaction = original_interaction
        self.current_round = 0
        self.round_number = 0
        self.player_dice = [0, 0, 0]
        self.nero_dice = [0, 0, 0]
        self.player_data = player_data

        # Create a list to keep track of the selected state of dice buttons
        self.selected_dice = [False, False, False]

        # Initialize in_round_2 as False
        self.in_round_2 = False

        # Create the 'Bet' button and pass the game_view instance
        self.bet_button = BetButton(label="Bet", style=discord.ButtonStyle.blurple, custom_id="bet_3es", player=self.player, game_view=self)

        # Add the 'Bet' button to the view
        self.add_item(self.bet_button)

        # Add dice buttons with unique custom_ids (pre-disabled)
        dice_emoji = "\U0001F3B2"  # Unicode for dice emoji
        for i in range(3):
            dice_id = f"dice_3es_{i}"  # unique custom_id for each dice button
            dice_button = DiceButton(label=dice_emoji, custom_id=dice_id, index=i)
            dice_button.disabled = True  # Set the button as disabled
            self.add_item(dice_button)

        # Add 'Roll' button (pre-disabled)
        roll_button = RollButton(label="Roll", style=discord.ButtonStyle.green, custom_id="roll_3es", player_data=self.player_data, game_view= self)
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
                # Enable dice buttons for round 1 and toggle their state based on the selected_dice list
                item.disabled = False if self.current_round == 1 else True
                item.selected = self.selected_dice[item.index]

    def reset_and_reroll(self):
        # Check if no dice are selected
        if not any(self.selected_dice):
            # Reroll all dice
            self.player_dice = [random.randint(1, 6) for _ in range(3)]
        else:
            # Reroll only selected dice
            for i, selected in enumerate(self.selected_dice):
                if selected:
                    self.player_dice[i] = random.randint(1, 6)

        # Reset all selected dice states to False and button styles to grey
        for i in range(len(self.selected_dice)):
            self.selected_dice[i] = False
            dice_button = self.children[i + 1]  # Adjust index based on your view's structure
            dice_button.style = discord.ButtonStyle.grey

    # Modify the toggle_round method
    def toggle_round(self):

        if self.current_round == 0:
            self.current_round = 1
        elif self.current_round == 1:
            self.current_round = 2
            self.in_round_2 = True
            self.reset_and_reroll()
        else:
            # Resetting the game to start a new round
            self.current_round = 1
            self.in_round_2 = False
            self.reset_dice_states()

        print(f"Current Round: {self.current_round}")


    def reset_dice_states(self):
        # Reset the selected_dice array and update button styles
        self.selected_dice = [False, False, False]
        for item in self.children:
            if isinstance(item, DiceButton):
                item.style = discord.ButtonStyle.grey
                item.selected = False

    def classify_roll(self, dice):
        counts = {x: dice.count(x) for x in set(dice)}
        if 3 in counts.values():
            number = next(x for x, count in counts.items() if count == 3)
            return f"{number}{number}{number}"
        straights = ["123", "234", "345", "456"]
        sorted_dice = ''.join(map(str, sorted(dice)))
        if sorted_dice in straights:
            return sorted_dice
        if counts.get(6, 0) == 2:
            return "66X"
        if counts.get(6, 0) == 1:
            return "6XX"
        return "Other"

    def compare_results(self, player_result, nero_result):
        # Priority order based on game rules
        order = ["111", "666", "555", "444", "333", "222", "66X", "456", "345", "234", "123", "6XX", "Other"]

        # Check for a tie
        if player_result == nero_result:
            return "tie"

        # Check for a win
        return "win" if order.index(player_result) < order.index(nero_result) else "lose"

    def calculate_winnings(self, result, bet_amount):
        multipliers = {
            "111": 20, "666": 10, "555": 5, "444": 5, "333": 5,
            "222": 5, "66X": 3, "456": 2, "345": 2, "234": 2,
            "123": 2, "6XX": 1
        }
        return bet_amount * multipliers.get(result, 0)

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
        bet_modal = BetModal(author_id=self.game_view.author_id, player=self.player, game_view=self.game_view)

        await interaction.response.send_modal(bet_modal)


# Modify the DiceButton class as follows:
class DiceButton(discord.ui.Button, CommonResponses):
    def __init__(self, label, custom_id, style=discord.ButtonStyle.grey, index=None):
        super().__init__(label=label, custom_id=custom_id, style=style)
        self.index = index  # Store the index of the button

    async def callback(self, interaction: discord.Interaction):
        # Authorization check
        if str(interaction.user.id) != self.view.author_id:
            await self.view.nero_unauthorized_user_response(interaction)
            return

        # Toggle dice selection state within the GameView
        self.view.selected_dice[self.index] = not self.view.selected_dice[self.index]

        # Update button style based on selection state
        self.style = discord.ButtonStyle.red if self.view.selected_dice[self.index] else discord.ButtonStyle.grey

        # Get the corresponding number (or "X") for the button
        number = self.view.player_dice[self.index] if self.view.current_round == 1 else "X"

        # Print whether the dice is selected or deselected, including the corresponding number
        action = "selected" if self.view.selected_dice[self.index] else "deselected"
        print(f"Button {self.index + 1} ({number}) {action}")

        # Update the message with the modified view
        await interaction.response.edit_message(view=self.view)


class RollButton(discord.ui.Button, CommonResponses):
    def __init__(self, label, custom_id, player_data, game_view, style=discord.ButtonStyle.green):
        super().__init__(label=label, custom_id=custom_id, style=style)
        self.player_data = player_data
        self.game_view = game_view

    async def callback(self, interaction: discord.Interaction):
        from utils import save_player_data
        # Authorization check
        if str(interaction.user.id) != self.game_view.author_id:
            await self.view.nero_unauthorized_user_response(interaction)
            return

        # Toggle rounds and update button states
        self.game_view.toggle_round()
        self.game_view.update_buttons_for_round()

        # Roll dice and print results based on the round
        if self.game_view.current_round == 1:
            # Round 1: Roll all dice for both players
            self.game_view.player_dice = [random.randint(1, 6) for _ in range(3)]
            self.game_view.nero_dice = [random.randint(1, 6) for _ in range(3)]
            print(f"Round 1 - Player's dice: {self.game_view.player_dice}")
            print(f"Round 1 - Nero's dice: {self.game_view.nero_dice}")
        elif self.game_view.current_round == 2:
            # Round 2: Reroll happens in toggle_round
            print(f"Round 2 - Player's dice: {self.game_view.player_dice}")
            print(f"Round 2 - Nero's dice: {self.game_view.nero_dice}")

        # Determine the game result if it's the end of round 2
        if self.game_view.current_round == 2:
            player_result = self.game_view.classify_roll(self.game_view.player_dice)
            nero_result = self.game_view.classify_roll(self.game_view.nero_dice)
            game_outcome = self.game_view.compare_results(player_result, nero_result)

            # Update coppers based on game outcome and regenerate game image
            if game_outcome == "tie":
                print("It's a tie! No coppers exchanged.")
            elif game_outcome == "win":
                winnings = self.game_view.calculate_winnings(player_result, self.game_view.bet_amount)
                self.game_view.player.inventory.coppers += winnings
                print(f"You win! Your roll: {player_result}. You win {winnings} coppers.")
            else:
                loss = self.game_view.bet_amount
                self.game_view.player.inventory.coppers -= loss
                print(f"You lose! Your roll: {player_result}. Nero's roll: {nero_result}.")

        # Save the updated player data
        save_player_data(interaction.guild.id, self.player_data)

        # Generate and send new game image for the current round
        self.game_view.discord_file = await generate_game_image(interaction, self.game_view.player,
                                                                current_round=self.game_view.current_round)
        self.game_view.embed.title = f"Your Game: Round {self.game_view.current_round}"

        # Edit the original message with the updated embed and file
        await self.game_view.original_interaction.edit_original_response(embed=self.game_view.embed,
                                                                         file=self.game_view.discord_file,
                                                                         view=self.game_view)

        # Update the message with the modified view
        await interaction.response.edit_message(view=self.game_view)



