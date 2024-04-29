from discord import Embed
import discord
import json
import random
from emojis import get_emoji
from utils import save_player_data, load_player_data, CommonResponses, refresh_player_from_data, get_server_setting
from images.urls import generate_urls
import asyncio

class LootOptions(discord.ui.View, CommonResponses):
    def __init__(self, interaction, player, monster, battle_embed, player_data, author_id, battle_outcome,
                 loot_messages, guild_id, ctx, experience_gained, loothaven_effect, rusty_spork_dropped, add_repeat_button=True):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.player = player
        self.monster = monster
        self.battle_embed = battle_embed
        self.player_data = player_data
        self.author_id = author_id
        self.battle_outcome = battle_outcome
        self.loot_messages = loot_messages
        self.guild_id = guild_id
        self.ctx = ctx
        self.experience_gained = experience_gained
        self.loothaven_effect = loothaven_effect
        self.rusty_spork_dropped = rusty_spork_dropped

        # Store the state for adding the repeat button
        self.should_add_repeat_button = add_repeat_button

        if self.should_add_repeat_button:
            self.add_repeat_battle_button()

    def add_repeat_battle_button(self):
        # Add the "Repeat Battle" button
        repeat_button = discord.ui.Button(
            custom_id="repeat_battle",
            style=discord.ButtonStyle.grey,
            emoji="🔁"
        )
        repeat_button.callback = self.repeat_battle
        self.add_item(repeat_button)

    async def repeat_battle(self, interaction):
        # Check if the user who interacted is the same as the one who initiated the view
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Check for battle flag and return if battling
        if self.player_data["location"] == "battle":
            await CommonResponses.ongoing_battle_response(interaction)
            return

        try:
            # Acknowledge the interaction
            await interaction.response.defer()

            # Clear all buttons from the view
            self.clear_items()

            # Update the interaction message to reflect the view changes
            await interaction.edit_original_response(view=self)

            # Start a new battle with the same monster
            await start_battle(self.ctx, self.monster, self.player_data, self.player, self.author_id, self.guild_id,
                               self.battle_embed)

        except (discord.InteractionResponded, discord.NotFound):
            # Construct a custom embed to inform the user about the expired session
            expired_embed = discord.Embed(
                title="Captain Ner0",
                description="Arr! The battle session has expired, matey. Start a new battle if ye dare!",
                color=discord.Color.dark_gold()
            )
            expired_embed.set_thumbnail(url=generate_urls("nero", "confused"))

            # Send the embed as a response to the interaction
            await interaction.followup.send(embed=expired_embed, ephemeral=True)

    @discord.ui.button(custom_id="loot", label="Loot", style=discord.ButtonStyle.blurple)
    async def collect_loot(self, button, interaction):

        # Check if the user who interacted is the same as the one who initiated the view
        # Inherited from CommonResponses class from utils
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        # Defer the response
        await interaction.response.defer()

        # Refresh player object from the latest player data
        self.player, self.player_data = await refresh_player_from_data(interaction)

        # Extract loot items and messages from the battle outcome
        loot = self.battle_outcome[3]

        # Extract all item drops (excluding 'coppers', 'materium' as they don't occupy inventory slots)
        new_items = [item for loot_type, loot_items in loot if loot_type in ('herb', 'items', 'gem', 'loot')
                     for item in (loot_items if isinstance(loot_items, list) else [loot_items])]

        # Calculate the number of new inventory slots required
        required_slots = 0
        for item in new_items:
            if isinstance(item, tuple):  # This is for 'items' type which has (Item, quantity) structure
                item_name = item[0].name
            else:
                item_name = item.name

            if not self.player.inventory.has_item(item_name):
                required_slots += 1

        # If player's inventory doesn't have enough space for new non-stackable items
        available_slots = self.player.inventory.limit - self.player.inventory.total_items_count()
        if available_slots < required_slots:
            await interaction.response.send_message("Inventory is full. Please make some room before collecting loot.",
                                                    ephemeral=True)
            return

        for loot_type, loot_items in self.battle_outcome[3]:
            if loot_type == 'coppers':
                self.player.inventory.add_coppers(loot_items)
            elif loot_type == 'gem':
                self.player.inventory.add_item_to_inventory(loot_items)
            elif loot_type == 'herb':
                self.player.inventory.add_item_to_inventory(loot_items)
            elif loot_type == 'materium':
                self.player.inventory.add_item_to_inventory(loot_items)
            elif loot_type == 'loot':
                self.player.inventory.add_item_to_inventory(loot_items)
            elif loot_type == 'potion':
                self.player.inventory.add_item_to_inventory(loot_items)
            elif loot_type == 'items':  # For items with quantity
                for item, quantity in loot_items:
                    self.player.inventory.add_item_to_inventory(item, amount=quantity)

        self.player_data["inventory"] = self.player.inventory.to_dict()

        loot_message_string = '\n'.join(self.loot_messages)
        # Incorporate Loothaven charm effect in the message
        loothaven_message = f"\n{get_emoji('Loothaven')} Your **Loothaven charm** is *glowing*!\n" if self.loothaven_effect else ""

        max_cap_message = ""
        if self.experience_gained == 0:
            max_cap_message = f"\n**(Max XP cap reached for Zone {self.player.stats.zone_level})**"

        message_text = (
            f"You have **DEFEATED** the {self.monster.name}!\n"
            f"You dealt **{self.battle_outcome[1]} damage** to the monster and took **{self.battle_outcome[2]} damage**.\n"
            f"You gained {self.experience_gained} combat XP. {max_cap_message}\n"
            f"{loothaven_message}\n"
            f"__**Loot picked up:**__\n"
            f"{loot_message_string}"
        )

        final_embed = create_battle_embed(self.ctx.user, self.player, self.monster, footer_text_for_embed(self.ctx, self.monster, self.player), message_text)

        if self.rusty_spork_dropped:
            special_nero_embed = discord.Embed(
                title="Avast! A 'Mundane' Discovery!",
                description=f"Ahoy, matey! What's this? Ye've dug up a {get_emoji('Rusty Spork')}**Rusty Spork**! Ah, such a common find, really—nothing to get yer sails in a twist over. Seems pretty worthless, but come see me at the Jolly Roger anyway. I might be able to scrounge up some {get_emoji('coppers_emoji')}Coppers for it.",
                color=discord.Color.gold()
            )
            special_nero_embed.set_thumbnail(url=generate_urls("nero", "nero"))
            await interaction.followup.send(embed=special_nero_embed)

        save_player_data(self.guild_id, self.author_id, self.player_data)

        self.clear_items()

        # Update the original response with the final embed
        await interaction.edit_original_response(embed=final_embed, view=None)

        # Conditionally add the "Repeat Battle" button based on the stored state
        if self.should_add_repeat_button:
            self.add_repeat_battle_button()

            # Update the view with the new button
            await interaction.edit_original_response(view=self)

