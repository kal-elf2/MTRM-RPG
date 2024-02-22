import discord

class HuntKrakenButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.green, label="Hunt Kraken", emoji="🦑")

    async def callback(self, interaction: discord.Interaction):
        # Placeholder for actual battle logic
        pass
