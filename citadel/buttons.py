import discord
import asyncio
from discord.ext import commands
import numpy as np
from citadel.crafting import CraftingSelect, create_crafting_stations
from images.urls import generate_urls
from citadel.grains import HarvestButton
from discord import Embed
from utils import CommonResponses, load_player_data, save_player_data, refresh_player_from_data

class CitadelCog(commands.Cog, CommonResponses):
    def __init__(self, bot):
        self.bot = bot


    @commands.slash_command(description="Visit the Citadel!")
    async def citadel(self, ctx):

        from utils import load_player_data
        from exemplars.exemplars import Exemplar

        guild_id = ctx.guild.id
        author_id = str(ctx.author.id)
        player_data = load_player_data(guild_id, author_id)

        # Check if player data exists for the user
        if not player_data:
            embed = Embed(title="Captain Ner0",
                          description="Arr! What be this? No record of yer adventures? Start a new game with `/newgame` before I make ye walk the plank.",
                          color=discord.Color.dark_gold())
            embed.set_thumbnail(url=generate_urls("nero", "confused"))
            await ctx.respond(embed=embed, ephemeral=True)
            return

        player = Exemplar(player_data["exemplar"],
                          player_data["stats"],
                          player_data["inventory"])

        # Check the player's health before starting a battle
        if player.stats.health <= 0:
            embed = Embed(title="Captain Ner0",
                          description="Ahoy! Ye can't do that ye bloody ghost! Ye must travel to the 🪦 `/cemetery` to reenter the realm of the living.",
                          color=discord.Color.dark_gold())
            embed.set_thumbnail(url=generate_urls("nero", "confused"))
            await ctx.respond(embed=embed, ephemeral=True)
            return

        # Check for battle flag and return if battling
        if player_data["location"] == "battle":
            await self.ongoing_battle_response(ctx)
            return

        if player_data["location"] == "kraken":
            await self.during_kraken_battle_response(ctx)
            return

        player_data["location"] = "citadel"
        save_player_data(guild_id, author_id, player_data)

        # Initialize the rows with the author_id
        row1 = ForgeRow(ctx, author_id=author_id)
        row2 = TanneryRow(player_data, ctx, author_id=author_id)
        row3 = BreadRow(player_data, ctx, author_id=author_id)
        row4 = WheatRow(player_data, ctx, author_id=author_id)
        row5 = TravelRow(player_data, ctx, author_id=author_id)

        await ctx.respond(view=row1)
        await ctx.send(view=row2)
        await ctx.send(view=row3)
        await ctx.send(view=row4)
        await ctx.send(view=row5)

class ForgeRow(discord.ui.View, CommonResponses):
    def __init__(self, player_data, ctx=None, author_id=None):
        super().__init__(timeout=None)
        self.player_data = player_data
        self.ctx = ctx
        self.author_id = author_id
        self.crafting_select = None


    def update_or_add_crafting_select(self, recipes, interaction):

        if self.crafting_select:
            self.remove_item(self.crafting_select)
        self.crafting_select = CraftingSelect(recipes, interaction, self.author_id)
        self.add_item(self.crafting_select)

    @discord.ui.button(label="🔨 Forge", custom_id="citadel_forge", style=discord.ButtonStyle.blurple)
    async def forge(self, button, interaction):
        # Check if the user who interacted is the same as the one who initiated the view
        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player data to prevent exploit after citadel exit.
        self.player_data = load_player_data(interaction.guild_id, self.author_id)

        # Check if the player is not in the citadel
        if self.player_data["location"] != "citadel":
            await self.not_in_citadel_response(interaction)
            return

        station = create_crafting_stations(interaction, "forge")
        self.update_or_add_crafting_select(station, interaction)
        await interaction.response.edit_message(content="Choose an item to Forge:", view=self)

    @discord.ui.button(label="🪓 Wood Shop", custom_id="citadel_woodshop", style=discord.ButtonStyle.blurple)
    async def wood_shop(self, button, interaction):
        # Check if the user who interacted is the same as the one who initiated the view
        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player data to prevent exploit after citadel exit.
        self.player_data = load_player_data(interaction.guild_id, self.author_id)

        # Check if the player is not in the citadel
        if self.player_data["location"] != "citadel":
            await self.not_in_citadel_response(interaction)
            return

        station = create_crafting_stations(interaction, "woodshop")
        self.update_or_add_crafting_select(station, interaction)
        await interaction.response.edit_message(content="Choose an item from the Wood Shop:", view=self)

    @discord.ui.button(label="🏹 Archery Stand", custom_id="citadel_archery", style=discord.ButtonStyle.blurple)
    async def archery_stand(self, button, interaction):
        # Check if the user who interacted is the same as the one who initiated the view
        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player data to prevent exploit after citadel exit.
        self.player_data = load_player_data(interaction.guild_id, self.author_id)

        # Check if the player is not in the citadel
        if self.player_data["location"] != "citadel":
            await self.not_in_citadel_response(interaction)
            return

        station = create_crafting_stations(interaction, "archery_stand")
        self.update_or_add_crafting_select(station, interaction)
        await interaction.response.edit_message(content="Choose an item from the Archery Stand:", view=self)