async def start_battle(ctx, monster, player_data, player, author_id, guild_id, battle_embed):
    from monsters.monster import BattleContext, monster_battle
    from stats import ResurrectOptions

    # Check if player data exists for the user
    if not player_data:
        embed = Embed(title="Captain Ner0",
                      description="Arr! What be this? No record of yer adventures? Start a new game with `/newgame` before I make ye walk the plank.",
                      color=discord.Color.dark_gold())
        embed.set_thumbnail(url=generate_urls("nero", "confused"))
        await ctx.respond(embed=embed, ephemeral=True)
        return

    # Check the player's health before starting a battle
    if player.stats.health <= 0:
        embed = Embed(title="Captain Ner0",
                      description="Ahoy! Ye can't do that ye bloody ghost! Ye must travel to the 🪦 `/cemetery` to reenter the realm of the living.",
                      color=discord.Color.dark_gold())
        embed.set_thumbnail(url=generate_urls("nero", "confused"))
        await ctx.respond(embed=embed, ephemeral=True)
        return

    player_data["location"] = "battle"
    save_player_data(guild_id, author_id, player_data)

    zone_level = player.stats.zone_level

    # Reset the monster's health to its maximum at the start of the battle
    monster.health = monster.max_health

    await ctx.respond(f"{ctx.author.mention} encounters a {monster.name}", ephemeral=True)

    def update_special_attack_buttons(context):
        if context.special_attack_options_view:
            context.special_attack_options_view.update_button_states()

    battle_context = BattleContext(ctx, ctx.author, player, monster, battle_embed, zone_level,
                                   update_special_attack_buttons)

    # Create the special attack options view without the messages first
    special_attack_options_view = SpecialAttackOptions(battle_context, None, None)

    # IMPORTANT: Set the special attack options view in the battle context immediately
    battle_context.special_attack_options_view = special_attack_options_view

    # Send the special attack message and store the reference
    special_attack_message = await ctx.send(view=special_attack_options_view)
    battle_context.special_attack_message = special_attack_message

    # Send the battle options message and store the reference
    battle_options_msg = await ctx.send(
        view=BattleOptions(ctx, player, player_data, battle_context, special_attack_options_view))
    battle_context.battle_options_msg = battle_options_msg

    # Now update the special attack options view with the message references
    special_attack_options_view.battle_options_msg = battle_options_msg
    special_attack_options_view.special_attack_message = special_attack_message

    # Start the monster attack task and receive its outcome
    battle_result = await monster_battle(battle_context, guild_id=guild_id)

    if battle_result is None:
        # Save the player's current stats
        player_data["stats"]["stamina"] = player.stats.stamina
        player_data["stats"]["combat_level"] = player.stats.combat_level
        player_data["stats"]["combat_experience"] = player.stats.combat_experience
        player_data["stats"]["health"] = player.stats.health
        player_data["stats"]["damage_taken"] = player.stats.damage_taken
        player_data["stats"].update(player.stats.__dict__)

        save_player_data(guild_id, author_id, player_data)

    # Process battle outcome
    else:
        # Unpack the battle outcome and loot messages
        battle_outcome, loot_messages = battle_result

        # Define the maximum level for each zone
        zone_max_levels = {
            1: 20,
            2: 40,
            3: 60,
            4: 80,
        }

        if battle_outcome[0]:

            # Check if the player is at or above the level cap for their current zone
            if zone_level in zone_max_levels and player.stats.combat_level >= zone_max_levels[zone_level]:
                # Player is at or has exceeded the level cap for their zone; set XP gain to 0
                experience_gained = 0
            else:
                # Player is below the level cap; award XP from the monster
                experience_gained = monster.experience_reward

            loothaven_effect = battle_outcome[5]  # Get the Loothaven effect status
            await player.gain_experience(experience_gained, 'combat', ctx, player)

            player_data["stats"]["stamina"] = player.stats.stamina
            player_data["stats"]["combat_level"] = player.stats.combat_level
            player_data["stats"]["combat_experience"] = player.stats.combat_experience
            player.stats.damage_taken = 0
            player_data["stats"].update(player.stats.__dict__)

            if player.stats.health <= 0:
                player.stats.health = player.stats.max_health

            # Increment the count of the defeated monster
            player_data["monster_kills"][monster.name] += 1

            # Save the player data after common actions
            save_player_data(guild_id, author_id, player_data)

            # Clear the previous views
            await battle_context.special_attack_message.delete()
            await battle_options_msg.delete()

            loot_view = LootOptions(ctx, player, monster, battle_embed, player_data, author_id, battle_outcome,
                                    loot_messages, guild_id, ctx, experience_gained, loothaven_effect, battle_context.rusty_spork_dropped)

            max_cap_message = ""
            if experience_gained == 0:
                max_cap_message = f"\n**(Max XP cap reached for Zone {player.stats.zone_level})**"

            # Construct the embed with the footer
            battle_outcome_embed = create_battle_embed(ctx.user, player, monster,
                                                       footer_text_for_embed(ctx, monster),
                                                       f"You have **DEFEATED** the {monster.name}!\n"
                                                       f"You dealt **{battle_outcome[1]} damage** to the monster and took **{battle_outcome[2]} damage**. "
                                                       f"You gained {experience_gained} combat XP. {max_cap_message}\n"
                                                       f"\n\u00A0\u00A0")

            await battle_embed.edit(
                embed=battle_outcome_embed,
                view=loot_view
            )

        else:

            # The player is defeated
            player.stats.health = 0  # Set player's health to 0
            player_data["stats"]["health"] = 0

            # Create a new embed with the defeat message
            new_embed = create_battle_embed(ctx.user, player, monster, footer_text="", messages=

            f"☠️ You have been **DEFEATED** by the **{monster.name}**!\n"
            f"{get_emoji('rip_emoji')} *Your spirit lingers, seeking renewal.* {get_emoji('rip_emoji')}\n\n"
            f"__**Options for Revival:**__\n"
            f"1. Use {get_emoji('Materium')} to revive without penalty.\n"
            f"2. Resurrect with 2.5% penalty to all skills."
            f"**Lose all items in inventory** (Keep equipped items, coppers, MTRM, potions, and charms)")

            # Clear the previous BattleOptions view
            await battle_context.special_attack_message.delete()
            await battle_options_msg.delete()

            # Add the "dead.png" image to the embed
            new_embed.set_image(url=generate_urls("cemetery", "dead"))

            # Update the message with the new embed and view
            await battle_embed.edit(embed=new_embed, view=ResurrectOptions(ctx, player_data, author_id))

    # Clear the battle flag after the battle ends
    player_data["location"] = None
    save_player_data(guild_id, author_id, player_data)

