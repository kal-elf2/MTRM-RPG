import discord
from images.urls import generate_urls

# Define a special item class for Three Eyed Snake
class TavernSpecialItem:
    def __init__(self):
        self.name = "Three Eyed Snake"

async def handle_three_eyed_snake_selection(interaction: discord.Interaction):
    nero_embed = discord.Embed(
        title="Captain Ner0",
        description="Ahoy! Let's play some **Three-Eyed-Snake**!",
        color=discord.Color.dark_gold()
    )
    nero_embed.set_image(url=generate_urls("nero", "dice"))

    view = discord.ui.View()
    view.add_item(PlayButton(label="Play", custom_id="play_3es"))
    view.add_item(RulesButton(label="Rules", custom_id="rules_3es"))
    await interaction.response.send_message(embed=nero_embed, view=view, ephemeral=True)


class PlayButton(discord.ui.Button):
    def __init__(self, label, custom_id):
        super().__init__(label=label, custom_id=custom_id, style=discord.ButtonStyle.blurple)

    async def callback(self, interaction: discord.Interaction):
        # Logic for when the 'Play' button is pressed
        pass

class RulesButton(discord.ui.Button):
    def __init__(self, label, custom_id):
        super().__init__(label=label, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):

        # Construct the embed with rules information
        rules_embed = discord.Embed(
            title="Three-Eyes-Snake Rules",
            description=f"Ahoy! Heed these rules for Three Eyed Snake {interaction.user.mention}. No blubberin' later if ye be outplayed",
            color=discord.Color.dark_gold()
        )
        rules_embed.set_image(url=generate_urls("3ES", "rules"))

        # Send the embed as an ephemeral message
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)


