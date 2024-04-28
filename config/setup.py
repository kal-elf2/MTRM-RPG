from discord import Embed
import discord
from discord import ButtonStyle
from discord.ui import View
import datetime
from discord.ext import commands
from utils import load_player_data, save_player_data, CommonResponses, refresh_player_from_data
from images.urls import generate_urls

class PrivateGameView(View, CommonResponses):
    def __init__(self, user_id: str, author_id):
        super().__init__()
        self.user_id = user_id
        self.author_id = author_id

    @discord.ui.button(label="Secret Cove", style=ButtonStyle.blurple, emoji="🔒", custom_id="private_play")
    async def play_privately(self, button, interaction):

        if str(interaction.user.id) != self.author_id:
            return await self.nero_unauthorized_user_response(interaction)

        # Retrieve active threads in the channel that are not archived and match the naming convention
        existing_threads = [t for t in interaction.channel.threads if
                            t.name.startswith(f"{interaction.user.display_name}-private") and not t.archived]

        if existing_threads:
            thread = existing_threads[0]  # Get the first active thread
            # Ensure the user is added back with permissions to read and send messages
            await thread.add_user(interaction.user)
            button.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(
                f"You already have an active private session here: {thread.mention}. You've been added back to it, so feel free to continue your adventure!", ephemeral=True)
            return

        # Generate a unique identifier using the current timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        thread_name = f"{interaction.user.display_name}-private-{timestamp}"

        # Create a private thread in the channel the command was used
        thread = await interaction.channel.create_thread(
            name=thread_name,
            auto_archive_duration=4320,  # 3 days
            type=discord.ChannelType.private_thread
        )
        # Add the user to the thread explicitly, even if they're the creator, to handle any permissions issues preemptively
        await thread.add_user(interaction.user)

        # Create a custom embed message to welcome the user to their private game session
        welcome_embed = discord.Embed(
            title="Welcome to Your Secret Cove!",
            description=f"Ahoy, {interaction.user.mention}! Yer private game session is ready.",
            color=discord.Color.dark_gold()
        )
        welcome_embed.set_image(
            url=generate_urls("nero", "welcome"))

        # Send the embed to the newly created thread
        await thread.send(embed=welcome_embed)

        # Update the button to be disabled and update the original message
        button.disabled = True
        await interaction.response.edit_message(view=self)  # This updates the message if it's the first response

        # Inform the user with a follow-up message in the main channel, if necessary
        await interaction.followup.send(f"Private thread created: {thread.mention}", ephemeral=True)

        # Stop the view to prevent further interactions
        self.stop()

class TeleportModal(discord.ui.Modal):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(title="Teleport Player", *args, **kwargs)
        self.bot = bot

        self.discord_id = discord.ui.InputText(
            label="Player's Discord ID",
            placeholder="Enter the Discord ID here...",
            style=discord.InputTextStyle.short
        )
        self.add_item(self.discord_id)

    async def callback(self, interaction: discord.Interaction):
        discord_id = self.discord_id.value.strip()
        if not discord_id.isdigit():
            await interaction.response.send_message("Invalid ID: IDs must be numeric.", ephemeral=True)
            return

        player_data = load_player_data(interaction.guild_id, discord_id)
        if player_data is None:
            await interaction.response.send_message("No player data found for the given ID.", ephemeral=True)
            return

        user = await self.bot.fetch_user(discord_id)  # Fetch the user object using the discord ID
        if user is None:
            await interaction.response.send_message("No user found with the given Discord ID.", ephemeral=True)
            return

        player_data["location"] = None
        save_player_data(interaction.guild_id, discord_id, player_data)

        # Use user.mention to mention the user in the response
        await interaction.response.send_message(f"{user.mention} has been teleported to neutral ground.", ephemeral=True)

class SetupCog(commands.Cog, CommonResponses):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Start a private game session.")
    async def private(self, ctx):


        # Refresh player object from the latest player data
        _, player_data = await refresh_player_from_data(ctx)

        if not player_data:
            embed = Embed(title="Captain Ner0",
                          description="Arr! What be this? No record of yer adventures? Start a new game with `/newgame` before I make ye walk the plank.",
                          color=discord.Color.dark_gold())
            embed.set_thumbnail(url=generate_urls("nero", "confused"))
            await ctx.respond(embed=embed, ephemeral=True)
            return

        # Determine the image and the specific part of the message based on the exemplar selection
        if player_data["exemplar"] == "elf":
            image_url = generate_urls("nero", "laugh")
            description = (f"Of course ye want to play privately, {ctx.user.mention}. Yer a *bloody elf*! "
                           "Skulking about like a leaf in the wind. "
                           "Well, if ye insist on hiding, click the button below. "
                           "Let's see if ye can prove yer worth away from prying eyes!")
        else:
            image_url = generate_urls("nero", "laugh")
            description = (f"Arr! Playing privately, are we, {ctx.user.mention}? What's the matter, scared of a little company? "
                           "Ye're acting just like those elf cowards. "
                           "Well, if ye insist on hiding from prying eyes, click the button below. ")

        # Create the ephemeral embed message asking if they want to create a private thread
        embed = Embed(
            title="Captain Ner0's Private Invitation",
            description=description,
            color=discord.Color.dark_gold()
        )
        embed.set_thumbnail(url=image_url)

        # Instantiate the view with the ID of the user who invoked the command
        view = PrivateGameView(user_id=ctx.user.id, author_id=ctx.user.id)

        # Send the ephemeral message with the button to the user
        await ctx.respond(embed=embed, view=view, ephemeral=False)

    @commands.slash_command(name="teleport", description="Teleport a player to a neutral location.")
    @commands.has_permissions(administrator=True)
    async def teleport(self, ctx):
        await ctx.send_modal(TeleportModal(self.bot))

def setup(bot):
    bot.add_cog(SetupCog(bot))