def use_potion_logic(player, potion_name):

    potion = next((p for p in player.inventory.potions if p.name == potion_name), None)
    if potion and potion.stack > 0:
        # Apply the potion effect
        if potion_name in ["Health Potion", "Super Health Potion"]:
            player.stats.health = min(player.stats.health + potion.effect_value, player.stats.max_health)
        elif potion_name in ["Stamina Potion", "Super Stamina Potion"]:
            player.stats.stamina = min(player.stats.stamina + potion.effect_value, player.stats.max_stamina)

        # Decrement the potion stack
        potion.stack -= 1
        return True
    return False

class BattleOptions(discord.ui.View, CommonResponses):
    def __init__(self, interaction, player, player_data, battle_context, special_attack_options_view):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.player = player
        self.player_data = player_data
        self.battle_context = battle_context
        self.special_attack_options_view = special_attack_options_view
        self.author_id = str(interaction.user.id)

        # Initialize buttons with potion stack counts in the labels
        self.stamina_button = self.create_potion_button("Stamina Potion", self.stamina_button_callback)
        self.super_stamina_button = self.create_potion_button("Super Stamina Potion", self.super_stamina_button_callback)
        self.health_button = self.create_potion_button("Health Potion", self.health_button_callback)
        self.super_health_button = self.create_potion_button("Super Health Potion", self.super_health_button_callback)

        # Add buttons to the view
        self.add_item(self.stamina_button)
        self.add_item(self.super_stamina_button)
        self.add_item(self.health_button)
        self.add_item(self.super_health_button)

    def create_potion_button(self, potion_name, callback):
        stack_count = self.player.get_potion_stack(potion_name)
        emoji_str = get_emoji(potion_name)
        emoji_id = int(emoji_str.split(':')[2].strip('>'))
        emoji = discord.PartialEmoji(name=potion_name, id=emoji_id)
        button_label = f" {stack_count:,}" if stack_count else ""
        button = discord.ui.Button(
            label=button_label,
            custom_id=potion_name.lower().replace(" ", "_"),
            style=discord.ButtonStyle.blurple,
            emoji=emoji,
            disabled=self.is_potion_disabled(potion_name)
        )
        button.callback = callback
        return button

    def update_potion_button_label(self, button, potion_name):
        stack_count = self.player.get_potion_stack(potion_name)
        button.label = f"{stack_count}" if stack_count else ""

    async def stamina_button_callback(self, interaction):
        # Check authorization
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        await self.use_potion("Stamina Potion", interaction, self.stamina_button)

    async def super_stamina_button_callback(self, interaction):
        # Check authorization
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        await self.use_potion("Super Stamina Potion", interaction, self.super_stamina_button)

    async def health_button_callback(self, interaction):
        # Check authorization
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        await self.use_potion("Health Potion", interaction, self.health_button)

    async def super_health_button_callback(self, interaction):
        # Check authorization
        if str(interaction.user.id) != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        await self.use_potion("Super Health Potion", interaction, self.super_health_button)

    def is_potion_disabled(self, potion_name):
        potion = next((item for item in self.player.inventory.potions if item.name == potion_name), None)
        return potion is None or potion.stack <= 0

    async def use_potion(self, potion_name, interaction, button):
        # Defer the interaction first
        await interaction.response.defer()

        potion_used = use_potion_logic(self.player, potion_name)

        # Save any changes to player data
        save_player_data(self.interaction.guild_id, self.author_id, self.player_data)

        if potion_used:
            # Update the button label to show new stack count
            self.update_potion_button_label(button, potion_name)

            # Check if the potion is now disabled
            button.disabled = self.is_potion_disabled(potion_name)

            # Generate and append the potion usage message
            potion = next((p for p in self.player.inventory.potions if p.name == potion_name), None)
            if potion:
                emoji_str = get_emoji(potion_name)
                potion_message = f"{emoji_str} **{potion_name} restores {potion.effect_value} {potion.effect_stat}**"
                await self.battle_context.add_battle_message(potion_message)

            # Attempt to update battle embed
            try:
                # Calculate the updated footer text including the run percentage
                updated_footer_text = footer_text_for_embed(interaction, self.battle_context.monster, self.player)
                battle_embed = create_battle_embed(
                    self.interaction.user, self.player, self.battle_context.monster, updated_footer_text,
                    self.battle_context.battle_messages
                )
                await self.battle_context.message.edit(embed=battle_embed)
            except discord.NotFound:
                pass

            # Since we deferred, attempt to use followup to edit the message
            try:
                await interaction.followup.edit_message(interaction.message.id, view=self)
            except discord.NotFound:
                pass

            # Update SpecialAttackOptions button states if available
            if self.special_attack_options_view:
                self.special_attack_options_view.update_button_states()
                try:
                    await self.battle_context.special_attack_message.edit(view=self.special_attack_options_view)
                except discord.NotFound:
                    pass

