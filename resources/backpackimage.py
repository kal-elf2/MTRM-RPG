from PIL import Image, ImageDraw, ImageFont
from images.urls import generate_urls
from requests.sessions import Session
from exemplars.exemplars import Exemplar
from citadel.crafting import ArmorType

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

    with Session() as session:  # Start a session
        # Prepare base image
        base_url = generate_urls("Icons", "Backpack")
        base_img = Image.open(session.get(base_url, stream=True).raw)
        draw = ImageDraw.Draw(base_img)

        # Define the categories and extract the icons based on the order
        categories = ["items", "trees", "herbs", "ore", "potions", "armors", "weapons", "shields", "charms"]
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
            # Streamlined Rarity Image Fetching
            rarity_image = None
            rarity_name = ZONE_LEVEL_TO_RARITY.get(getattr(item_obj, "zone_level", None))
            if rarity_name:
                rarity_url = generate_urls("Icons", rarity_name)
                rarity_image = Image.open(session.get(rarity_url, stream=True).raw).resize(
                    (int(square_size / 3), int(square_size / 3)))

            if row_items == 7:
                x_offset = x_offset_start
                y_offset += square_size + line_gap
                row_items = 0

            icon_url = generate_urls("Icons", item_obj.name)
            icon_img = Image.open(session.get(icon_url, stream=True).raw).resize((int(square_size), int(square_size)))
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

        # Display equipped armor items
        equipped_armor_items = [player.inventory.equipped_armor[ArmorType.CHEST],
                                player.inventory.equipped_armor[ArmorType.GLOVES],
                                player.inventory.equipped_armor[ArmorType.BOOTS]]

        equipped_armor_positions = [
            (x_offset_start - 2.285 * square_size, y_offset_start + 4.28 * square_size),
            (x_offset_start - 2.285 * square_size, y_offset_start + 5.35 * square_size),
            (x_offset_start - 2.285 * square_size, y_offset_start + 6.425 * square_size)
        ]

        for i, armor_item in enumerate(equipped_armor_items):
            if armor_item:
                # Overlay a square of color #191919
                square_overlay = Image.new('RGBA', (int(square_size), int(square_size)), color=(25, 25, 25, 255))
                base_img.paste(square_overlay,
                               (int(equipped_armor_positions[i][0]), int(equipped_armor_positions[i][1])),
                               square_overlay)

                # Fetch the rarity image for equipped items
                rarity_image = None
                rarity_name = ZONE_LEVEL_TO_RARITY.get(getattr(armor_item, "zone_level", None))
                if rarity_name:
                    rarity_url = generate_urls("Icons", rarity_name)
                    rarity_image = Image.open(session.get(rarity_url, stream=True).raw).resize(
                        (int(square_size / 3), int(square_size / 3)))

                # Fetch the armor item image
                icon_url = generate_urls("Icons", armor_item.name)
                icon_img = Image.open(session.get(icon_url, stream=True).raw).resize(
                    (int(square_size), int(square_size)))

                # Paste the armor item image on the base image
                base_img.paste(icon_img, (int(equipped_armor_positions[i][0]), int(equipped_armor_positions[i][1])),
                               icon_img)

                # If there's a rarity image for the equipped item, paste it in the bottom left corner of the item square
                if rarity_image:
                    base_img.paste(rarity_image, (
                        int(equipped_armor_positions[i][0]), int(equipped_armor_positions[i][1] + 2 * square_size / 3)),
                                   rarity_image)

        # Display equipped weapon, shield, and charm
        equipped_weapon = player.inventory.equipped_weapon
        equipped_shield = player.inventory.equipped_shield
        equipped_charm = player.inventory.equipped_charm

        equipped_weapon_position = (x_offset_start - 2.285 * square_size, y_offset_start + 0 * square_size)  # Adjust position as needed
        equipped_shield_position = (x_offset_start - 3.36 * square_size, y_offset_start + 5.35 * square_size)  # Adjust position as needed
        equipped_charm_position = (x_offset_start - 3.36 * square_size, y_offset_start + 4.28 * square_size)  # Adjust position as needed

        equipped_positions = [
            equipped_weapon_position,
            equipped_shield_position,
            equipped_charm_position,
        ]

        equipped_items = [equipped_weapon, equipped_shield, equipped_charm]

        for i, item in enumerate(equipped_items):
            if item:
                # Overlay a square of color #191919
                square_overlay = Image.new('RGBA', (int(square_size), int(square_size)), color=(25, 25, 25, 255))
                base_img.paste(square_overlay,
                               (int(equipped_positions[i][0]), int(equipped_positions[i][1])),
                               square_overlay)

                # Fetch the rarity image for equipped items
                rarity_image = None
                rarity_name = ZONE_LEVEL_TO_RARITY.get(getattr(item, "zone_level", None))
                if rarity_name:
                    rarity_url = generate_urls("Icons", rarity_name)
                    rarity_image = Image.open(session.get(rarity_url, stream=True).raw).resize(
                        (int(square_size / 3), int(square_size / 3)))

                # Fetch the equipped item image
                icon_url = generate_urls("Icons", item.name)
                icon_img = Image.open(session.get(icon_url, stream=True).raw).resize(
                    (int(square_size), int(square_size)))

                # Paste the equipped item image on the base image
                base_img.paste(icon_img, (int(equipped_positions[i][0]), int(equipped_positions[i][1])),
                               icon_img)

                # If there's a rarity image for the equipped item, paste it in the bottom left corner of the item square
                if rarity_image:
                    base_img.paste(rarity_image, (
                        int(equipped_positions[i][0]), int(equipped_positions[i][1] + 2 * square_size / 3)),
                                   rarity_image)

    base_img.save('backpack_with_items.png')
    return base_img
