import discord
from discord.ext import commands
from citadel.crafting import CraftingSelect, forge, woodshop, bread_stand, archery_stand, tannery, clothiery, meat_stand
from images.urls import generate_urls
from resources.grains import HarvestButton
from exemplars.exemplars import Exemplar

class CitadelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _get_player(self, ctx):
        from utils import load_player_data
        guild_id = ctx.guild.id
        author_id = str(ctx.author.id)
        player_data = load_player_data(guild_id)
        return Exemplar(
            player_data[author_id]["exemplar"],
            player_data[author_id]["stats"],
            player_data[author_id]["inventory"]
        )

    @commands.slash_command(description="Visit the Citadel!")
    async def citadel(self, ctx):
        player = self._get_player(ctx)
        guild_id = ctx.guild.id

        from utils import load_player_data
        player_data = load_player_data(guild_id)

        row1 = ForgeRow(ctx)
        row2 = TanneryRow(ctx)
        row3 = BreadRow(ctx)
        row4 = WheatRow(ctx, player=player, guild_id=guild_id, player_data=player_data)
        row5 = TravelRow(ctx)

        await ctx.respond(view=row1)
        await ctx.send(view=row2)
        await ctx.send(view=row3)
        await ctx.send(view=row4)
        await ctx.send(view=row5)

class ForgeRow(discord.ui.View):
    def __init__(self, ctx=None):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.crafting_select = None

    def update_or_add_crafting_select(self, recipes):
        if self.crafting_select:
            self.remove_item(self.crafting_select)
        self.crafting_select = CraftingSelect(recipes)
        self.add_item(self.crafting_select)

    @discord.ui.button(label="🔨 Forge", custom_id="citadel_forge", style=discord.ButtonStyle.blurple)
    async def forge(self, button, interaction):
        self.update_or_add_crafting_select(forge)
        await interaction.response.edit_message(content="Choose an item to Forge:", view=self)

    @discord.ui.button(label="🪓 Wood Shop", custom_id="citadel_woodshop", style=discord.ButtonStyle.blurple)
    async def wood_shop(self, button, interaction):
        self.update_or_add_crafting_select(woodshop)
        await interaction.response.edit_message(content="Choose an item from the Wood Shop:", view=self)

    @discord.ui.button(label="🏹 Archery Stand", custom_id="citadel_archery", style=discord.ButtonStyle.blurple)
    async def archery_stand(self, button, interaction):
        self.update_or_add_crafting_select(archery_stand)
        await interaction.response.edit_message(content="Choose an item from the Archery Stand:", view=self)


class TanneryRow(discord.ui.View):
    def __init__(self, ctx=None):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.crafting_select = None

    def update_or_add_crafting_select(self, recipes):
        if self.crafting_select:
            self.remove_item(self.crafting_select)
        self.crafting_select = CraftingSelect(recipes)
        self.add_item(self.crafting_select)

    @discord.ui.button(label="🐄 Tannery", custom_id="citadel_tannery", style=discord.ButtonStyle.blurple)
    async def tannery(self, button, interaction):
        self.update_or_add_crafting_select(tannery)
        await interaction.response.edit_message(content="Choose an item from the Tannery:", view=self)

    @discord.ui.button(label="🧵 Clothiery", custom_id="citadel_clothiery", style=discord.ButtonStyle.blurple)
    async def clothiery(self, button, interaction):
        self.update_or_add_crafting_select(clothiery)
        await interaction.response.edit_message(content="Choose an item from the Clothiery:", view=self)

    @discord.ui.button(label="🍶 Potion Shop", custom_id="citadel_potion_shop", style=discord.ButtonStyle.blurple)
    async def potion_shop(self, button, interaction):
        await interaction.response.send_message("You're at the Potion Shop!")


class BreadRow(discord.ui.View):
    def __init__(self, ctx=None):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.crafting_select = None

    def update_or_add_crafting_select(self, recipes):
        if self.crafting_select:
            self.remove_item(self.crafting_select)
        self.crafting_select = CraftingSelect(recipes)
        self.add_item(self.crafting_select)

    @discord.ui.button(label="🥖 Bread Stand", custom_id="citadel_bread_stand", style=discord.ButtonStyle.blurple)
    async def bread_stand(self, button, interaction):
        self.update_or_add_crafting_select(bread_stand)
        await interaction.response.edit_message(content="Choose an item from the Bread Stand:", view=self)

    @discord.ui.button(label="🍖 Meat Stand", custom_id="citadel_meat_stand", style=discord.ButtonStyle.blurple)
    async def meat_stand(self, button, interaction):
        self.update_or_add_crafting_select(meat_stand)
        await interaction.response.edit_message(content="Choose an item from the Meat Stand:", view=self)


    @discord.ui.button(label="🎲 Tavern", custom_id="citadel_tavern", style=discord.ButtonStyle.blurple)
    async def tavern(self, button, interaction):
        await interaction.response.send_message("You're at the Tavern!")

class WheatRow(discord.ui.View):
    def __init__(self, ctx=None, player=None, guild_id=None, player_data=None):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.player = player
        self.guild_id = guild_id
        self.player_data = player_data

    @discord.ui.button(label="🌾 Wheat", custom_id="citadel_wheat", style=discord.ButtonStyle.blurple)
    async def wheat(self, button, interaction):
        embed = discord.Embed(
            title="Wheat Field",
            description="Harvest the wheat to add to your inventory.",
            color=discord.Color.green()
        )
        wheat_url = generate_urls("Grains", "Wheat")
        embed.set_thumbnail(url=wheat_url)

        view = HarvestButton(ctx=self.ctx, guild_id=self.guild_id, player=self.player, player_data=self.player_data)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="🌿 Flax", custom_id="citadel_flax", style=discord.ButtonStyle.blurple)
    async def flax(self, button, interaction):
        await interaction.response.send_message("You're at the Flax Field!")

    @discord.ui.button(label="⛺ Heal Tent", custom_id="citadel_heal_tent", style=discord.ButtonStyle.blurple)
    async def heal_tent(self, button, interaction):
        await interaction.response.send_message("You're at the Heal Tent!")

class TravelRow(discord.ui.View):

    def __init__(self, ctx=None):
        super().__init__(timeout=None)
        self.value = None
        self.ctx = ctx
    @discord.ui.button(label="🏴‍☠️ Jolly Roger (Travel)", custom_id="citadel_travel", style=discord.ButtonStyle.blurple)
    async def travel(self, button, interaction):
        await interaction.response.send_message("You're preparing to Travel!")

    @discord.ui.button(label="🏟️ Colosseum", custom_id="citadel_colosseum", style=discord.ButtonStyle.blurple)
    async def colosseum(self, button, interaction):
        await interaction.response.send_message("You entered the Colosseum!")

    @discord.ui.button(label="🚪 Leave Citadel", custom_id="citadel_exit", style=discord.ButtonStyle.blurple)
    async def exit(self, button, interaction):
        await interaction.response.send_message("You left the Citadel!")


def setup(bot):
    bot.add_cog(CitadelCog(bot))