class TanneryRow(discord.ui.View, CommonResponses):
    def __init__(self, player_data, ctx=None, author_id=None):
        super().__init__(timeout=None)
        self.player_data = player_data
        self.ctx = ctx
        self.author_id = author_id
        self.crafting_select = None

    def update_or_add_crafting_select(self, recipes, interaction):
        if self.crafting_select:
            self.remove_item(self.crafting_select)
        self.crafting_select = CraftingSelect(recipes, interaction, self.author_id)
        self.add_item(self.crafting_select)

    @discord.ui.button(label="🐄 Tannery", custom_id="citadel_tannery", style=discord.ButtonStyle.blurple)
    async def tannery(self, button, interaction):
        # Check if the user who interacted is the same as the one who initiated the view
        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player object from the latest player data
        _, self.player_data = await refresh_player_from_data(self, self.ctx)

        # Check if the player is not in the citadel
        if self.player_data["location"] != "citadel":
            await self.not_in_citadel_response(interaction)
            return

        station = create_crafting_stations(interaction, "tannery")
        self.update_or_add_crafting_select(station, interaction)
        await interaction.response.edit_message(content="Choose an item from the Tannery:", view=self)

    @discord.ui.button(label="🧵 Clothiery", custom_id="citadel_clothiery", style=discord.ButtonStyle.blurple)
    async def clothiery(self, button, interaction):
        # Check if the user who interacted is the same as the one who initiated the view
        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player object from the latest player data
        _, self.player_data = await refresh_player_from_data(self, self.ctx)

        # Check if the player is not in the citadel
        if self.player_data["location"] != "citadel":
            await self.not_in_citadel_response(interaction)
            return

        station = create_crafting_stations(interaction, "clothiery")
        self.update_or_add_crafting_select(station, interaction)
        await interaction.response.edit_message(content="Choose an item from the Clothiery:", view=self)

    @discord.ui.button(label="🍶 Potion Shop", custom_id="citadel_potion_shop", style=discord.ButtonStyle.blurple)
    async def potion_shop(self, button, interaction):
        # Check if the user who interacted is the same as the one who initiated the view
        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player object from the latest player data
        _, self.player_data = await refresh_player_from_data(self, self.ctx)

        # Check if the player is not in the citadel
        if self.player_data["location"] != "citadel":
            await self.not_in_citadel_response(interaction)
            return

        station = create_crafting_stations(interaction, "potion_shop")
        self.update_or_add_crafting_select(station, interaction)
        await interaction.response.edit_message(content="Choose an item from the Potion Shop:", view=self)

