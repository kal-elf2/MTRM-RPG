import discord
from discord.ext import commands
from citadel.crafting import CraftingSelect, forge, woodshop, bread_stand, archery_stand, tannery, clothiery, meat_stand


class CitadelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    class ForgeRow(discord.ui.View):
        def __init__(self, ctx=None):
            super().__init__(timeout=None)
            self.ctx = ctx

        @discord.ui.button(label="Forge", custom_id="citadel_forge", style=discord.ButtonStyle.blurple)
        async def forge(self, button, interaction):

            # Add the CraftingSelect with forge recipes
            self.add_item(CraftingSelect(forge.recipes))

            # Update the original message to display the CraftingSelect
            await interaction.response.edit_message(content="Choose an item to Forge:", view=self)

        @discord.ui.button(label="Wood Shop", custom_id="citadel_woodshop", style=discord.ButtonStyle.blurple)
        async def wood_shop(self, button, interaction):
            await interaction.response.send_message("You're at the Wood Shop!")

        @discord.ui.button(label="Archery Stand", custom_id="citadel_archery", style=discord.ButtonStyle.blurple)
        async def archery_stand(self, button, interaction):
            await interaction.response.send_message("You're at the Archery Stand!")

    class TanneryRow(discord.ui.View):
        def __init__(self, ctx=None):
            super().__init__(timeout=None)
            self.value = None
            self.ctx = ctx
        @discord.ui.button(label="Tannery", custom_id="citadel_tannery", style=discord.ButtonStyle.blurple)
        async def tannery(self, button, interaction):
            await interaction.response.send_message("You're at the Tannery!")

        @discord.ui.button(label="Clothiery", custom_id="citadel_clothiery", style=discord.ButtonStyle.blurple)
        async def clothiery(self, button, interaction):
            await interaction.response.send_message("You're at the Clothiery!")

        @discord.ui.button(label="Potion Shop", custom_id="citadel_potion_shop", style=discord.ButtonStyle.blurple)
        async def potion_shop(self, button, interaction):
            await interaction.response.send_message("You're at the Potion Shop!")

    class BreadRow(discord.ui.View):
        def __init__(self, ctx=None):
            super().__init__(timeout=None)
            self.value = None
            self.ctx = ctx
        @discord.ui.button(label="Bread Stand", custom_id="citadel_bread_stand", style=discord.ButtonStyle.blurple)
        async def bread_stand(self, button, interaction):
            await interaction.response.send_message("You're at the Bread Stand!")

        @discord.ui.button(label="Meat Stand", custom_id="citadel_meat_stand", style=discord.ButtonStyle.blurple)
        async def meat_stand(self, button, interaction):
            await interaction.response.send_message("You're at the Meat Stand!")

        @discord.ui.button(label="Tavern", custom_id="citadel_tavern", style=discord.ButtonStyle.blurple)
        async def tavern(self, button, interaction):
            await interaction.response.send_message("You're at the Tavern!")

    class WheatRow(discord.ui.View):
        def __init__(self, ctx=None):
            super().__init__(timeout=None)
            self.value = None
            self.ctx = ctx
        @discord.ui.button(label="Wheat", custom_id="citadel_wheat", style=discord.ButtonStyle.blurple)
        async def wheat(self, button, interaction):
            await interaction.response.send_message("You're at the Wheat Field!")

        @discord.ui.button(label="Flax", custom_id="citadel_flax", style=discord.ButtonStyle.blurple)
        async def flax(self, button, interaction):
            await interaction.response.send_message("You're at the Flax Field!")

        @discord.ui.button(label="Heal Tent", custom_id="citadel_heal_tent", style=discord.ButtonStyle.blurple)
        async def heal_tent(self, button, interaction):
            await interaction.response.send_message("You're at the Heal Tent!")

    class TravelRow(discord.ui.View):

        def __init__(self, ctx=None):
            super().__init__(timeout=None)
            self.value = None
            self.ctx = ctx
        @discord.ui.button(label="Travel", custom_id="citadel_travel", style=discord.ButtonStyle.blurple)
        async def travel(self, button, interaction):
            await interaction.response.send_message("You're preparing to Travel!")

        @discord.ui.button(label="Colosseum", custom_id="citadel_colosseum", style=discord.ButtonStyle.blurple)
        async def colosseum(self, button, interaction):
            await interaction.response.send_message("You entered the Colosseum!")

        @discord.ui.button(label="Exit", custom_id="citadel_exit", style=discord.ButtonStyle.blurple)
        async def exit(self, button, interaction):
            await interaction.response.send_message("You left the Citadel!")

    @commands.slash_command(description="Visit the Citadel!")
    async def citadel(self, ctx):
        row1 = CitadelCog.ForgeRow(ctx)
        row2 = CitadelCog.TanneryRow(ctx)
        row3 = CitadelCog.BreadRow(ctx)
        row4 = CitadelCog.WheatRow(ctx)
        row5 = CitadelCog.TravelRow(ctx)

        await ctx.respond(view=row1)
        await ctx.send(view=row2)
        await ctx.send(view=row3)
        await ctx.send(view=row4)
        await ctx.send(view=row5)


def setup(bot):
    bot.add_cog(CitadelCog(bot))