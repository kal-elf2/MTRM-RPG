import discord
from utils import load_player_data, save_player_data, send_message, CommonResponses
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
        self.cannon_angle = 45
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

    def create_battle_embed(self, ctx, player_data):
        # Calculate the correct angle for a hit based on the Kraken's distance
        correct_angle = self.find_correct_angle(self.kraken_distance)
        print(correct_angle)
        """Generates the battle embed based on the current state, including Kraken's direction and distance, and shows current cannonball count in the shipwreck."""
        # Access the cannonball count from the shipwreck in player_data
        cannonball_count = player_data['shipwreck'].get('Cannonball', 0)
        description = (
            f"**The Kraken is `{self.kraken_direction}` at `{self.kraken_distance}` meters.**\n\n"
            f"**Cannon angle:** {self.cannon_angle}°\n"
            f"{get_emoji('Cannonball')} **{cannonball_count}**"
        )
        # Prepare the Kraken's health bar
        kraken_health_bar = self.kraken.health_bar()

        embed = discord.Embed(title="There She Blows!", description=description, color=discord.Color.dark_gold())
        # Add field for Kraken's health using the same format as in the FireButton's response
        kraken_name = "Kraken"  # Adjust if you have a variable for Kraken's name
        embed.add_field(name=f"{kraken_name}'s Health",
                        value=f"{get_emoji('heart_emoji')} {self.kraken.health}/{self.kraken.max_health}\n{kraken_health_bar}",
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

    async def move_kraken(self, ctx, player_data):
        """Randomly moves the Kraken and notifies players of its new position."""
        self.kraken_visible = False
        await asyncio.sleep(randint(5, 12))  # Kraken temporarily disappears
        await self.set_kraken_direction()  # Randomly set the new direction and distance for the Kraken
        self.kraken_visible = True

        # Update the battle_message with the new Kraken position and state
        if self.battle_message:
            await self.battle_message.edit(embed=self.create_battle_embed(ctx, player_data))

    @commands.slash_command(name="kraken", description="Initiate a battle with the Kraken!")
    async def kraken(self, ctx):
        player_data = load_player_data(ctx.guild_id, ctx.author.id)
        player = Exemplar(player_data["exemplar"], player_data["stats"], player_data["inventory"])

        # Check if player's location is 'kraken'
        if player_data['location'] != 'kraken':
            embed = discord.Embed(
                title="Ye Be Not Ready!",
                description="Ahoy! It seems ye are not ready to enter the waters of the Kraken. Come see me at the Jolly Roger. ",
                color=discord.Color.dark_gold()
            )
            embed.set_image(
                url=generate_urls("nero", "confused"))
            await ctx.respond(embed=embed, ephemeral=True)
            return

        await ctx.respond(f"{ctx.author.mention} sails into Kraken-infested waters...")

        # Set the Kraken's direction and distance
        await self.set_kraken_direction()

        self.battle_message = await send_message(ctx, self.send_initial_embed())

        # Wait for 5 seconds before updating the embed
        await asyncio.sleep(5)

        # Edit the original battle_message with the updated embed
        await self.battle_message.edit(embed=self.create_battle_embed(ctx, player_data))

        # Prepare views for steering and aiming
        steering_view = SteeringView(author_id=str(ctx.author.id), battle_commands=self, ctx=ctx, player_data=player_data)
        aiming_view = AimingView(author_id=str(ctx.author.id), battle_commands=self, ctx=ctx, player=player, player_data=player_data)

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
            await self.battle_commands.battle_message.edit(embed=self.battle_commands.create_battle_embed(self.ctx, self.player_data))

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
        new_angle = max(0, min(90, self.battle_commands.cannon_angle + self.angle_change))
        self.battle_commands.cannon_angle = new_angle

        # Update the battle message to reflect the new cannon angle
        if self.battle_commands.battle_message:
            await self.battle_commands.battle_message.edit(embed=self.battle_commands.create_battle_embed(self.ctx, self.player_data))

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
                "Keep yer eyes on the compass, matey! Use the ⬅️ and ➡️ buttons to steer the ship true! We've no time for dalliance!"),
            color=discord.Color.dark_gold()
        )
        embed.set_thumbnail(url=generate_urls("nero", "confused"))

        # Send the embed as an ephemeral message
        await interaction.response.send_message(embed=embed, ephemeral=True)