class BreadRow(discord.ui.View, CommonResponses):
    def __init__(self, player_data, ctx=None, author_id=None):
        super().__init__(timeout=None)
        self.player_data = player_data
        self.ctx = ctx
        self.author_id = author_id
        self.crafting_select = None

    def update_or_add_crafting_select(self, recipes, interaction, is_tavern=False):
        from citadel.crafting import Recipe
        from nero.TES import TavernSpecialItem
        if self.crafting_select:
            self.remove_item(self.crafting_select)

        # Pass 'tavern' as context if is_tavern is True
        context = 'tavern' if is_tavern else None
        self.crafting_select = CraftingSelect(recipes, interaction, self.author_id, context=context)
        if is_tavern:
            # Append the 'Three Eyed Snake' option only for the tavern
            three_eyed_snake_recipe = Recipe(TavernSpecialItem(), None)  # Create a special recipe for Three Eyed Snake
            self.crafting_select.options.append(discord.SelectOption(
                label=three_eyed_snake_recipe.result.name,
                value='three_eyed_snake',
                emoji='🎲'
            ))
        self.add_item(self.crafting_select)

    @discord.ui.button(label="🥖 Bread Stand", custom_id="citadel_bread_stand", style=discord.ButtonStyle.blurple)
    async def bread_stand(self, button, interaction):
        # Check if the user who interacted is the same as the one who initiated the view
        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player object from the latest player data
        _, self.player_data = await refresh_player_from_data(self, self.ctx)

        # Check if the player is not in the citadel
        if self.player_data["location"] != "citadel":
            await self.not_in_citadel_response(interaction)
            return

        station = create_crafting_stations(interaction, "bread_stand")
        self.update_or_add_crafting_select(station, interaction)
        await interaction.response.edit_message(content="Choose an item from the Bread Stand:", view=self)

    @discord.ui.button(label="🍖 Meat Stand", custom_id="citadel_meat_stand", style=discord.ButtonStyle.blurple)
    async def meat_stand(self, button, interaction):

        # Check if the user who interacted is the same as the one who initiated the view
        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player object from the latest player data
        _, self.player_data = await refresh_player_from_data(self, self.ctx)

        # Check if the player is not in the citadel
        if self.player_data["location"] != "citadel":
            await self.not_in_citadel_response(interaction)
            return

        station = create_crafting_stations(interaction, "meat_stand")
        self.update_or_add_crafting_select(station, interaction)
        await interaction.response.edit_message(content="Choose an item from the Meat Stand:", view=self)


    @discord.ui.button(label="🎲 Tavern", custom_id="citadel_tavern", style=discord.ButtonStyle.blurple)
    async def tavern(self, button, interaction):
        # Check if the user who interacted is the same as the one who initiated the view
        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player object from the latest player data
        _, self.player_data = await refresh_player_from_data(self, self.ctx)

        # Check if the player is not in the citadel
        if self.player_data["location"] != "citadel":
            await self.not_in_citadel_response(interaction)
            return

        station = create_crafting_stations(interaction, "tavern")
        self.update_or_add_crafting_select(station, interaction)
        self.update_or_add_crafting_select(station, interaction, is_tavern=True)
        await interaction.response.edit_message(content="Choose an item from the Tavern:", view=self)

