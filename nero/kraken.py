import discord
from utils import save_player_data, load_player_data, send_message, CommonResponses, refresh_player_from_data
from exemplars.exemplars import Exemplar
from images.urls import generate_urls
from emojis import get_emoji
import asyncio
from discord.ext import commands
from random import choice, randint
import math

class HuntKrakenButton(discord.ui.Button, CommonResponses):
    def __init__(self, guild_id, player_data, author_id):
        super().__init__(style=discord.ButtonStyle.green, label="Hunt Kraken", emoji=f"{get_emoji('kraken')}")
        self.guild_id = guild_id
        self.player_data = player_data
        self.author_id = author_id

        # Initialize the player from player_data
        self.player = Exemplar(self.player_data["exemplar"],
                               self.player_data["stats"],
                               self.player_data["inventory"])

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            return await self.nero_unauthorized_user_response(interaction)

        await interaction.response.defer()

        # Disable the button
        self.disabled = True

        # Update view to disable button
        await interaction.edit_original_response(view=self.view)

        self.player_data["location"] = 'kraken'

        zone_level = self.player.stats.zone_level

        # Handle inventory based on zone level
        if zone_level < 5:
            # Clear inventory for zones 1 through 4
            self.player.inventory.items = []
            self.player.inventory.trees = []
            self.player.inventory.herbs = []
            self.player.inventory.ore = []
            self.player.inventory.armors = []
            self.player.inventory.weapons = []
            self.player.inventory.shields = []
            self.player.inventory.charms = []
            self.player.inventory.potions = []

        else:
            # Subtract one Goblin Crown from the inventory in zone 5
            self.player.inventory.remove_item("Goblin Crown", 1)

        # Save the updated player data
        save_player_data(self.guild_id, self.author_id, self.player_data)

        # Prepare the embed message
        embed = discord.Embed(
            title="Captain Ner0's Call to Arms",
            description=(
                "Ahoy! The dreaded Kraken lurks beneath the waves, a beast most foul and fearsome. "
                "**I will be yer eyes on the sea**, calling out when the Kraken surfaces. "
                "It'll be yer duty to **turn the ship, aim the cannon, and fire with precision!** "
                "Prepare yerself, for the battle will be fierce and the sea shows no mercy. "
                "\n\n### When ye ready to face her, type `/kraken` to begin the battle!"
            ),
            color=discord.Color.dark_gold()
        )

        # Set the thumbnail to the "kraken" image
        thumbnail_url = generate_urls("nero", "kraken")
        embed.set_thumbnail(url=thumbnail_url)


        # Send the embed message as a follow-up to the interaction
        await interaction.followup.send(embed=embed, ephemeral=True)

class BattleCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.kraken_visible = True
        self.kraken_distance = None
        self.kraken_direction = None
        self.ship_direction = "N"
        self.battle_message = None
        self.cannon_angle = 20
        self.kraken = Kraken()

    @staticmethod
    def find_correct_angle(distance, velocity=100):
        g = 9.8  # acceleration due to gravity in m/s^2
        try:
            angle_radians = math.asin(distance * g / velocity ** 2) / 2
            angle_degrees = math.degrees(angle_radians)
            return angle_degrees
        except ValueError:
            # Return None or an appropriate value if the distance is too great for a hit at this velocity
            return None


    async def set_kraken_direction(self):
        directions = ["N", "S", "E", "W", "NW", "NE", "SE", "SW"]
        self.kraken_direction = choice(directions)  # Randomly set the Kraken's direction
        self.kraken_distance = randint(50, 1020)  # Set initial Kraken distance

    def create_battle_embed(self, player_data):

        # Calculate the correct angle for a hit based on the Kraken's distance
        correct_angle = self.find_correct_angle(self.kraken_distance)
        print(correct_angle)

        """Generates the battle embed based on the current state, including Kraken's direction and distance, and shows current cannonball count in the shipwreck."""
        # Description updated to remove the cannon angle part
        description = f"**The Kraken is `{self.kraken_direction}` at `{self.kraken_distance}` meters.**"

        # Access the cannonball count from the shipwreck in player_data
        cannonball_count = player_data['shipwreck'].get('Cannonball', 0)

        # Prepare the Kraken's health bar
        kraken_health_bar = self.kraken.health_bar()

        # Calculate the distance the cannonball will travel
        cannonball_travel_distance = calculate_range(self.cannon_angle, 100)  # Using default velocity of 100

        embed = discord.Embed(title=f"{get_emoji('kraken')} There She Blows {get_emoji('kraken')}", description=description, color=discord.Color.dark_gold())

        # Kraken's health formatted with commas
        kraken_current_health_formatted = f"{self.kraken.health:,}"
        kraken_max_health_formatted = f"{self.kraken.max_health:,}"

        # Add field for cannonball count
        embed.add_field(name="Ammo", value=f"{get_emoji('Cannonball')} **{cannonball_count}**",
                        inline=True)

        # Cannon angle field
        embed.add_field(name="Angle", value=f"{self.cannon_angle}°", inline=True)

        # Cannonball distance field, rounded to a whole number
        embed.add_field(name="Distance", value=f"{round(cannonball_travel_distance)} meters",
                        inline=True)

        # Kraken's health field
        embed.add_field(name=f"Kraken's Health",
                        value=f"{get_emoji('heart_emoji')} {kraken_current_health_formatted}/{kraken_max_health_formatted}\n{kraken_health_bar}",
                        inline=False)

        embed.set_image(url=generate_urls("nero", "kraken"))
        embed.set_thumbnail(url=generate_urls("Kraken", self.ship_direction))


        return embed

    @staticmethod
    def send_initial_embed():
        """Generates the battle embed based on the current state."""
        embed = discord.Embed(
            title="To Battle Stations!",
            description=f"Steady, matey...\n\nReady the cannons and keep your eye on the horizon.\n\n"
                        "**When I call out her position, aim true and fire!**",
            color=discord.Color.dark_gold()
        )
        embed.set_image(url=generate_urls("Kraken", "Looking"))
        return embed

    async def move_kraken(self, player_data):
        """Randomly moves the Kraken and notifies players of its new position."""
        self.kraken_visible = False
        await asyncio.sleep(randint(5, 9))  # Kraken temporarily disappears
        await self.set_kraken_direction()  # Randomly set the new direction and distance for the Kraken
        self.kraken_visible = True

        # Update the battle_message with the new Kraken position and state
        if self.battle_message:
            await self.battle_message.edit(embed=self.create_battle_embed(player_data))

    @commands.slash_command(name="kraken", description="Initiate a battle with the Kraken!")
    async def kraken(self, ctx):
        player_data = load_player_data(ctx.guild_id, ctx.author.id)
        player = Exemplar(player_data["exemplar"], player_data["stats"], player_data["inventory"])
        author_id = str(ctx.author.id)

        # Check if player's location is not 'kraken'
        if player_data['location'] != 'kraken':
            # Nested check if player's location is 'kraken_battle'
            if player_data['location'] == 'kraken_battle':
                embed = discord.Embed(
                    title="Battle's Already Raging!",
                    description="Ye're already clashing with the Kraken, ye salty dog! No time for gabbin'—to battle!",
                    color=discord.Color.dark_gold()
                )
                embed.set_thumbnail(url=generate_urls("nero", "gun"))
                await ctx.respond(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(
                    title="Ye Be Not Ready!",
                    description="Ahoy! It seems ye are not ready to enter the waters of the Kraken. Come see me at the Jolly Roger.",
                    color=discord.Color.dark_gold()
                )
                embed.set_thumbnail(url=generate_urls("nero", "confused"))
                await ctx.respond(embed=embed, ephemeral=True)
            return

        player_data["location"] = "kraken_battle"
        save_player_data(ctx.guild_id, author_id, player_data)

        await ctx.respond(f"{ctx.author.mention} sails into Kraken-infested waters...")

        # Set the Kraken's direction and distance
        await self.set_kraken_direction()

        self.battle_message = await send_message(ctx, self.send_initial_embed())

        # Wait for 5 seconds before updating the embed
        await asyncio.sleep(7)

        # Edit the original battle_message with the updated embed
        await self.battle_message.edit(embed=self.create_battle_embed(player_data))

        # Prepare views for steering and aiming
        steering_view = SteeringView(author_id=str(ctx.author.id), battle_commands=self, ctx=ctx, player_data=player_data)
        aiming_view = AimingView(author_id=str(ctx.author.id), battle_commands=self, ctx=ctx, player=player, player_data=player_data, kraken=self.kraken)

        # Send the views in separate messages to organize them into rows
        await ctx.send(view=steering_view)
        await ctx.send(view=aiming_view)

class SteerButton(discord.ui.Button, CommonResponses):
    def __init__(self, label, author_id, battle_commands, direction_change, ctx, player_data, disabled=False):
        super().__init__(style=discord.ButtonStyle.secondary, label=label, disabled=disabled)
        self.author_id = author_id
        self.battle_commands = battle_commands
        self.direction_change = direction_change
        self.ctx = ctx
        self.player_data = player_data

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        await interaction.response.defer()

        # Update the ship's direction based on the button pressed
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        current_index = directions.index(self.battle_commands.ship_direction)
        new_index = (current_index + self.direction_change) % len(directions)
        self.battle_commands.ship_direction = directions[new_index]

        # Update the battle message's thumbnail to reflect the new direction
        if self.battle_commands.battle_message:
            await self.battle_commands.battle_message.edit(embed=self.battle_commands.create_battle_embed(self.player_data))

class AimButton(discord.ui.Button, CommonResponses):
    def __init__(self, label, author_id, battle_commands, angle_change, ctx, player_data, disabled=False):
        super().__init__(style=discord.ButtonStyle.secondary, label=label, disabled=disabled)
        self.author_id = author_id
        self.battle_commands = battle_commands
        self.angle_change = angle_change
        self.ctx = ctx
        self.player_data = player_data

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        await interaction.response.defer()

        # Update to modify the shared aim_angle
        new_angle = max(0, min(45, self.battle_commands.cannon_angle + self.angle_change))
        self.battle_commands.cannon_angle = new_angle

        # Update the battle message to reflect the new cannon angle
        if self.battle_commands.battle_message:
            await self.battle_commands.battle_message.edit(embed=self.battle_commands.create_battle_embed(self.player_data))

class MiddleSteerButton(discord.ui.Button, CommonResponses):
    def __init__(self, emoji, author_id):
        super().__init__(style=discord.ButtonStyle.secondary, disabled=False, emoji=emoji)
        self.author_id = author_id

    async def callback(self, interaction: discord.Interaction):

        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        embed = discord.Embed(
            title="Captain Nero's Bellow",
            description=(
                f"Keep yer eyes on the compass, {interaction.user.mention}! Use the ⬅️ and ➡️ buttons to steer the ship! We've no time for dalliance!"),
            color=discord.Color.dark_gold()
        )
        embed.set_thumbnail(url=generate_urls("nero", "confused"))

        # Send the embed as an ephemeral message
        await interaction.response.send_message(embed=embed, ephemeral=True)


class FireButton(discord.ui.Button, CommonResponses):
    def __init__(self, author_id, emoji, battle_commands, kraken, player, player_data, ctx):
        super().__init__(style=discord.ButtonStyle.secondary, disabled=False, emoji=emoji)
        self.author_id = author_id
        self.battle_commands = battle_commands
        self.kraken = kraken
        self.player = player
        self.player_data = player_data
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        if not self.battle_commands.kraken_visible:
            await interaction.response.send_message("Ye cannot see the Kraken! Wait for it to resurface.", ephemeral=True)
            return

        await interaction.response.defer()

        cannonball_count = self.player_data['shipwreck'].get('Cannonball', 0)
        if cannonball_count > 0:
            self.player_data['shipwreck']['Cannonball'] -= 1

            # Check if the ship is aiming in the correct general direction
            if self.battle_commands.ship_direction != self.battle_commands.kraken_direction:
                response = f"What were ye aimin' at, {interaction.user.mention}?\nYe weren't even pointing the right direction!\n\nPut down the rum and put yer good eye **on the compass**!"
            else:
                hit, distance_difference = check_hit(self.battle_commands.kraken_distance,
                                                     self.battle_commands.cannon_angle)
                if hit:
                    damage = calculate_damage(distance_difference, self.player.stats.zone_level)
                    self.battle_commands.kraken.take_damage(damage)
                    damage_message = f"\n\n**Ye dealt {damage} damage to the Kraken!**"
                    if damage > 300:
                        response = "Bullseye! Ye could've blinded it with that shot! " + damage_message
                    elif damage > 250:
                        response = "A smashing hit! It's reelin' from that one! " + damage_message
                    elif damage > 200:
                        response = "Ye nicked a tentacle! It's angry now! " + damage_message
                    else:
                        response = "A glancin' blow! Aim better, ye swab! " + damage_message
                else:
                    overshoot_message = "overshot" if distance_difference > 0 else "undershot"
                    rounded_distance = round(abs(distance_difference))
                    response = f"Miss! Ye {overshoot_message} the Kraken by {rounded_distance} meters."

            # Get the existing embed from the message to preserve other embed data
            existing_embed = self.battle_commands.battle_message.embeds[0]

            existing_embed.title = f"She went back under!"

            cannonball_count = self.player_data['shipwreck'].get('Cannonball', 0)
            cannonball_text = "Cannonball" if cannonball_count == 1 else "Cannonballs"

            # Modify the existing embed description with the new response, dynamically adjusting the cannonball text
            existing_embed.description = f"{response}\n\n{get_emoji('Cannonball')} **{format(cannonball_count, ',d')} {cannonball_text} left**"

            # Clear existing fields to avoid duplicating them
            existing_embed.clear_fields()

            # Kraken's health formatted with commas
            kraken_current_health_formatted = f"{self.kraken.health:,}"
            kraken_max_health_formatted = f"{self.kraken.max_health:,}"
            kraken_health_bar = self.kraken.health_bar()

            # Kraken's health field
            existing_embed.add_field(name=f"Kraken's Health",
                                     value=f"{get_emoji('heart_emoji')} {kraken_current_health_formatted}/{kraken_max_health_formatted}\n{kraken_health_bar}",
                                     inline=False)

            # Update the player data and save
            save_player_data(interaction.guild_id, self.author_id, self.player_data)

            # Edit the original message with the updated embed
            await self.battle_commands.battle_message.edit(embed=existing_embed)

            # Optional: Move the Kraken or handle the end of the battle if the Kraken is defeated
            if self.battle_commands.kraken.is_alive():
                asyncio.create_task(self.battle_commands.move_kraken(self.player_data))
            else:
                # Handle victory conditions, if applicable
                pass
        else:
            # Player has run out of cannonballs
            await self.handle_no_cannonballs(interaction)

    async def handle_no_cannonballs(self, interaction: discord.Interaction):
        # Refresh player object from the latest player data
        self.player, self.player_data = await refresh_player_from_data(interaction)

        citadel_names = ["Sun", "Moon", "Earth", "Wind", "Stars"]


        # Colors for each zone
        color_mapping = {
            1: 0x969696,
            2: 0x15ce00,
            3: 0x0096f1,
            4: 0x9900ff,
            5: 0xfebd0d
        }


        if self.player.stats.zone_level < 5:
            # Advance to the next zone
            self.player.stats.zone_level += 1
            self.player_data["stats"]["zone_level"] = self.player.stats.zone_level

            embed_color = color_mapping.get(self.player.stats.zone_level)
            new_zone_index = self.player.stats.zone_level - 1  # Adjust for 0-based indexing

            # Determine citadel name based on the new zone level
            citadel_name = citadel_names[new_zone_index]

            message_title = "We Had to Flee!"
            message_description = (
                f"Arrr, {interaction.user.mention}! Ye ran out of cannonballs! \n\n"
                "That monstrous Kraken nearly had us in its clutches. Luckily this citadel was here when we needed it.\n\n"
                "I'll be seeking out a grander vessel to hold more powder and plunder. Ye best start honing yer skills and pillaging for loot. "
                "Mark me words, the beasts lurking in these waters be ***far deadlier*** than any we've crossed swords with before. Keep a weather eye on the horizon and ready yer cutlass..."
                f"\n\n### Welcome to Zone {self.player.stats.zone_level}:\n## The Citadel of the {citadel_name}"
            )
        else:
            # Stay in zone 5
            message_title = "A Narrow Escape!"
            message_description = (
                "We barely escaped... I could tell we weren't going to make it so I turned her back around "
                "before we got lost to the sea... try bringing more cannonballs next time.\n\n"
                "I'll start repairing the ship. Come back and see me at the **Jolly Roger** when yer ready."
            )
            embed_color = color_mapping.get(self.player.stats.zone_level)
            new_zone_index = self.player.stats.zone_level - 1  # Adjust for 0-based indexing
            citadel_name = citadel_names[new_zone_index]

        self.player_data["location"] = None

        # Update the player data and save
        save_player_data(interaction.guild_id, self.author_id, self.player_data)

        # Send Nero's message
        embed = discord.Embed(
            title=message_title,
            description=message_description,
            color=embed_color
        )
        # Set the image to the citadel they are now in
        embed.set_image(url=generate_urls("Citadel", citadel_name))
        await interaction.followup.send(embed=embed, ephemeral=False)

class SteeringView(discord.ui.View):
    def __init__(self, author_id, battle_commands, ctx, player_data):
        super().__init__()
        self.author_id = author_id
        self.battle_commands = battle_commands
        self.ctx = ctx
        self.player_data = player_data

        # Define direction changes for the left and right buttons
        left_direction_change = -1
        right_direction_change = 1

        # Adjust the SteerButton initialization with new parameters
        self.add_item(SteerButton(label="⬅️", author_id=self.author_id, battle_commands=self.battle_commands, direction_change=left_direction_change, ctx=self.ctx, player_data=self.player_data))
        self.add_item(MiddleSteerButton(emoji=get_emoji('helm'), author_id=self.author_id))
        self.add_item(SteerButton(label="➡️", author_id=self.author_id, battle_commands=self.battle_commands, direction_change=right_direction_change, ctx=self.ctx, player_data=self.player_data))

class AimingView(discord.ui.View):
    def __init__(self, author_id, battle_commands, ctx, player, player_data, kraken):
        super().__init__()
        self.author_id = author_id
        self.battle_commands = battle_commands
        self.ctx = ctx
        self.player = player
        self.player_data = player_data
        self.kraken = kraken
        self.add_item(AimButton(label="⬇️", author_id=self.author_id, battle_commands=battle_commands, angle_change=-2.5,
                      ctx=self.ctx, player_data=player_data))
        self.add_item(FireButton(emoji=get_emoji('Cannonball'), author_id=self.author_id, kraken=self.kraken, battle_commands=battle_commands,
                       player=self.player, player_data=player_data, ctx=self.ctx))
        self.add_item(AimButton(label="⬆️", author_id=self.author_id, battle_commands=battle_commands, angle_change=2.5,
                                ctx=self.ctx, player_data=player_data))


# Helper function to calculate the projectile range
def calculate_range(angle_degrees, velocity=100):
    angle_radians = math.radians(angle_degrees)
    g = 9.8  # acceleration due to gravity in m/s^2
    return (velocity ** 2) * math.sin(2 * angle_radians) / g

# Helper function to check if the angle results in a hit
def check_hit(kraken_distance, player_angle, velocity=100):
    calculated_distance = calculate_range(player_angle, velocity)
    distance_difference = calculated_distance - kraken_distance
    hit = kraken_distance * 0.9 <= calculated_distance <= kraken_distance * 1.1
    return hit, distance_difference

def create_monster_health_bar(current, max_health):
    bar_length = 18  # Fixed bar length
    health_percentage = current / max_health
    filled_length = round(bar_length * health_percentage)

    # Calculate how many '▣' symbols to display
    filled_symbols = '◼' * filled_length

    # Calculate how many '-' symbols to display
    empty_symbols = '◻' * (bar_length - filled_length)
    return filled_symbols + empty_symbols

def calculate_damage(distance_difference, zone_level):
    accuracy = max(0, 1 - abs(distance_difference) / 100)  # Scaling factor
    return round(100 + (accuracy * 250)) * round(1.1**zone_level) # Min damage + scaled portion of max additional damage


class Kraken:
    def __init__(self, max_health=20000):
        self.max_health = max_health
        self.health = max_health

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)

    def is_alive(self):
        return self.health > 0

    def health_bar(self):
        return create_monster_health_bar(self.health, self.max_health)


def setup(bot):
    bot.add_cog(BattleCommands(bot))