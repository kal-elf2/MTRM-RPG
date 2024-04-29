from utils import save_player_data, send_message
from monsters.monster import create_battle_embed, monster_battle, generate_monster_by_name
from exemplars.exemplars import Exemplar
from monsters.battle import BattleOptions, LootOptions, footer_text_for_embed
from images.urls import generate_urls
from emojis import get_emoji
from stats import ResurrectOptions

# Define the maximum level for each zone
zone_max_levels = {
1: 20,
2: 40,
3: 60,
4: 80,
}
async def mega_brute_encounter(player_data, ctx, interaction, guild_id, author_id):

    player_data["location"] = "battle"
    save_player_data(guild_id, author_id, player_data)

    player = Exemplar(player_data["exemplar"],
                      player_data["stats"],
                      guild_id,
                      player_data["inventory"])

    monster = generate_monster_by_name('Mega Brute', player.stats.zone_level)

    battle_embed = await send_message(interaction.channel,
                                      create_battle_embed(interaction.user, player, monster,
                                                          footer_text_for_embed(ctx, monster, player)))

    from monsters.monster import BattleContext
    from monsters.battle import SpecialAttackOptions

    def update_special_attack_buttons(context):
        if context.special_attack_options_view:
            context.special_attack_options_view.update_button_states()

    battle_context = BattleContext(ctx, interaction.user, player, monster, battle_embed,
                                   player.stats.zone_level,
                                   update_special_attack_buttons)

    special_attack_options_view = SpecialAttackOptions(battle_context, None, None)
    battle_context.special_attack_options_view = special_attack_options_view

    special_attack_message = await ctx.send(view=special_attack_options_view)
    battle_context.special_attack_message = special_attack_message

    battle_options_msg = await ctx.send(
        view=BattleOptions(ctx, player, player_data, battle_context, special_attack_options_view))
    battle_context.battle_options_msg = battle_options_msg

    special_attack_options_view.battle_options_msg = battle_options_msg
    special_attack_options_view.special_attack_message = special_attack_message

    battle_result = await monster_battle(battle_context, guild_id)

    if battle_result is None:
        # Save the player's current stats
        player_data["stats"].update(player.stats.__dict__)
        save_player_data(guild_id, author_id, player_data)

    else:
        # Unpack the battle outcome and loot messages
        battle_outcome, loot_messages = battle_result
        if battle_outcome[0]:

            # Check if the player is at or above the level cap for their current zone
            if player.stats.zone_level in zone_max_levels and player.stats.combat_level >= zone_max_levels[player.stats.zone_level]:
                # Player is at or has exceeded the level cap for their zone; set XP gain to 0
                experience_gained = 0
            else:
                # Player is below the level cap; award XP from the monster
                experience_gained = monster.experience_reward

            loothaven_effect = battle_outcome[5]  # Get the Loothaven effect status
            messages = await player.gain_experience(experience_gained, 'combat', interaction, player)
            # Ensure messages is iterable if it's None
            messages = messages or []
            for msg_embed in messages:
                await interaction.followup.send(embed=msg_embed, ephemeral=False)

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

            loot_view = LootOptions(interaction, player, monster, battle_embed, player_data,
                                    author_id, battle_outcome,
                                    loot_messages, guild_id, interaction, experience_gained, loothaven_effect, battle_context.rusty_spork_dropped,
                                    add_repeat_button=False)

            # Send max XP cap message if experience gained is 0
            max_cap_message = ""
            if experience_gained == 0:
                max_cap_message = f"\n**(Max XP cap reached for Zone {player.stats.zone_level})**"

            await battle_embed.edit(
                embed=create_battle_embed(interaction.user, player, monster,
                                          footer_text_for_embed(ctx, monster, player),
                                          f"You have **DEFEATED** the {monster.name}!\n\n"
                                          f"You dealt **{battle_outcome[1]} damage** to the monster and took **{battle_outcome[2]} damage**. "
                                          f"You gained {experience_gained} combat XP. {max_cap_message}\n"
                                          f"\n"),
                view=loot_view
            )

        else:
            # The player is defeated
            player.stats.health = 0  # Set player's health to 0
            player_data["stats"]["health"] = 0

            # Create a new embed with the defeat message
            new_embed = create_battle_embed(interaction.user, player, monster, footer_text="", messages=

            f"☠️ You have been **DEFEATED** by the **{monster.name}**!\n"
            f"{get_emoji('rip_emoji')} *Your spirit lingers, seeking renewal.* {get_emoji('rip_emoji')}\n\n"
            f"__**Options for Revival:**__\n"
            f"1. Use {get_emoji('Materium')} to revive without penalty.\n"
            f"2. Resurrect with 2.5% penalty to all skills."
            f"**Lose all items in inventory** (Keep equipped items, coppers, MTRM, potions, and charms)")

            # Clear the previous views
            await battle_context.special_attack_message.delete()
            await battle_options_msg.delete()

            # Add the "dead.png" image to the embed
            new_embed.set_image(
                url=generate_urls("cemetery", "dead"))
            # Update the message with the new embed and view
            await battle_embed.edit(embed=new_embed,
                                    view=ResurrectOptions(interaction, player_data, author_id))

    # Clear the battle flag after the battle ends
    player_data["location"] = None
    save_player_data(guild_id, author_id, player_data)