class FireButton(discord.ui.Button, CommonResponses):
    def __init__(self, author_id, emoji, battle_commands, player, player_data, ctx):
        super().__init__(style=discord.ButtonStyle.secondary, disabled=False, emoji=emoji)
        self.author_id = author_id
        self.battle_commands = battle_commands
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

        if self.battle_commands.ship_direction != self.battle_commands.kraken_direction:
            await interaction.response.send_message("Miss! Ye must face the Kraken directly to hit it.", ephemeral=True)
            return

        # This response is to acknowledge the button press interaction if no prior response was made
        await interaction.response.defer()

        cannonball_count = self.player_data['shipwreck'].get('Cannonball', 0)
        if cannonball_count > 0:
            self.player_data['shipwreck']['Cannonball'] -= 1

            hit, distance_difference = check_hit(self.battle_commands.kraken_distance, self.battle_commands.cannon_angle)
            if hit:
                damage = calculate_damage(distance_difference)
                self.battle_commands.kraken.take_damage(damage)
                response = f"Direct hit! Damage dealt: {damage}."
            else:
                overshoot_message = "overshot" if distance_difference > 0 else "undershot"
                response = f"Miss! Ye {overshoot_message} the Kraken by {abs(distance_difference):.2f} meters."

            # Prepare the Kraken's health bar
            kraken_health_bar = self.battle_commands.kraken.health_bar()

            # Get the existing embed from the message to preserve other embed data
            existing_embed = self.battle_commands.battle_message.embeds[0]

            # Modify the existing embed description with the new response
            existing_embed.description = f"{response}\n\n{get_emoji('Cannonball')} **{self.player_data['shipwreck'].get('Cannonball', 0)}** Cannonballs left in shipwreck."

            # Add or update the Kraken's health field
            kraken_name = "Kraken"  # Change this to your Kraken's name variable if different
            existing_embed.clear_fields()  # Clear existing fields to avoid duplicating them
            existing_embed.add_field(name=f"{kraken_name}",
                                     value=f"{get_emoji('heart_emoji')} {self.battle_commands.kraken.health}/{self.battle_commands.kraken.max_health}\n{kraken_health_bar}",
                                     inline=False)

            # Edit the original message with the updated embed
            await self.battle_commands.battle_message.edit(embed=existing_embed)

            # Optional: Move the Kraken or handle the end of the battle if the Kraken is defeated
            if self.battle_commands.kraken.is_alive():
                asyncio.create_task(self.battle_commands.move_kraken(self.ctx, self.player_data))
            else:
                # Handle victory conditions, if applicable
                pass
        else:
            await interaction.response.send_message("Ye have no cannonballs left in the shipwreck!", ephemeral=True)

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
    def __init__(self, author_id, battle_commands, ctx, player, player_data):
        super().__init__()
        self.author_id = author_id
        self.battle_commands = battle_commands
        self.ctx = ctx
        self.player = player
        self.player_data = player_data
        self.add_item(AimButton(label="⬆️", author_id=self.author_id, battle_commands=battle_commands, angle_change=5,
                                ctx=self.ctx, player_data=player_data))
        self.add_item(FireButton(emoji=get_emoji('Cannonball'), author_id=self.author_id, battle_commands=battle_commands,
                       player=self.player, player_data=player_data, ctx=self.ctx))
        self.add_item(AimButton(label="⬇️", author_id=self.author_id, battle_commands=battle_commands, angle_change=-5,
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
    bar_length = 25  # Fixed bar length
    health_percentage = current / max_health
    filled_length = round(bar_length * health_percentage)

    # Calculate how many '▣' symbols to display
    filled_symbols = '◼' * filled_length

    # Calculate how many '-' symbols to display
    empty_symbols = '◻' * (bar_length - filled_length)
    return filled_symbols + empty_symbols

def calculate_damage(distance_difference):
    accuracy = max(0, 1 - abs(distance_difference) / 200)  # Scaling factor
    return round(100 + (accuracy * 250))  # Min damage + scaled portion of max additional damage


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