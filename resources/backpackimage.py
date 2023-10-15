from PIL import Image
from images.urls import generate_urls
import requests
from exemplars.exemplars import Exemplar


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

    # Define the categories and extract the icons based on the order
    categories = ["items", "trees", "herbs", "ore", "gems", "potions", "armors", "weapons", "shields", "charms"]
    icons = []
    for category in categories:
        category_items = getattr(player.inventory, category, [])
        icons.extend([item.name for item in category_items])

    # Set the base position for the first item icon
    square_size = 1.075 * 72  # converting inches to pixels (assuming 72 DPI)
    line_gap = 0.08 * 72

    # Estimated starting positions based on the image
    x_offset_start = 7.925 * square_size
    y_offset_start = 1.95 * square_size

    x_offset, y_offset = x_offset_start, y_offset_start
    row_items = 0  # initialize row_items here

    for icon in icons:
        # If a row is filled with 7 items, move to the next row
        if row_items == 7:
            x_offset = x_offset_start
            y_offset += square_size + line_gap
            row_items = 0

        icon_url = generate_urls("Icons", icon)
        icon_img = Image.open(requests.get(icon_url, stream=True).raw).resize((int(square_size), int(square_size)))

        # Calculate the center position for pasting the icon
        centered_x_offset = x_offset + (square_size - icon_img.width) / 2
        centered_y_offset = y_offset + (square_size - icon_img.height) / 2

        base_img.paste(icon_img, (int(centered_x_offset), int(centered_y_offset)), icon_img)

        # Update x_offset and row_items
        x_offset += square_size + line_gap
        row_items += 1

    # Save the final image or return it
    base_img.save('backpack_with_items.png')

    return base_img