class SpecialAttackOptions(discord.ui.View, CommonResponses):
    stamina_costs = {1: 1, 2: 10, 3: 20, 4: 30}

    def __init__(self, battle_context, battle_options_msg, special_attack_message):
        super().__init__(timeout=None)

        self.battle_context = battle_context
        self.battle_options_msg = battle_options_msg
        self.special_attack_message = special_attack_message
        self.ctx = battle_context.ctx
        self.player = battle_context.player
        self.monster = battle_context.monster
        self.battle_embed_message = battle_context.message
        self.author_id = battle_context.user.id
        self.battle_messages = battle_context.battle_messages

        self.equip_weapon = self.player.inventory.equipped_weapon
        self.special_attack = self.equip_weapon.special_attack if self.equip_weapon else 0

        # Determine the maximum special attack level based on player's special_attack
        self.max_special_attack_level = min(4, self.special_attack)

        # Create buttons based on the maximum special attack level
        self.create_buttons()

        # Manage the run/cooldown states
        self.run_button_disabled = False
        self.run_button_cooldown = False

    def create_buttons(self):
        attack_emojis = ["left_click", "right_click", "q", "e"]

        for i in range(1, self.max_special_attack_level + 1):
            emoji = get_emoji(attack_emojis[i - 1])
            custom_id = f"attack_{i}"

            # Disable the button if the player doesn't have enough stamina
            disabled_state = self.player.stats.stamina < self.stamina_costs[i]

            button = discord.ui.Button(style=discord.ButtonStyle.blurple, custom_id=custom_id, emoji=emoji,
                                       disabled=disabled_state)
            button.callback = self.on_button_click  # Assigning the callback function

            # Add the button to the view
            self.add_item(button)

        # Add the unarmed button if no weapon is equipped
        unarmed_stamina_cost = 1  # Define the stamina cost for unarmed attack
        unarmed_button_disabled = self.player.stats.stamina < unarmed_stamina_cost  # Disable if stamina is too low

        if not self.equip_weapon:
            button = discord.ui.Button(
                style=discord.ButtonStyle.blurple,
                custom_id="unarmed",
                emoji="👊🏽",
                disabled=unarmed_button_disabled  # Set disabled state based on current stamina
            )
            button.callback = self.on_button_click  # Assigning the callback function
            self.add_item(button)

        # Add the 'Run' button
        run_button = discord.ui.Button(style=discord.ButtonStyle.red, label="Run", custom_id="run")
        run_button.callback = self.on_run_button_click
        self.add_item(run_button)

    async def reenable_run_button_after_delay(self, interaction):
        # Set sleep time based on the stamina value
        sleep_time = 2 if self.player.stats.stamina == 0 else 1
        await asyncio.sleep(sleep_time)

        self.run_button_disabled = False
        self.run_button_cooldown = False
        self.update_button_states()
        try:
            await interaction.edit_original_response(view=self)
        except discord.NotFound:
            pass

    async def on_run_button_click(self, interaction: discord.Interaction):
        # Authorization check
        if interaction.user.id != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        await interaction.response.defer()

        # Calculate the dynamic run chance
        run_chance = calculate_run_chance(self.player, self.battle_context.monster.health, self.battle_context.monster.max_health, interaction.guild_id)

        # Successful escape
        if random.random() < run_chance:
            self.battle_context.end_battle()
            self.disable_all_buttons()
            await self.battle_options_msg.delete()
            await self.special_attack_message.delete()

            # Add successful escape message to battle messages
            await self.battle_context.add_battle_message(
                f"**{interaction.user.mention} has successfully fled the battle with the {self.battle_context.monster.name}!**")

            # Clear the battle flag
            player_data = load_player_data(self.battle_context.ctx.guild.id, str(self.battle_context.user.id))
            player_data["location"] = None
            save_player_data(self.battle_context.ctx.guild.id, str(self.battle_context.user.id), player_data)


        else:  # Failed escape
            self.disable_run_button()
            await interaction.edit_original_response(view=self)
            self.run_button_cooldown = True
            # Add failed escape attempt to battle messages
            await self.battle_context.add_battle_message(f"**{interaction.user.mention} tried to flee but failed!**")
            # Schedule re-enabling the run button
            asyncio.create_task(self.reenable_run_button_after_delay(interaction))
            await interaction.edit_original_response(view=self)

    def disable_run_button(self):
        self.run_button_disabled = True
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.custom_id == "run":
                item.disabled = True

    def update_button_states(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.custom_id.startswith("attack_"):
                    # Disable attack buttons based on stamina
                    attack_level = int(item.custom_id.split("_")[-1])
                    item.disabled = self.player.stats.stamina < self.stamina_costs[attack_level]
                elif item.custom_id == "run":
                    # Enable the 'Run' button only if not in cooldown or disabled
                    item.disabled = self.run_button_disabled or self.run_button_cooldown
                elif item.custom_id == "unarmed":
                    # Disable the unarmed button if the player's stamina is too low
                    unarmed_stamina_cost = 1  # Define the stamina cost for unarmed attack
                    item.disabled = self.player.stats.stamina < unarmed_stamina_cost

    async def on_button_click(self, interaction: discord.Interaction):
        # Authorization check
        if interaction.user.id != self.author_id:
            await self.nero_unauthorized_user_response(interaction)
            return

        await interaction.response.defer()
        custom_id = interaction.data["custom_id"]
        attack_level = 1 if custom_id == "unarmed" else int(custom_id.split("_")[-1])

        # Disable all buttons immediately to prevent spamming
        self.disable_all_buttons()

        # Update the view to reflect the disabled buttons
        await interaction.edit_original_response(view=self)

        # Now proceed with the attack handling
        await self.handle_attack(interaction, attack_level)

        # After handling the attack, update the button states based on the new game context
        self.update_button_states()

        try:
            # Finally, edit the original response to reflect the updated button states
            await interaction.edit_original_response(view=self)
        except discord.NotFound:
            pass

    def disable_unarmed_button(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.custom_id == "unarmed":
                item.disabled = True

    def disable_all_buttons(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

    async def handle_attack(self, interaction, attack_level):
        from monsters.monster import player_attack_task

        # Deduct stamina before performing the attack, ensuring it doesn't fall below 0
        self.player.stats.stamina = max(self.player.stats.stamina - self.stamina_costs[attack_level], 0)

        # Check if the player is unarmed
        is_unarmed = attack_level == 1 and self.battle_context.player.inventory.equipped_weapon is None

        # Perform the attack with the unarmed check
        await player_attack_task(self.battle_context, attack_level, guild_id=interaction.guild_id, is_unarmed=is_unarmed)

        # After monster's health changes, update the battle embed
        new_footer_text = footer_text_for_embed(self.ctx, self.monster, self.player)
        updated_embed = create_battle_embed(self.battle_context.user, self.player, self.monster, new_footer_text,
                                            self.battle_messages)
        await self.battle_embed_message.edit(embed=updated_embed)

        # Check if the monster is already defeated
        if self.battle_context.monster.is_defeated():
            # Check if the interaction has not been responded to
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"The monster {self.battle_context.monster.name} is already dead!", ephemeral=True)
            return

        try:
            # Update button states based on the new stamina level
            self.update_button_states()

            # Update the Discord view again to reflect the re-enabled buttons
            await interaction.edit_original_response(view=self)
        except discord.NotFound:
            pass

def calculate_run_chance(player, monster_health, monster_max_health, guild_id):

    base_run_chance = get_server_setting(guild_id, 'base_run_chance')

    # Calculate base run chance
    if monster_health > monster_max_health * 0.5:
        run_chance = base_run_chance  # Base chance if monster health is above 50%
    else:
        # Linearly increase the run chance from base to 50% as monster health decreases from 50% to 0%
        run_chance = base_run_chance + ((0.5 - base_run_chance) * ((monster_max_health * 0.5 - monster_health) / (monster_max_health * 0.5)))

    # Double the run chance if Ironhide charm is equipped
    if player.inventory.equipped_charm and player.inventory.equipped_charm.name == "Ironhide":
        run_chance *= 2

    # Halve the run chance if player's stamina is 0
    if player.stats.stamina == 0:
        run_chance *= 0.5

    # Ensure run chance does not exceed 100%
    return min(run_chance, 1.0)


def create_health_bar(current, max_health):
    bar_length = 25  # Fixed bar length
    health_percentage = current / max_health
    filled_length = round(bar_length * health_percentage)

    # Calculate how many '▣' symbols to display
    filled_symbols = '◼' * filled_length

    # Calculate how many '-' symbols to display
    empty_symbols = '◻' * (bar_length - filled_length)
    return filled_symbols + empty_symbols

def create_monster_health_bar(current, max_health):
    bar_length = 25  # Fixed bar length
    health_percentage = current / max_health
    filled_length = round(bar_length * health_percentage)

    # Calculate how many '▣' symbols to display
    filled_symbols = '◼' * filled_length

    # Calculate how many '-' symbols to display
    empty_symbols = '◻' * (bar_length - filled_length)
    return filled_symbols + empty_symbols

def create_stamina_bar(current, max_stamina):
    bar_length = 25  # Fixed bar length
    stamina_percentage = current / max_stamina
    filled_length = round(bar_length * stamina_percentage)

    # Calculate how many '◼' symbols to display
    filled_symbols = '◼' * filled_length

    # Calculate how many '◻' symbols to display
    empty_symbols = '◻' * (bar_length - filled_length)
    return filled_symbols + empty_symbols

def create_battle_embed(user, player, monster, footer_text, messages=None):

    player_health_bar = create_health_bar(player.stats.health, player.stats.max_health)
    player_stamina_bar = create_stamina_bar(player.stats.stamina, player.stats.max_stamina)
    monster_health_bar = create_monster_health_bar(monster.health, monster.max_health)

    zone_level = player.stats.zone_level

    # Emojis for each zone
    zone_emoji_mapping = {
        1: 'common_emoji',
        2: 'uncommon_emoji',
        3: 'rare_emoji',
        4: 'epic_emoji',
        5: 'legendary_emoji'
    }

    color_mapping = {
        1: 0x969696,
        2: 0x15ce00,
        3: 0x0096f1,
        4: 0x9900ff,
        5: 0xfebd0d
    }

    # Get the appropriate emoji for the current zone
    zone_emoji = get_emoji(zone_emoji_mapping.get(zone_level))
    embed_color = color_mapping.get(zone_level)

    # Replace spaces with '%20' for URL compatibility
    monster_name_url = monster.name.replace(" ", "%20")
    # Construct image URL
    image_url = generate_urls("monsters", monster_name_url)

    if isinstance(messages, list):
        messages = "\n".join(messages)
    elif isinstance(messages, str):
        messages = messages
    else:
        messages = ""

    embed = Embed(title=f"{zone_emoji} {monster.name}", color=embed_color)

    # Add Battle Messages
    embed.add_field(name="Battle Outcome", value=messages, inline=False)

    # Add an extra blank space before the player's health and stamina bars
    embed.add_field(name='', value='', inline=False)

    # Add Health and Stamina Bars
    embed.add_field(name=user.name,
                    value=f"{get_emoji('heart_emoji')} {player.stats.health}/{player.stats.max_health}\n{player_health_bar}",
                    inline=False)
    embed.add_field(name="",
                    value=f"{get_emoji('stamina_emoji')} {player.stats.stamina}/{player.stats.max_stamina}\n{player_stamina_bar}",
                    inline=False)
    embed.add_field(name=f"{monster.name}",
                    value=f"{get_emoji('heart_emoji')} {monster.health}/{monster.max_health}\n{monster_health_bar}",
                    inline=False)

    # Add image to embed
    embed.set_image(url=image_url)
    # Set the footer for the embed
    embed.set_footer(text=footer_text)

    return embed

def footer_text_for_embed(ctx, monster=None, player=None):
    with open("level_data.json", "r") as f:
        LEVEL_DATA = json.load(f)

    guild_id = ctx.guild.id
    author_id = str(ctx.user.id)
    player_data = load_player_data(guild_id, author_id)

    current_combat_level = player_data["stats"]["combat_level"]
    next_combat_level = current_combat_level + 1
    current_combat_experience = player_data["stats"]["combat_experience"]
    formatted_current_combat_experience = "{:,}".format(current_combat_experience)

    # Generate base footer text based on combat level
    if next_combat_level >= 100:
        footer_text = f"⚔️ Combat Level: {current_combat_level} | 📊 Max Level! {formatted_current_combat_experience} XP"
    else:
        next_level_experience_needed = LEVEL_DATA.get(str(current_combat_level), {}).get("total_experience")
        experience_to_next_level = next_level_experience_needed - current_combat_experience
        formatted_experience_to_next_level = "{:,}".format(experience_to_next_level)
        footer_text = f"⚔️ Combat: {current_combat_level} ~~ 📊 XP to {next_combat_level}: {formatted_experience_to_next_level}"

    # Calculate and append the run chance if the monster is not defeated
    if monster and not monster.is_defeated():
        run_chance = calculate_run_chance(player, monster.health, monster.max_health, guild_id)
        run_chance_percent = round(run_chance * 100)  # Convert to percentage
        footer_text += f" ~~ 💨 Run {run_chance_percent}%"

    return footer_text





