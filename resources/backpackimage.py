from PIL import Image, ImageDraw, ImageFont
from images.urls import generate_urls
import requests
from exemplars.exemplars import Exemplar

ZONE_LEVEL_TO_RARITY = {
            1: "Common",
            2: "Uncommon",
            3: "Rare",
            4: "Epic",
            5: "Legendary"
        }

def generate_backpack_image(interaction):
    from utils import load_player_data

    guild_id = interaction.guild.id
    author_id = str(interaction.user.id)
    player_data = load_player_data(guild_id)

    player = Exemplar(player_data[author_id]["exemplar"],
                      player_data[author_id]["stats"],
                      player_data[author_id]["inventory"])

    # Prepare base image
    base_url = generate_urls("Icons", "Backpack")
    base_img = Image.open(requests.get(base_url, stream=True).raw)
    draw = ImageDraw.Draw(base_img)

    # Define the categories and extract the icons based on the order
    categories = ["items", "trees", "herbs", "ore", "gems", "potions", "armors", "weapons", "shields", "charms"]
    # Adjusting the icons extraction:
    icons = []
    for category in categories:
        category_items = getattr(player.inventory, category, [])
        icons.extend([(item, item.stack) for item in category_items])

    square_size = 1.075 * 72
    line_gap = 0.08 * 72

    x_offset_start = 7.925 * square_size
    y_offset_start = 1.95 * square_size

    x_offset, y_offset = x_offset_start, y_offset_start
    row_items = 0

    # Setting font for the quantity. You can adjust the size and font type as required.
    font = ImageFont.truetype("arial.ttf", 15)

    for item_obj, quantity in icons:
        zone_level = getattr(item_obj, "zone_level", None)
        rarity_image = None

        if zone_level and zone_level in ZONE_LEVEL_TO_RARITY:
            rarity_name = ZONE_LEVEL_TO_RARITY[zone_level]
            rarity_url = generate_urls("Icons", rarity_name)
            rarity_image = Image.open(requests.get(rarity_url, stream=True).raw).resize(
                (int(square_size / 3), int(square_size / 3)))

        if row_items == 7:
            x_offset = x_offset_start
            y_offset += square_size + line_gap
            row_items = 0

        icon_url = generate_urls("Icons", item_obj.name)
        icon_img = Image.open(requests.get(icon_url, stream=True).raw).resize((int(square_size), int(square_size)))

        centered_x_offset = x_offset + (square_size - icon_img.width) / 2
        centered_y_offset = y_offset + (square_size - icon_img.height) / 2

        base_img.paste(icon_img, (int(centered_x_offset), int(centered_y_offset)), icon_img)

        # Drawing the quantity on the image in the top right corner
        text_width, text_height = draw.textsize(str(quantity), font=font)
        draw.text((x_offset + square_size - text_width - 5, y_offset + 5), str(quantity), fill="white", font=font)

        # If there's a rarity image, paste it in the bottom left corner of the item square
        if rarity_image:

            base_img.paste(rarity_image, (int(centered_x_offset), int(centered_y_offset + 2 * square_size / 3)),
                           rarity_image)

        x_offset += square_size + line_gap
        row_items += 1

    base_img.save('backpack_with_items.png')
    return base_img
