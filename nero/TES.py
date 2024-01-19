import discord
from images.urls import generate_urls
from utils import load_player_data, CommonResponses
from exemplars.exemplars import Exemplar
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
import random
from emojis import get_emoji


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

        # Create the game embed with additional description for betting
        game_embed = discord.Embed(title="Three Eyed Snake", color=discord.Color.blue())
        coppers_emoji = get_emoji('coppers_emoji')
        game_embed.description = f"Select how many {coppers_emoji}coppers you want to bet."
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

        # Calculate max bet, rounded down to the nearest multiple of 20
        max_bet = (self.player.inventory.coppers // 20)
        bet_label = f"20x Coppers required (Max: {max_bet})"
        bet_placeholder = f"How many Coppers would you like to wager?)"
        self.bet = discord.ui.InputText(label=bet_label, placeholder=bet_placeholder, style=discord.InputTextStyle.short)
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
        if self.player.inventory.coppers >= bet_amount * 20:
            discord_file = await generate_game_image(interaction, self.player, bet_amount=bet_amount, current_round=0)

            # Update the game view with the bet amount
            self.game_view.bet_amount = bet_amount

            # Create a new embed with the updated image
            game_embed = discord.Embed(title="Three Eyed Snake", color=discord.Color.blue())
            game_embed.set_image(url="attachment://table.png")

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

def get_dice_image_dimensions(dice_rolls, is_nero=False, scale_factor=1.25):
    dimensions = []
    for roll in dice_rolls:
        identifier = f"nero{roll}" if is_nero else str(roll)
        dice_image_url = generate_urls("3ES", identifier)
        dice_image_response = requests.get(dice_image_url)
        dice_image = Image.open(BytesIO(dice_image_response.content))
        width, height = dice_image.size
        scaled_dimensions = (int(width * scale_factor), int(height * scale_factor))
        dimensions.append(scaled_dimensions)  # Scaled (width, height)
    return dimensions

def get_random_dice_positions(box_coords, dice_dimensions):
    x_start, y_start = box_coords[0]
    x_end, y_end = box_coords[1]
    box_width = x_end - x_start
    box_height = y_end - y_start

    total_dice_width = sum(width for width, _ in dice_dimensions)
    total_space_available_x = box_width - total_dice_width

    spacings_x = [random.uniform(0, total_space_available_x / 2) for _ in range(len(dice_dimensions) + 1)]
    total_spacings_x = sum(spacings_x)
    scale_factor_x = total_space_available_x / total_spacings_x
    scaled_spacings_x = [s * scale_factor_x for s in spacings_x]

    positions = []
    current_x = x_start
    for i, (width, height) in enumerate(dice_dimensions):
        current_x += scaled_spacings_x[i]

        # Calculate the maximum possible vertical space, allowing dice to extend 60 pixels below the box
        max_vertical_space = box_height - height
        # Randomize the top spacing within the available vertical space
        top_spacing = random.randint(0, max_vertical_space)

        y_position = y_start + top_spacing

        positions.append((int(current_x), int(y_position)))
        current_x += width

    return positions

async def generate_game_image(interaction, player, player_dice=None, nero_dice=None, bet_amount=None, current_round=0, dice_positions_round1=None, selected_dice=None, nero_reroll_decisions=None):
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

    # Font for player coppers amount
    font_size_xlarge = 75
    font_xlarge = ImageFont.truetype("arial.ttf", font_size_xlarge)

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
    coppers_text_width, _ = draw.textsize(coppers_text, font=font_xlarge)

    # Increase the offset here to move the coppers amount further to the right
    coppers_text_x_offset = 210  # Adjust this value as needed
    coppers_text_x = player_text_x + player_text_width + coppers_text_x_offset

    coppers_text_y = player_text_y - 45  # Vertically align with player's name

    # Load and resize the coppers icon
    coppers_icon_url = generate_urls("Icons", "Coppers")
    coppers_icon_response = requests.get(coppers_icon_url)
    coppers_icon_image = Image.open(BytesIO(coppers_icon_response.content))
    coppers_icon_image = coppers_icon_image.resize((100, 100))

    # Adjust the icon_x_position to align with the updated coppers text position
    icon_x_position = coppers_text_x - 110  # Adjust this value as needed to align the icon with the text
    icon_y_position = coppers_text_y - 10  # Move the icon up slightly

    # Paste the coppers icon and add the text
    table_image.paste(coppers_icon_image, (icon_x_position, icon_y_position), coppers_icon_image)
    draw.text((coppers_text_x, coppers_text_y), coppers_text, fill="white", font=font_xlarge)

    # Font for the round text
    font_size_round = 75
    font_round = ImageFont.truetype("arial.ttf", font_size_round)

    round_text = f"Round {current_round}" if current_round in [1, 2] else ""
    if round_text:
        round_text_x, round_text_y = 20, 20  # Top-left corner
        draw.text((round_text_x, round_text_y), round_text, fill="white", font=font_round)

    if bet_amount:
        formatted_bet_amount = "{:,}".format(bet_amount)  # Formatting the bet amount with commas
        text = "Wager "
        text_width, _ = draw.textsize(text, font=font_xlarge)
        coppers_url = generate_urls("Icons", "Coppers")
        coppers_response = requests.get(coppers_url)

        coppers_image = Image.open(BytesIO(coppers_response.content))
        coppers_image = coppers_image.resize((100, 100))  # Resize as needed
        bet_text = f" {formatted_bet_amount}"
        bet_text_width, _ = draw.textsize(bet_text, font=font_xlarge)

        x_text = table_image.width - text_width - bet_text_width - 175
        y = 10
        draw.text((x_text, y), text, fill="white", font=font_xlarge)
        table_image.paste(coppers_image, (x_text + text_width + 5, y), coppers_image)
        draw.text((x_text + text_width + 80, y), bet_text, fill="white", font=font_xlarge)

    # Define the dimensions and positions for the bounding boxes
    box_width = 850  # Adjust the width
    box_height = 350  # Adjust the height
    top_box_y = 375  # Adjust top box Y position
    bottom_box_y = table_image.height - 325 - box_height  # Adjust bottom box Y position

    # Coordinates for top and bottom boxes
    top_box_coords = ((table_image.width // 2 - box_width // 2, top_box_y),
                      (table_image.width // 2 + box_width // 2, top_box_y + box_height))
    bottom_box_coords = ((table_image.width // 2 - box_width // 2, bottom_box_y),
                         (table_image.width // 2 + box_width // 2, bottom_box_y + box_height))

    # Draw bounding boxes only for rounds 1 and 2
    if current_round in [1, 2]:
        # Bounding box to test
        # draw.rectangle(top_box_coords, outline="black", width=3)
        # draw.rectangle(bottom_box_coords, outline="black", width=3)

        # Retrieve dimensions of Nero's and player's dice
        nero_dice_dimensions = get_dice_image_dimensions(nero_dice, is_nero=True)
        player_dice_dimensions = get_dice_image_dimensions(player_dice, is_nero=False)

        # Generate random positions for Nero's and player's dice within the bounding boxes
        nero_dice_positions = get_random_dice_positions(top_box_coords, nero_dice_dimensions)
        player_dice_positions = get_random_dice_positions(bottom_box_coords, player_dice_dimensions)

        # Use the passed positions for Round 2
        if current_round == 2 and dice_positions_round1 is not None:
            player_dice_positions = dice_positions_round1
            # Update positions for re-rolled dice
            for i, selected in enumerate(selected_dice):
                if selected:  # If dice is re-rolled, generate new position
                    player_dice_positions[i] = \
                    get_random_dice_positions(bottom_box_coords, [player_dice_dimensions[i]])[0]
        else:
            # Generate positions as usual for Round 1
            player_dice_positions = get_random_dice_positions(bottom_box_coords, player_dice_dimensions)

        # Place Nero's dice
        for i, nero_roll in enumerate(nero_dice):
            # Check if it's the first round and if Nero decided to reroll this dice
            if current_round == 1 and nero_reroll_decisions[i]:
                dice_image_url = generate_urls("3ES", f"nero{nero_roll}glow")
            else:
                dice_image_url = generate_urls("3ES", f"nero{nero_roll}")

            dice_image_response = requests.get(dice_image_url)
            dice_image = Image.open(BytesIO(dice_image_response.content))
            dice_image = dice_image.resize(nero_dice_dimensions[i])
            table_image.paste(dice_image, nero_dice_positions[i], dice_image)

        # Place player's dice
        for i, player_roll in enumerate(player_dice):
            dice_image_url = generate_urls("3ES", str(player_roll))
            dice_image_response = requests.get(dice_image_url)
            dice_image = Image.open(BytesIO(dice_image_response.content))

            # Resize the dice image based on the scaled dimensions
            dice_image = dice_image.resize(player_dice_dimensions[i])

            # Paste the resized dice image
            table_image.paste(dice_image, player_dice_positions[i], dice_image)

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
        self.nero_reroll_decisions = [False, False, False]
        self.order = ["111", "666", "555", "444", "333", "222", "66X", "456", "345", "234", "123", "6XX", "Other"]
        self.dice_positions_round1 = None

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

    def store_dice_positions(self, positions):
        self.dice_positions_round1 = positions

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
                item.selected = self.selected_dice[item.index ]

    def reset_and_reroll(self):
        # Check if no dice are selected
        if not any(self.selected_dice):
            # Do not reroll any dice
            pass  # You can simply pass here as you're keeping all dice
        else:
            # Reroll only selected dice
            for i, selected in enumerate(self.selected_dice):
                if selected:
                    self.player_dice[i] = random.randint(1, 6)

        # Reset all selected dice states to False and button styles to grey
        for i in range(len(self.selected_dice)):
            self.selected_dice[i] = False
            dice_button = self.children[i + 1]
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
            # Clear all fields in the embed except for the title
            self.embed.clear_fields()
            self.embed.description = ''

        print(f"Current Round: {self.current_round}")

    def reset_dice_states(self):
        # Reset the selected_dice array and update button styles
        self.selected_dice = [False, False, False]
        for item in self.children:
            if isinstance(item, DiceButton):
                item.style = discord.ButtonStyle.grey
                item.selected = False
    @staticmethod
    def classify_roll(dice):
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

    @staticmethod
    def get_descriptive_roll_name(roll):
        if roll == "111":
            return "**Three Eyed Snake**"
        elif roll == "666":
            return f"**Triple 6***"
        elif roll in ["222", "333", "444", "555"]:
            return f"**3 of a Kind**"
        elif roll in ["123", "234", "345", "456"]:
            return f"**Straight**"
        elif roll == "66X":
            return "**Double 6**"
        elif roll == "6XX":
            return "**Single 6**"
        elif roll == "Other":
            return "Nothing"
        return roll

    @staticmethod
    def get_result_reaction(result, is_win):
        """ Get a custom reaction message based on the result and whether it's a win or a loss. """
        if is_win:
            if result == "111":  # Three Eyed Snake
                return "**Big Crits!**"
            elif result == "666":  # 666
                return "**Amazing win!**"
            elif result in ["555", "444", "333", "222"]:  # 3 of a kind
                return "**Well done!**"
            else:
                return "**Nice!**"
        else:  # In case of a loss
            if result == "111":  # Three Eyed Snake
                return "**Bad beat.**"
            elif result == "666":  # 666
                return "**Yikes.**"
            elif result in ["555", "444", "333", "222"]:  # 3 of a kind
                return "**Ouch.**"
            else:
                return ""  # No specific reaction for other cases

    @staticmethod
    def compare_results(player_result, nero_result):
        # Priority order based on game rules
        order = ["111", "666", "555", "444", "333", "222", "66X", "456", "345", "234", "123", "6XX", "Other"]

        # Check for a tie
        if player_result == nero_result:
            return "tie"

        # Check for a win
        return "win" if order.index(player_result) < order.index(nero_result) else "lose"

    @staticmethod
    def calculate_winnings(result, bet_amount):
        multipliers = {
            "111": 20, "666": 10, "555": 5, "444": 5, "333": 5,
            "222": 5, "66X": 3, "456": 2, "345": 2, "234": 2,
            "123": 2, "6XX": 1
        }
        return bet_amount * multipliers.get(result, 0)

    def nero_decision_logic(self, nero_dice, player_dice, order):
        nero_result = self.classify_roll(nero_dice)
        player_result = self.classify_roll(player_dice)

        reroll_decisions = [True, True, True]  # Default decision to reroll all dice

        # If Nero has a high-ranking hand like a straight or triples, consider keeping it
        if nero_result in ["111", "666", "555", "444", "333", "222", "123", "234", "345", "456"]:
            if order.index(nero_result) <= order.index(player_result):
                return [False, False, False]  # Keep if Nero's hand is equal or better than the player's

        # Prioritize keeping pairs or triples, especially if they could beat the player's roll
        counts = {x: nero_dice.count(x) for x in set(nero_dice)}
        for i, dice_value in enumerate(nero_dice):
            if counts[dice_value] > 1 and order.index(
                    self.classify_roll([dice_value, dice_value, dice_value])) <= order.index(player_result):
                reroll_decisions[i] = False  # Keep dice that are part of a pair or triple

        # Prioritize keeping 6s if it could lead to a higher-ranking hand
        if 6 in nero_dice and counts[6] == 1 and order.index("66X") <= order.index(player_result):
            reroll_decisions = [dice != 6 for dice in nero_dice]

        return reroll_decisions

    def calculate_best_strategy(self, nero_dice, player_dice, order):
        """
        Determine the best strategy for Nero's reroll.
        """
        nero_result = self.classify_roll(nero_dice)
        player_result = self.classify_roll(player_dice)
        reroll_decisions = [True, True, True]

        # If Nero's roll is already winning, no need to reroll
        if order.index(nero_result) < order.index(player_result):
            return [False, False, False]

        # Evaluate each dice for potential high-value combinations
        counts = {x: nero_dice.count(x) for x in set(nero_dice)}
        for i, dice_value in enumerate(nero_dice):
            # Check for potential three of a kind, straights, or "111"
            if self.is_potential_high_value_hand(nero_dice, dice_value, counts):
                reroll_decisions[i] = False
            # Other strategic considerations can be added here

        return reroll_decisions

    @staticmethod
    def is_potential_high_value_hand(dice, dice_value, counts):
        """
        Check if the current dice contributes to a potential high-value hand.
        """
        # Three of a kind
        if counts[dice_value] > 1:
            return True

        # Check for straights or "111"
        if "123" in dice or "234" in dice or "345" in dice or "456" in dice or counts.get(1, 0) == 2:
            return True

        return False

    def nero_reroll(self):
        # Reroll Nero's dice based on decisions made in Round 1
        for i, reroll in enumerate(self.nero_reroll_decisions):
            if reroll:
                self.nero_dice[i] = random.randint(1, 6)

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

        # Check if the player has at least 20 coppers
        if self.player.inventory.coppers < 20:
            # Create the pirate-themed embed
            pirate_embed = discord.Embed(
                title="Captain Ner0's Notice",
                description="Arr matey! Ye need at least 20 coppers to place a wager. Off ye go to gather more booty!",
                color=discord.Color.dark_red()
            )
            # Set the thumbnail to a pirate-themed image
            pirate_thumbnail_url = generate_urls("nero", "confused")
            pirate_embed.set_thumbnail(url=pirate_thumbnail_url)

            # Send the ephemeral message
            await interaction.response.send_message(embed=pirate_embed, ephemeral=True)
        else:
            # Create and send the bet modal
            bet_modal = BetModal(author_id=self.game_view.author_id, player=self.player, game_view=self.game_view)
            await interaction.response.send_modal(bet_modal)

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

        # Defer the response as generating the game image might take time
        await interaction.response.defer()

        # Authorization check
        if str(interaction.user.id) != self.game_view.author_id:
            await self.view.nero_unauthorized_user_response(interaction)
            return

        # Toggle the game round and update button states
        self.game_view.toggle_round()
        self.game_view.update_buttons_for_round()

        if self.game_view.current_round == 1:
            # Roll all dice for both players in Round 1
            self.game_view.player_dice = [random.randint(1, 6) for _ in range(3)]
            self.game_view.nero_dice = [random.randint(1, 6) for _ in range(3)]

            # Make Nero's reroll decisions based on initial roll
            self.game_view.nero_reroll_decisions = self.game_view.nero_decision_logic(
                self.game_view.nero_dice,
                self.game_view.player_dice,
                self.game_view.order
            )

            # Logging for debugging
            print(f"Round 1 - Player's dice: {self.game_view.player_dice}")
            print(f"Round 1 - Initial Nero's dice: {self.game_view.nero_dice}")
            print(f"Round 1 - Nero's reroll decisions: {self.game_view.nero_reroll_decisions}")

        elif self.game_view.current_round == 2:
            # Execute rerolls in Round 2
            self.game_view.reset_and_reroll()
            self.game_view.nero_reroll()

            # Logging for debugging
            print(f"Round 2 - Player's dice: {self.game_view.player_dice}")
            print(f"Round 2 - Nero's dice: {self.game_view.nero_dice}")

        # Determine the game result if it's the end of round 2
        if self.game_view.current_round == 2:
            player_result = self.game_view.classify_roll(self.game_view.player_dice)
            nero_result = self.game_view.classify_roll(self.game_view.nero_dice)
            game_outcome = self.game_view.compare_results(player_result, nero_result)

            player_roll_name = self.game_view.get_descriptive_roll_name(player_result)
            nero_roll_name = self.game_view.get_descriptive_roll_name(nero_result)
            coppers_emoji = get_emoji('coppers_emoji')  # Fetch the emoji

            # Customize the outcome message
            if game_outcome == "tie":
                outcome_message = "It's a draw. No coppers exchanged."
            elif game_outcome == "win":
                win_reaction = GameView.get_result_reaction(player_result, True)
                potential_winnings = "{:,}".format(
                    self.game_view.calculate_winnings(player_result, self.game_view.bet_amount))
                self.game_view.player.inventory.coppers += int(potential_winnings.replace(',', ''))
                if nero_roll_name == "Nothing":
                    outcome_message = f"{win_reaction} Your {player_roll_name} wins. You win {coppers_emoji}{potential_winnings}."
                else:
                    outcome_message = f"{win_reaction} Your {player_roll_name} beats Captain Nero's {nero_roll_name}. You win {coppers_emoji}{potential_winnings}."
            else:  # Nero wins
                loss_reaction = GameView.get_result_reaction(nero_result, False)
                loss = "{:,}".format(self.game_view.calculate_winnings(nero_result, self.game_view.bet_amount))
                self.game_view.player.inventory.coppers -= int(loss.replace(',', ''))
                if player_roll_name == "Nothing":
                    outcome_message = f"{loss_reaction} Captain Nero's {nero_roll_name} wins. You lose {coppers_emoji}{loss}."
                else:
                    outcome_message = f"{loss_reaction} Captain Nero's {nero_roll_name} beats your {player_roll_name}. You lose {coppers_emoji}{loss}."

            # Update the embed with the game outcome
            self.game_view.embed.clear_fields()  # Clear previous fields if any
            self.game_view.embed.add_field(name="Game Outcome", value=outcome_message, inline=False)

        # Generate and send new game image for the current round
        self.game_view.discord_file = await generate_game_image(
            interaction,
            self.game_view.player,
            player_dice=self.game_view.player_dice if self.game_view.current_round in [1, 2] else None,
            nero_dice=self.game_view.nero_dice if self.game_view.current_round in [1, 2] else None,
            bet_amount=self.game_view.bet_amount,
            current_round=self.game_view.current_round,
            dice_positions_round1=self.game_view.dice_positions_round1 if self.game_view.current_round == 2 else None,
            selected_dice=self.game_view.selected_dice, nero_reroll_decisions=self.game_view.nero_reroll_decisions
        )

        self.game_view.embed.title = f"Your Game: Round {self.game_view.current_round}"

        # Check and handle insufficient coppers
        insufficient_coppers = False
        if self.game_view.player.inventory.coppers < (self.game_view.bet_amount * 20):
            insufficient_coppers = True
            self.disabled = True  # Disable the Roll button

        # Edit the original message with the updated embed and file
        await self.game_view.original_interaction.edit_original_response(embed=self.game_view.embed,
                                                                         file=self.game_view.discord_file,
                                                                         view=self.game_view)

        # Save the updated player data
        save_player_data(interaction.guild.id, self.player_data)

        # If player has insufficient coppers, send an ephemeral message
        if insufficient_coppers:
            # Send a nero embed if not enough coppers
            pirate_embed = discord.Embed(
                title="Captain Ner0's Warning",
                description="Arr, ye be runnin' low on coppers! Either lower yer wager or find yerself some more coppers before ye challenge me again!",
                color=discord.Color.red()
            )
            pirate_thumbnail_url = generate_urls("nero", "confused")
            pirate_embed.set_thumbnail(url=pirate_thumbnail_url)
            await interaction.followup.send(embed=pirate_embed, ephemeral=True)