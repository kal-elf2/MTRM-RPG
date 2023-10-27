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
def create_solid_square(size, color=(25, 25, 25, 255)):
    return Image.new('RGBA', (size, size), color=color)

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
        base_url = generate_urls("Icons", "Backpack2")
        base_img = Image.open(session.get(base_url, stream=True).raw)
        draw = ImageDraw.Draw(base_img)

        # Define the categories and extract the icons based on the order
        categories = ["items", "trees", "herbs", "ore", "armors", "weapons", "shields"]
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

        # Set a fixed starting y_offset for charms from the top of the image
        fixed_distance_from_top = 9.45  # Set this value according to the required distance from the top
        y_offset_for_charms = fixed_distance_from_top * (square_size + line_gap)

        # Define the fixed order and corresponding x_offsets for charms
        charm_order = ["Woodcleaver", "Stonebreaker", "Loothaven", "Mightstone", "Ironhide"]
        charm_offsets = {name: 2 * square_size + i * (square_size + line_gap) for i, name in enumerate(charm_order)}

        # For manual adjustments in terms of number of squares:
        # (dx, dy) adjustments.
        charm_adjustments = {
            "Woodcleaver": (7, 0),
            "Stonebreaker": (7.0, 0),
            "Loothaven": (7, 0),
            "Mightstone": (7, 0),
            "Ironhide": (7, 0),
        }

        charms = getattr(player.inventory, "charms", [])

        for charm in charms:
            if charm.name in charm_offsets:
                # Calculate the adjustment values in terms of pixels
                dx_pixels = charm_adjustments[charm.name][0] * square_size
                dy_pixels = charm_adjustments[charm.name][1] * square_size

                # Overlay the solid square for charm
                square_overlay = create_solid_square(int(square_size))
                base_img.paste(square_overlay,
                               (int(charm_offsets[charm.name] + dx_pixels),
                                int(y_offset_for_charms + dy_pixels)),
                               square_overlay)

                icon_url = generate_urls("Icons", charm.name)
                icon_img = Image.open(session.get(icon_url, stream=True).raw).resize(
                    (int(square_size), int(square_size)))

                adjusted_x_offset = charm_offsets[charm.name] + dx_pixels + (square_size - icon_img.width) / 2
                adjusted_y_offset = y_offset_for_charms + dy_pixels + (square_size - icon_img.height) / 2

                base_img.paste(icon_img, (int(adjusted_x_offset), int(adjusted_y_offset)), icon_img)

                # Drawing the quantity on the image in the top right corner of the charm
                text_width, text_height = draw.textsize(str(charm.stack),
                                                        font=font)  # charm.stack is assumed to be the quantity of charms
                draw.text((adjusted_x_offset + square_size - text_width - 5, adjusted_y_offset + 5), str(charm.stack),
                          fill="white", font=font)

        # Define the fixed order and corresponding x_offsets for potions (after charms)
        potion_order = ["Stamina Potion", "Super Stamina Potion", "Health Potion", "Super Health Potion"]
        potion_offsets = {name: 2 * square_size + i * (square_size + line_gap) for i, name in enumerate(potion_order)}

        # For manual adjustments in terms of number of squares:
        potion_adjustments = {
            "Stamina Potion": (0.4, 0),
            "Health Potion": (0.4, 0),
            "Super Stamina Potion": (0.4, 0),
            "Super Health Potion": (0.4, 0),
        }

        potions = getattr(player.inventory, "potions", [])

        # Set a fixed starting y_offset for potions from the top of the image
        y_offset_for_potions = fixed_distance_from_top * (square_size + line_gap) + 0 * square_size

        for potion in potions:
            if potion.name in potion_offsets:
                # Calculate the adjustment values in terms of pixels
                dx_pixels = potion_adjustments[potion.name][0] * square_size
                dy_pixels = potion_adjustments[potion.name][1] * square_size

                # Overlay the solid square for potion
                square_overlay = create_solid_square(int(square_size))
                base_img.paste(square_overlay,
                               (int(potion_offsets[potion.name] + dx_pixels),
                                int(y_offset_for_potions + dy_pixels)),
                               square_overlay)

                icon_url = generate_urls("Icons", potion.name)
                icon_img = Image.open(session.get(icon_url, stream=True).raw).resize(
                    (int(square_size), int(square_size)))

                adjusted_x_offset = potion_offsets[potion.name] + dx_pixels + (square_size - icon_img.width) / 2
                adjusted_y_offset = y_offset_for_potions + dy_pixels + (square_size - icon_img.height) / 2

                base_img.paste(icon_img, (int(adjusted_x_offset), int(adjusted_y_offset)), icon_img)

                # Drawing the quantity on the image in the top right corner of the potion
                text_width, text_height = draw.textsize(str(potion.stack), font=font)
                draw.text((adjusted_x_offset + square_size - text_width - 5, adjusted_y_offset + 5), str(potion.stack),
                          fill="white", font=font)

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
        equipped_charm_position = (x_offset_start - 3.36 * square_size, y_offset_start + 4.3 * square_size)  # Adjust position as needed

        equipped_positions = [
            equipped_weapon_position,
            equipped_shield_position,
            equipped_charm_position,
        ]

        equipped_items = [equipped_weapon, equipped_shield, equipped_charm]

        for i, item in enumerate(equipped_items):
            from citadel.crafting import Weapon
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

                if isinstance(equipped_weapon, Weapon) and equipped_weapon.wtype == 'Bow':
                    arrow_url = generate_urls("Icons", "Arrow")
                    arrow_img = Image.open(session.get(arrow_url, stream=True).raw).resize(
                        (int(square_size), int(square_size)))

                    # Create a colored square for the Arrow background
                    arrow_bg_square = Image.new('RGBA', arrow_img.size, color=(25, 25, 25, 255))

                    # Paste the arrow image on top of the colored square
                    arrow_bg_square.paste(arrow_img, (0, 0), arrow_img)

                    # Placement based on charm's position
                    charm_x, charm_y = equipped_positions[2]
                    arrow_x_offset = charm_x
                    arrow_y_offset = charm_y + 2.11 * square_size
                    base_img.paste(arrow_bg_square, (int(arrow_x_offset), int(arrow_y_offset)), arrow_bg_square)

                    # Define the text to be added
                    text_to_add = "∞"  # Replace with your desired text

                    # Setting font for the text. Use the same font and size as the rest of your code.
                    font = ImageFont.truetype("arial.ttf", 22)  # Adjust the font and size as needed

                    # Calculate the position to place the text in the top right corner of the arrow box
                    text_width, text_height = draw.textsize(text_to_add, font=font)
                    text_x_offset = arrow_x_offset + arrow_img.width - text_width - 5
                    text_y_offset = arrow_y_offset + 5

                    # Add the text to the image
                    draw.text((int(text_x_offset), int(text_y_offset)), text_to_add, fill="white", font=font)

    return base_img
