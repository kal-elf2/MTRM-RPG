import discord
from utils import load_player_data, save_player_data, send_message, CommonResponses
from exemplars.exemplars import Exemplar
from images.urls import generate_urls
from emojis import get_emoji
import asyncio
from discord.ext import commands
from random import choice, randint
import math

class ConfirmSellView(discord.ui.View, CommonResponses):
    def __init__(self, author_id, guild_id, player_data):
        super().__init__()
        self.author_id = author_id
        self.guild_id = guild_id
        self.player_data = player_data

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.blurple, custom_id="confirm_sell_yes")
    async def confirm_sell(self, button: discord.ui.Button, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            return await self.nero_unauthorized_user_response(interaction)

        player_data = load_player_data(self.guild_id, self.author_id)
        player = Exemplar(player_data["exemplar"], player_data["stats"], player_data["inventory"])
        sellable_categories = ["weapons", "armors", "shields", "charms", "potions"]
        total_coppers_earned = 0

        # Iterate over each category and remove items, adding their value to total coppers earned
        for category_name in sellable_categories:
            category_items = getattr(player.inventory, category_name, [])
            for item in list(category_items):
                total_coppers_earned += item.value * item.stack
                category_items.remove(item)

        player.inventory.coppers += total_coppers_earned
        save_player_data(self.guild_id, self.author_id, player_data)

        # Provide feedback to the player
        sell_feedback_embed = discord.Embed(
            title="Ye Sold Yer Booty!",
            description=f"All loot sold for {total_coppers_earned:,} {get_emoji('coppers_emoji')}\n\n***Ye be ready to face the Kraken!***",
            color=discord.Color.dark_gold()
        )
        sell_feedback_embed.set_thumbnail(url=generate_urls("nero", "kraken"))
        view = discord.ui.View()
        view.add_item(HuntKrakenButton(self.guild_id, self.player_data, self.author_id))
        await interaction.response.edit_message(embed=sell_feedback_embed, view=view)

    @discord.ui.button(label="No", style=discord.ButtonStyle.grey, custom_id="confirm_sell_no")
    async def cancel_sell(self, button: discord.ui.Button, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            return await self.nero_unauthorized_user_response(interaction)

        cancel_embed = discord.Embed(
            title="Change of heart, matey?",
            description="Arr, looks like ye had second thoughts. Come back and see me when ye change yer mind.",
            color=discord.Color.dark_gold()
        )
        cancel_embed.set_thumbnail(url=generate_urls("nero", "confused"))
        await interaction.response.edit_message(embed=cancel_embed, view=None)

class SellAllButton(discord.ui.Button, CommonResponses):
    def __init__(self, label: str, author_id, guild_id, player_data, style=discord.ButtonStyle.blurple):
        super().__init__(style=style, label=label)
        self.author_id = author_id
        self.guild_id = guild_id
        self.player_data = player_data

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            return await self.nero_unauthorized_user_response(interaction)

        # Confirmation message
        confirm_embed = discord.Embed(
            title="Confirm Sale",
            description="Are ye sure ye want to sell all yer loot?\n\n***There ain't no going back after this, savvy?***",
            color=discord.Color.dark_gold()
        )
        confirm_embed.set_thumbnail(url=generate_urls("nero", "gun "))
        confirm_view = ConfirmSellView(self.author_id, self.guild_id, self.player_data)
        await interaction.response.edit_message(embed=confirm_embed, view=confirm_view)

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
            f"{get_emoji('Cannonball')} **{cannonball_count}** Cannonballs."
        )
        embed = discord.Embed(title="There She Blows!", description=description, color=discord.Color.dark_gold())
        embed.set_image(url=generate_urls("nero", "kraken"))
        embed.set_thumbnail(url=generate_urls("Kraken", self.ship_direction))
        return embed

    @staticmethod
    def send_initial_embed():
        """Generates the battle embed based on the current state."""
        embed = discord.Embed(
            title="To Battle Stations!",
            description=f"Steady, matey! Ready the cannons and keep your eye on the horizon.\n\n"
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

        # Adjust the cannon's angle within bounds (e.g., 0 to 90 degrees)
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
    def __init__(self, author_id, emoji, aim_angle, ctx, battle_commands, player, player_data):
        super().__init__(style=discord.ButtonStyle.secondary, disabled=False, emoji=emoji)
        self.author_id = author_id
        self.aim_angle = aim_angle
        self.ctx = ctx
        self.battle_commands = battle_commands
        self.player = player
        self.player_data = player_data

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        if not self.battle_commands.kraken_visible:
            await interaction.response.send_message("Ye cannot see the Kraken! Wait for it to resurface.", ephemeral=True)
            return

        # Check and update cannonball inventory in shipwreck
        cannonball_count = self.player_data['shipwreck'].get('Cannonball', 0)
        if cannonball_count > 0:
            self.player_data['shipwreck']['Cannonball'] -= 1
            self.disabled = True  # Disable the button after firing
            hit = check_hit(self.battle_commands.kraken_distance, self.aim_angle)

            if hit:
                response = "Direct hit! The Kraken roars in fury."
            else:
                response = "Miss! The Kraken dives deep, readying its next attack."

            await interaction.response.edit_message(content=response, view=None)  # Remove the view to disable the button
            # Update the embed to show "Kraken, Looking" and the new cannonball count
            embed = discord.Embed(
                title="There She Blows!",
                description=f"{response}\n\n{get_emoji('Cannonball')} **{self.player_data['shipwreck'].get('Cannonball', 0)}** Cannonballs left in shipwreck.",
                color=discord.Color.dark_gold()
            )
            embed.set_image(url=generate_urls("Kraken", "Looking"))
            await self.battle_commands.battle_message.edit(embed=embed)

            # Move the Kraken after a short delay
            asyncio.create_task(self.battle_commands.move_kraken(self.ctx, self.player_data))
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
        self.add_item(AimButton(label="⬆️", author_id=self.author_id, battle_commands=self.battle_commands, angle_change=5, ctx=self.ctx, player_data=player_data))
        self.add_item(FireButton(emoji=get_emoji('Cannonball'), author_id=self.author_id, aim_angle=self.battle_commands.cannon_angle, ctx=None, battle_commands=self.battle_commands, player=self.player, player_data=player_data))
        self.add_item(AimButton(label="⬇️", author_id=self.author_id, battle_commands=self.battle_commands, angle_change=-5, ctx=self.ctx, player_data=player_data))


# Helper function to calculate the projectile range
def calculate_range(angle_degrees, velocity=100):
    angle_radians = math.radians(angle_degrees)
    g = 9.8  # acceleration due to gravity in m/s^2
    return (velocity ** 2) * math.sin(2 * angle_radians) / g

# Helper function to check if the angle results in a hit
def check_hit(kraken_distance, player_angle, velocity=100):
    calculated_distance = calculate_range(player_angle, velocity)
    # Define a tolerance window for hitting the target
    lower_bound = kraken_distance * 0.9
    upper_bound = kraken_distance * 1.1
    return lower_bound <= calculated_distance <= upper_bound



def setup(bot):
    bot.add_cog(BattleCommands(bot))