class WheatRow(discord.ui.View, CommonResponses):
    def __init__(self, player_data, ctx=None, author_id=None):
        super().__init__(timeout=None)
        self.player_data = player_data
        self.ctx = ctx
        self.author_id = author_id
        self.crafting_select = None

    @discord.ui.button(label="🌾 Wheat", custom_id="citadel_wheat", style=discord.ButtonStyle.blurple)
    async def wheat(self, button, interaction):
        # Check if the user who interacted is the same as the one who initiated the view
        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player object from the latest player data
        _, self.player_data = await refresh_player_from_data(self, self.ctx)

        # Check if the player is not in the citadel
        if self.player_data["location"] != "citadel":
            await self.not_in_citadel_response(interaction)
            return

        embed = discord.Embed(
            title="Wheat Field",
            description="Harvest the wheat to add to your inventory.",
            color=discord.Color.green()
        )
        wheat_url = generate_urls("Citadel", "Wheat")
        embed.set_thumbnail(url=wheat_url)

        view = HarvestButton(ctx=self.ctx, crop="Wheat")
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="🌿 Flax", custom_id="citadel_flax", style=discord.ButtonStyle.blurple)
    async def flax(self, button, interaction):
        # Check if the user who interacted is the same as the one who initiated the view
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player object from the latest player data
        _, self.player_data = await refresh_player_from_data(self, self.ctx)

        # Check if the player is not in the citadel
        if self.player_data["location"] != "citadel":
            await self.not_in_citadel_response(interaction)
            return

        embed = discord.Embed(
            title="Flax Field",
            description="Harvest the flax to add to your inventory.",
            color=discord.Color.green()
        )
        flax_url = generate_urls("Citadel", "Flax")
        embed.set_thumbnail(url=flax_url)
        view = HarvestButton(ctx=self.ctx,
                             crop="Flax")
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="⛺ Heal Tent", custom_id="citadel_heal_tent", style=discord.ButtonStyle.blurple)
    async def heal_tent(self, button, interaction):

        # Check if the user who interacted is the same as the one who initiated the view
        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player object from the latest player data
        _, self.player_data = await refresh_player_from_data(self, self.ctx)

        # Check if the player is not in the citadel
        if self.player_data["location"] != "citadel":
            await self.not_in_citadel_response(interaction)
            return

        from exemplars.exemplars import Exemplar
        from utils import load_player_data
        from emojis import get_emoji
        from citadel.heal import HealTentButton

        # Load player data
        author_id = str(interaction.user.id)
        guild_id = self.ctx.guild.id
        player_data = load_player_data(guild_id, author_id)
        player = Exemplar(
            player_data["exemplar"],
            player_data["stats"],
            player_data["inventory"]
        )

        # Generate health bar
        def health_bar(current, max_health):
            bar_length = 20
            health_percentage = current / max_health
            filled_length = round(bar_length * health_percentage)
            filled_symbols = '◼' * filled_length
            empty_symbols = '◻' * (bar_length - filled_length)
            return filled_symbols + empty_symbols

        # Generate health bar
        current_health_bar = health_bar(player.stats.health, player.stats.max_health)
        health_emoji = get_emoji('heart_emoji')

        # Check if health is full and set the appropriate message
        is_full_health = player.stats.health >= player.stats.max_health
        message = "**You are already fully healed!**" if is_full_health else "Recover your health."

        # Create the initial embed with health info
        embed = discord.Embed(
            title="Heal Tent",
            description=f"{message}\n\n{health_emoji} Health: {current_health_bar} {player.stats.health}/{player.stats.max_health}",
            color=discord.Color.blue()
        )
        heal_tent_url = generate_urls('Citadel', 'Heal')
        embed.set_image(url=heal_tent_url)

        # Create the view and pass the player, player_data, and author_id
        view = HealTentButton(ctx=self.ctx, player=player, player_data=player_data, author_id=author_id, guild_id=guild_id)

        # Disable the Heal button if the player's health is full
        if is_full_health:
            for item in view.children:
                if isinstance(item, discord.ui.Button) and item.custom_id == "heal":
                    item.disabled = True

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class TravelRow(discord.ui.View, CommonResponses):
    def __init__(self, player_data, ctx=None, author_id=None):
        super().__init__(timeout=None)
        self.player_data = player_data
        self.ctx = ctx
        self.author_id = author_id
        self.crafting_select = None
        self.guild_id = ctx.guild.id

    @discord.ui.button(label="🏴‍☠️ Jolly Roger", custom_id="citadel_travel", style=discord.ButtonStyle.blurple)
    async def travel(self, button, interaction):
        from exemplars.exemplars import Exemplar
        from nero.options import JollyRogerView

        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player object from the latest player data
        _, self.player_data = await refresh_player_from_data(self, self.ctx)

        # Check if the player is not in the citadel
        if self.player_data["location"] != "citadel":
            await self.not_in_citadel_response(interaction)
            return

        player_data = load_player_data(interaction.guild.id, str(interaction.user.id))
        player = Exemplar(player_data["exemplar"],
                          player_data["stats"],
                          player_data["inventory"])

        view = JollyRogerView(self.guild_id, player, player_data, self.author_id)

        nero_embed = discord.Embed(
            title="Captain Ner0",
            description="Ahoy, matey! Welcome aboard the Jolly Roger. Adventure and treasure await ye on the high seas!",
            color=discord.Color.gold()
        )
        nero_embed.set_image(url=generate_urls("nero", "welcome"))

        await interaction.response.send_message(embed=nero_embed, ephemeral=False, view=view)

    @discord.ui.button(label="🏟️ Colosseum", custom_id="citadel_colosseum", style=discord.ButtonStyle.blurple)
    async def colosseum(self, button, interaction):
        # Check if the user who interacted is the same as the one who initiated the view
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Refresh player object from the latest player data
        _, self.player_data = await refresh_player_from_data(self, self.ctx)

        # Check if the player is not in the citadel
        if self.player_data["location"] != "citadel":
            await self.not_in_citadel_response(interaction)
            return

        # Send a message about the Colosseum
        nero_embed = discord.Embed(
            title="Captain Nero",
            description="Arr, I've heard tales of the Colosseum! A place for hearty brawls and clashin' swords. But it seems it's not yet ready for ye, matey. PvP is a hot topic on the high seas, best to keep yer powder dry till it opens!",
            color=discord.Color.dark_gold()
        )
        nero_embed.set_thumbnail(url=generate_urls("nero", "confused"))
        await interaction.response.send_message(embed=nero_embed, ephemeral=True)

    @discord.ui.button(label="🚪 Exit", custom_id="citadel_exit", style=discord.ButtonStyle.blurple)
    async def exit(self, button, interaction):
        from probabilities import brute_percent
        from citadel.brute import mega_brute_encounter

        if str(interaction.user.id) != self.author_id:
            await self.unauthorized_user_response(interaction)
            return

        # Refresh player object from the latest player data
        _, self.player_data = await refresh_player_from_data(self, self.ctx)

        if self.player_data["location"] != "citadel":
            await self.not_in_citadel_response(interaction)
            return

        # Determine if the brute encounter will happen
        will_encounter_brute = np.random.rand() <= brute_percent

        await interaction.response.defer()

        player_data = load_player_data(interaction.guild.id, str(interaction.user.id))

        if will_encounter_brute:
            # Prepare the suspenseful message for brute encounter
            embed = discord.Embed(title="Captain Ner0",
                                  description="Hmmm... do you hear that?",
                                  color=discord.Color.dark_gold())
            embed.set_thumbnail(url=generate_urls("nero", "confused"))

            # Send the suspenseful message as a new follow-up message
            suspense_message = await interaction.followup.send(embed=embed, wait=True)

            await asyncio.sleep(2.5)  # Wait for suspense to build

            # Update the embed for the brute encounter
            embed.description = "Arrr! Ye better leg it, ye pointy-eared scallywags! **BRUTE AT THE GATE!**"
            embed.set_thumbnail(url=generate_urls("nero", "laugh"))
            await suspense_message.edit(embed=embed)  # Update the existing follow-up message

            await mega_brute_encounter(player_data, self.ctx, interaction, self.guild_id, self.author_id)
        else:

            # Prepare and send the "coast is clear" message directly
            embed = discord.Embed(title="Captain Ner0",
                                  description="**The coast is clear, me hearties!** Time to plunder and claim our fortunes! Onward!",
                                  color=discord.Color.dark_gold())
            embed.set_thumbnail(url=generate_urls("nero", "gun"))
            await interaction.followup.send(embed=embed, ephemeral = True)

        player_data["location"] = None
        save_player_data(self.guild_id, self.author_id, player_data)


def setup(bot):
    bot.add_cog(CitadelCog(bot))