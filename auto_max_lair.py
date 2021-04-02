"""Main script for automating Dynamax Adventures."""

#       Eric Donders
#       Contributions from Miguel Tavera, Discord user fawress,
#           Discord user pifopi, and Discord user denvoros
#       Created 2020-11-20

import logging
import logging.handlers
import os
import sys
from datetime import datetime

import pytesseract
import toml

import automaxlair
from automaxlair import matchup_scoring

VERSION = 'v0.8-beta-20210328'

# load configuration from the config file
try:
    config = toml.load("Config.toml")
except FileNotFoundError:
    raise FileNotFoundError(
        "The Config.toml file was not found! Be sure to copy "
        "Config.sample.toml as Config.toml and edit it!")
except Exception:
    raise SyntaxError(
        "Something went wrong parsing Config.toml\n"
        "Please make sure you entered the information right "
        "and did not modify \" or . symbols or have uppercase true or false "
        "in the settings.")

COM_PORT = config['COM_PORT']
VIDEO_INDEX = config['VIDEO_INDEX']
VIDEO_EXTRA_DELAY = config['advanced']['VIDEO_EXTRA_DELAY']
BOSS = config['BOSS'].lower().replace(' ', '-')
BOSS_INDEX = config['advanced']['BOSS_INDEX']
pytesseract.pytesseract.tesseract_cmd = config['TESSERACT_PATH']
ENABLE_DEBUG_LOGS = config['advanced']['ENABLE_DEBUG_LOGS']
NON_LEGEND = config['advanced']['NON_LEGEND'].lower().replace(' ', '-')
FIND_PATH_WINS = config['FIND_PATH_WINS']

# Set the log name
LOG_NAME = f"{BOSS}_{datetime.now().strftime('%Y-%m-%d %H-%M-%S')}"


def initialize(ctrlr) -> str:
    """Placeholder. Immediately enter the join stage."""
    # send a discord message that we're ready to rumble
    ctrlr.send_discord_message(
        f"Starting a new full run for {ctrlr.boss}!",
        embed_fields=ctrlr.get_stats_for_discord(), level="update"
    )
    ctrlr.log(f'Initializing AutoMaxLair {VERSION}.')

    # assume we're starting from the select controller menu, connect, then
    # press home twice to return to the game
    ctrlr.push_buttons(
        (b'a', 2), (b'h', 2.0), (b'h', 2.0), (b'b', 1.5), (b'b', 1.5)
    )

    return 'join'


def join(ctrlr) -> str:
    """Join a Dynamax Adventure and choose a Pokemon."""
    run = ctrlr.current_run
    # Start a new Dynamax Adventure.
    #
    # First, start a new run by talking to the scientist in the Max Lair.
    ctrlr.log(f'Run #{ctrlr.runs + 1} started!')
    ctrlr.push_buttons(
        (b'b', 2), (b'a', 1), (b'a', 1.5), (b'a', 1.5), (b'a', 1.5), (b'b', 1)
    )

    # select the right path
    for __ in range(BOSS_INDEX):
        ctrlr.push_button(b'v', 1)

    ctrlr.push_buttons(
        (b'a', 1.5), (b'a', 1), (b'a', 1.5), (b'a', 4), (b'v', 1),
        (b'a', 3 + VIDEO_EXTRA_DELAY)
    )

    # Next, read what rental Pokemon are available to choose.
    # Note that pokemon_list contains preconfigured Pokemon objects with types,
    # abilities, stats, moves, et cetera.
    pokemon_list = ctrlr.read_selectable_pokemon('join')
    pokemon_scores = []

    # Then, assign a score to each of the Pokemon based on how it is estimated
    # to perform against the minibosses (other rental Pokemon) and the final
    # boss.
    for pokemon in pokemon_list:
        name_id = pokemon.name_id
        # Consider the amount of remaining minibosses when scoring each rental
        # Pokemon, at the start of the run, there are 3 minibosses and 1 final
        # boss. We weigh the boss more heavily because it is more difficult
        # than the other bosses.
        rental_weight = 3
        boss_weight = 2
        score = matchup_scoring.get_weighted_score(
            run.rental_scores[name_id], rental_weight,
            run.boss_matchups[name_id][ctrlr.boss], boss_weight
        )
        pokemon_scores.append(score)
        ctrlr.log(f'Score for {name_id}: {score:.2f}', 'DEBUG')
    selection_index = pokemon_scores.index(max(pokemon_scores))
    for __ in range(selection_index):
        ctrlr.push_button(b'v', 1)
    run.pokemon = pokemon_list[selection_index]
    ctrlr.push_button(b'a', 22 + VIDEO_EXTRA_DELAY)

    # Read teammates.
    ctrlr.identify_team_pokemon()

    # Read the path.
    ctrlr.read_path_information(1)
    ctrlr.push_button(b'8', 2 + VIDEO_EXTRA_DELAY, 7)
    ctrlr.read_path_information(2)
    ctrlr.log(f'Path type identified as: {run.path_type}')
    ctrlr.push_button(b'8', 2 + VIDEO_EXTRA_DELAY, 8)
    ctrlr.read_path_information(3)
    for line in run.get_output_strings():
        ctrlr.log(line)
    all_paths_str = run.get_paths(truncate=True, name_only=True)

    # Choose the best path out of the options.
    # TODO: Improve path selection algorithm.
    best_path_index, target_path_str, score_list = run.path_tree.get_best_path(
        run.boss, all_paths_str
    )
    for i, path_str in enumerate(all_paths_str):
        ctrlr.log(
            f'Path at index {i} has score: {score_list[i]:.3f} and sequence: '
            f'{path_str}', 'DEBUG')
    run.target_path = run.get_paths()[best_path_index]
    ctrlr.log(
        f'Target path at index {best_path_index} selected with score '
        f'{score_list[best_path_index]:.3f}: {target_path_str}.')

    ctrlr.log('Finished joining.', 'DEBUG')
    return 'path'


def path(ctrlr) -> str:
    """Choose a path to follow."""
    run = ctrlr.current_run
    ctrlr.log('Choosing a path to follow.', 'DEBUG')
    # Check what direction the target path is.
    offset = run.get_next_fork_offset()
    # Then, move the cursor onto that boss and select it.
    for __ in range(offset):
        ctrlr.push_button(b'>', 1)
    ctrlr.push_button(b'a', 4 + VIDEO_EXTRA_DELAY)
    run.advance_node()
    ctrlr.log(
        f'Chose path with index {offset} from the left, towards type '
        f'{run.current_node.name}.', 'DEBUG')
    return 'detect'


def detect(ctrlr) -> str:
    """Detect whether the chosen path has led to a battle, scientist,
    backpacker, or fork in the path.
    """

    ctrlr.log('Detecting where the path led.', 'DEBUG')
    # Loop continually until an event is detected.
    # Relevant events include a battle starting, a backpacker encountered,
    # a scientist encountered, or a fork in the path.
    #
    # This function returns directly when those conditions are found.
    while True:
        state = ctrlr.read_in_den_state()
        if state is not None:
            return state
        ctrlr.push_button(None, 0.1)


def battle(ctrlr) -> str:
    """Choose moves during a battle and detect whether the battle has ended."""
    run = ctrlr.current_run
    ctrlr.log(f'Battle {run.num_caught+1} starting.')
    # Wait for the black screen at the start of the battle to go away.
    ctrlr.push_button(None, 13)
    while ctrlr.check_black_screen():
        ctrlr.push_button(None, 1)
    # Loop continuously until an event that ends the battle is detected.
    # The battle ends either in victory (signalled by the catch screen)
    # or in defeat (signalled by the screen going completely black).
    #
    # This function returns directly when those conditions are found.
    while True:
        # Read text from the bottom section of the screen.
        battle_state = ctrlr.read_in_battle_state()

        # Check the text for key phrases that inform the bot what to do next.
        if battle_state == 'CATCH':
            ctrlr.log('Battle finished.', 'DEBUG')
            run.reset_stage()
            return 'catch'
        elif battle_state == 'FAINT':
            run.lives -= 1
            ctrlr.log(f'Pokemon fainted. {run.lives} lives remaining.')
            ctrlr.push_button(None, 3.5)
        elif battle_state == 'LOSS':
            ctrlr.log('You lose and the battle is finished.')
            run.lives -= 1
            if run.lives != 0:
                ctrlr.log('The lives counter was not 0.', 'WARNING')
                run.lives = 0
            run.reset_stage()
            ctrlr.push_button(None, 7)
            return 'select_pokemon'  # Go to quit sequence.
        elif battle_state == 'CHEER':
            ctrlr.log('Cheering for your teammates.', 'DEBUG')
            if run.pokemon.dynamax:
                run.pokemon.dynamax = False
                run.move_index = 0
                run.dmax_timer = 0
            ctrlr.push_buttons((b'a', 1.5), (b'b', 1 + VIDEO_EXTRA_DELAY))
        elif battle_state == 'FIGHT':
            # Before the bot makes a decision, it needs to know what the boss
            # is.
            if run.opponent is None:
                # If we have defeated three oppoenents already we know the
                # opponent is the boss Pokemon.
                if run.num_caught == 3:
                    run.opponent = run.boss_pokemon[BOSS]

                # Otherwise, we identify the boss using its name and types.
                else:
                    #
                    ctrlr.push_buttons(
                        (b'y', 1), (b'a', 1), (b'l', 3 + VIDEO_EXTRA_DELAY))
                    run.opponent = ctrlr.read_selectable_pokemon('battle')[0]
                    ctrlr.push_buttons((b'b', 1), (b'b', 1.5), (b'b', 2))

                    if run.opponent.name_id == 'ditto':
                        if run.current_node.name != 'normal':
                            ctrlr.log(
                                f'We were expecting a {run.current_node.name} '
                                'type pokemon and we got ditto.', 'WARNING')
                    else:
                        if run.current_node.name not in run.opponent.type_ids:
                            ctrlr.log(
                                f'We were expecting a {run.current_node.name} '
                                'type pokemon and we got '
                                f'{run.opponent.name_id}.', 'WARNING')

                # If our Pokemon is Ditto, transform it into the boss (or vice
                # versa).
                if run.pokemon.name_id == 'ditto':
                    run.pokemon = matchup_scoring.transform_ditto(
                        run.pokemon, run.opponent)
                elif run.opponent.name_id == 'ditto':
                    ctrlr.opponent = (
                        matchup_scoring.transform_ditto(
                            run.opponent, run.pokemon))

            # Handle the Dynamax timer
            # The timer starts at 3 and decreases by 1 after each turn of
            # Dynamax.
            # A value of -1 indicates a pre-dynamax state (i.e., someone can
            # Dynamax).
            # A value of 0 indicates Dynamax has ended and nobody can Dynamax
            # for the remainder of the battle.
            if run.dmax_timer == 1:
                run.dmax_timer = 0
                run.move_index = 0
                run.pokemon.dynamax = False
            elif run.dmax_timer > 1:
                run.dmax_timer -= 1

            # Navigate to the move selection screen.
            ctrlr.push_button(b'a', 2 + VIDEO_EXTRA_DELAY)

            # Then, check whether Dynamax is available.
            # Note that a dmax_timer value of -1 indicates that the player's
            # Pokemon has not Dynamaxed yet.
            # If no Pokemon has Dynamaxed yet, check_dynamax_available visually
            # detects if the player can Dynamax by observing the icon.
            run.dynamax_available = (
                run.dmax_timer == -1 and ctrlr.check_dynamax_available()
            )
            # Choose the best move to use against the boss
            best_move_index, __, best_move_score = (
                matchup_scoring.select_best_move(
                    run.pokemon, run.opponent, run.field,
                    teammates=run.team_pokemon)
            )
            if run.dynamax_available:
                default_score = best_move_score
                run.pokemon.dynamax = True  # Temporary
                best_max_move_index, __, best_dmax_move_score = (
                    matchup_scoring.select_best_move(
                        run.pokemon, run.opponent, run.field,
                        teammates=run.team_pokemon)
                )
                if best_dmax_move_score > default_score:
                    best_move_index = best_max_move_index
                else:
                    # Choose not to Dynamax this time by making the following
                    # code think that it isn't available.
                    run.dynamax_available = False
                run.pokemon.dynamax = False  # Revert previous temporary change

            # Navigate to the correct move and use it.
            # Note that ctrlr.dynamax_available is set to false if dynamax is
            # available but not optimal.
            if run.dynamax_available:
                # Dynamax and then choose a move as usual
                ctrlr.push_buttons((b'<', 1), (b'a', 1))
                run.dmax_timer = 3
                run.pokemon.dynamax = True
                run.dynamax_available = False
            move = (
                run.pokemon.max_moves[best_move_index] if run.pokemon.dynamax
                else run.pokemon.moves[best_move_index]
            )
            ctrlr.log(
                f'Best move against {run.opponent.name_id}: {move.name_id} '
                f'(index {best_move_index})', 'DEBUG'
            )
            run.move_index %= 4  # Loop index back to zero if it exceeds 3
            for __ in range((best_move_index - run.move_index + 4) % 4):
                ctrlr.push_button(b'v', 0.5)
                run.move_index = (run.move_index + 1) % 4
            # Select the attack and then mash a bunch of buttons to try and
            # recover if something goes wrong.
            ctrlr.push_buttons(
                (b'a', 1), (b'a', 1), (b'a', 1), (b'v', 1), (b'a', 0.5),
                (b'b', 0.5), (b'^', 0.5), (b'b', 0.5)
            )
            run.pokemon.PP[run.move_index] -= (
                1 if run.opponent.ability_name_id != 'pressure' else 2
            )
        else:
            # Press B which can speed up dialogue
            ctrlr.push_button(b'b', 0.1)


def catch(ctrlr) -> str:
    """Catch each boss after defeating it."""
    run = ctrlr.current_run
    # Check if we need to skip catching a the final boss.
    # This scenario is used by Ball Saver mode when it can't afford to reset
    # the game.
    if (
        run.num_caught == 3 and ctrlr.mode == 'ball saver'
        and not ctrlr.check_sufficient_ore(1)
    ):
        ctrlr.log('Finishing the run without wasting a ball on the boss.')
        ctrlr.push_buttons((b'v', 2), (b'a', 10))
        ctrlr.log('Congratulations!')
        return 'select_pokemon'

    # Catch the boss in almost all cases.
    ctrlr.log(f'Catching boss #{run.num_caught + 1}.')
    # Start by navigating to the ball selection screen
    ctrlr.push_button(b'a', 2)
    # then navigate to the ball specified in the config file
    while (ctrlr.get_target_ball() not in ctrlr.check_ball()):
        ctrlr.push_button(b'<', 2 + VIDEO_EXTRA_DELAY)
    ctrlr.push_button(b'a', 30)
    ctrlr.record_ball_use()

    # If the caught Pokemon was not the final boss, check out the Pokemon and
    # decide whether to keep it.
    if run.num_caught < 4:
        # Note that read_selectable_pokemon returns a list of preconfigured
        # Pokemon objects with types, abilities, stats, moves, et cetera.
        #
        # In this stage the list contains only 1 item.
        pokemon = ctrlr.read_selectable_pokemon('catch')[0]
        run.caught_pokemon.append(pokemon.name_id)

        # Update the list of potential minibosses that we might encounter later
        # in the den.
        run.prune_potential_minibosses()
        ctrlr.log(
            'The following Pokemon have been encountered and will not appear '
            f'again: {run.all_encountered_pokemon}', 'DEBUG'
        )
        ctrlr.log(
            'The following Pokemon may still appear along the target path: '
            f'{[x for x in run.potential_boss_pokemon]}', 'DEBUG'
        )
        # Consider the amount of remaining minibosses when scoring each rental
        # Pokemon, at the start of the run, there are 3 - num_caught minibosses
        # and 1 final boss. We weigh the boss more heavily because it is more
        # difficult than the other bosses.
        rental_weight = 3 - run.num_caught
        boss_weight = 2

        # Calculate scores for every potential team resulting from the decision
        # to take or leave the new Pokemon.
        team = run.team_pokemon
        # Re-measure team HP.
        for i, HP in enumerate(ctrlr.measure_team_HP()):
            if i == 0:
                run.pokemon.HP = HP
            else:
                team[i - 1].HP = HP
        team_scores = []
        potential_teams = (
            (pokemon, team[0], team[1], team[2]),
            (run.pokemon, team[0], team[1], team[2]),
            (run.pokemon, pokemon, team[1], team[2]),
            (run.pokemon, team[0], pokemon, team[2]),
            (run.pokemon, team[0], team[1], pokemon)
        )
        ctrlr.log(f'HP of current team: {[x.HP for x in team]}.', 'DEBUG')
        for potential_team in potential_teams:
            score = matchup_scoring.get_weighted_score(
                matchup_scoring.evaluate_average_matchup(
                    potential_team[0], run.potential_boss_pokemon.values(),
                    potential_team[1:], run.lives
                ), rental_weight,
                matchup_scoring.evaluate_matchup(
                    potential_team[0], run.boss_pokemon[run.boss],
                    potential_team[1:], run.lives
                ), boss_weight
            )
            ctrlr.log(
                'Score for potential team: '
                f'{[x.name_id for x in potential_team]}: {score:.2f}', 'DEBUG')
            team_scores.append(score)
        # Choosing not to take the Pokemon may result in a teammate choosing
        # it, or none may choose it. The mechanics of your teammates choosing
        # is currently not known. Qualitatively, it seems like they choose yes
        # or no randomly with about 50% chance. Using this assumption, the
        # chance that none of them take the Pokemon is (1/2)^3 or 12.5%.
        choose_score = team_scores[0]
        leave_score = 0.125 * team_scores[1] + 0.875 * sum(team_scores[2:]) / 3
        ctrlr.log(
            f'Score for taking {pokemon.name_id}: {choose_score:.2f}', 'DEBUG')
        ctrlr.log(
            f'Score for declining {pokemon.name_id}: {leave_score:.2f}',
            'DEBUG')

        # Compare the scores for the two options and choose the best one.
        if choose_score > leave_score:
            # Choose to swap your existing Pokemon for the new Pokemon.
            run.pokemon = pokemon
            ctrlr.log(f'Decided to swap for {run.pokemon.name_id}.')
            # Note: a long delay is required here so the bot doesn't think a
            # battle started.
            ctrlr.push_button(b'a', 6)

        else:
            ctrlr.log(f'Decided to keep going with {run.pokemon.name_id}.')
            # Note: a long delay is required here so the bot doesn't think a
            # battle started.
            ctrlr.push_button(b'b', 6)

        # Re-read teammates in case something changed.
        ctrlr.identify_team_pokemon()
        run.prune_potential_minibosses()

        # Move on to the detect stage.
        return 'detect'

    # If the final boss was the caught Pokemon, wrap up the run and check the
    # Pokemon caught along the way.
    else:
        run.caught_pokemon.append(ctrlr.boss)
        ctrlr.push_button(None, 10)
        ctrlr.log('Congratulations!')
        return 'select_pokemon'


def backpacker(ctrlr) -> str:
    """Choose an item from the backpacker."""
    ctrlr.push_button(None, 1 + VIDEO_EXTRA_DELAY)

    ctrlr.log("Reading the backpacker's items.")

    items = []
    frame = ctrlr.get_frame()
    for rect in (
        ctrlr.item_rect_1, ctrlr.item_rect_2, ctrlr.item_rect_3,
        ctrlr.item_rect_4, ctrlr.item_rect_5
    ):
        item = ctrlr.read_text(
            frame, rect, threshold=False, invert=False,
            segmentation_mode='--psm 7').strip()
        items.append(item)
        ctrlr.log(f'Detected item: {item}', 'DEBUG')

    # Note: a long delay is required here so the bot doesn't think a battle
    # started.
    ctrlr.push_button(b'a', 7 + VIDEO_EXTRA_DELAY)

    ctrlr.log('Finished choosing an item.', 'DEBUG')
    return 'detect'


def scientist(ctrlr) -> str:
    """Take (or not) a Pokemon from the scientist."""
    run = ctrlr.current_run

    ctrlr.log('Scientist encountered.', 'DEBUG')

    # Consider the amount of remaining minibosses when scoring each rental
    # Pokemon, at the start of the run, there are 3 - num_caught minibosses
    # and 1 final boss. We weigh the boss more heavily because it is more
    # difficult than the other bosses.
    rental_weight = 3 - run.num_caught
    boss_weight = 2

    # Calculate scores for an average and existing Pokemon.
    pokemon_scores = []
    for name_id in run.rental_pokemon:
        score = matchup_scoring.get_weighted_score(
            run.rental_scores[name_id], rental_weight,
            run.boss_matchups[name_id][ctrlr.boss], boss_weight
        )
        pokemon_scores.append(score)
    average_score = sum(pokemon_scores) / len(pokemon_scores)

    # TODO: actually read the current Pokemon's health so the bot can
    # decide to switch if it's low.
    existing_score = matchup_scoring.get_weighted_score(
        run.rental_scores[run.pokemon.name_id], rental_weight,
        matchup_scoring.evaluate_matchup(
            run.pokemon, run.boss_pokemon[ctrlr.boss],
            run.team_pokemon, run.lives
        ), boss_weight
    )
    ctrlr.log(f'Score for average pokemon: {average_score:.2f}', 'DEBUG')
    ctrlr.log(
        f'Score for {run.pokemon.name_id}: {existing_score:.2f}', 'DEBUG')

    if average_score > existing_score:
        # Note: a long delay is required here so the bot doesn't think a
        # battle started.
        ctrlr.push_buttons((None, 3), (b'a', 2 + VIDEO_EXTRA_DELAY))
        run.pokemon = None
        ctrlr.log('Took a Pokemon from the scientist.')
    else:
        # Note: a long delay is required here so the bot doesn't think a
        # battle started.
        ctrlr.push_buttons((None, 3), (b'b', 2 + VIDEO_EXTRA_DELAY))
        ctrlr.log(f'Decided to keep going with {run.pokemon.name_id}')

    # Read teammates.
    ctrlr.identify_team_pokemon()
    # If we took a Pokemon from the scientist, try to identify it.
    # Note: as of Python 3.6, dicts remember insertion order so using an
    # OrderedDict is unnecessary.
    if average_score > existing_score:
        ctrlr.log(f'Identified {run.pokemon.name_id} as our new Pokemon.')
    ctrlr.push_button(None, 3)

    return 'detect'


def select_pokemon(ctrlr) -> str:
    """Check Pokemon caught during the run and keep one if it's shiny.

    Note that this function returns None, causing the program to quit, if a
    shiny legendary Pokemon is found.
    """

    run = ctrlr.current_run
    # If the bot lost against the first boss, skip the checking process since
    # there are no Pokemon to check.
    if run.num_caught == 0:
        ctrlr.log('No Pokemon caught.')
        ctrlr.push_buttons((None, 10), (b'b', 1))
        ctrlr.runs += 1
        ctrlr.send_discord_message(
            "No Pokémon were caught in the last run.",
            embed_fields=ctrlr.get_stats_for_discord(),
            level="update"
        )
        ctrlr.record_ore_reward()
        ctrlr.reset_run()
        ctrlr.log('Preparing for another run.')

        # No Pokemon to review, so go back to the beginning.
        # Note that the "keep path" mode is meant to be used on a good path, so
        # although the path would be lost that situation should never arise.
        return 'join'
    # "find path" mode quits if the run is successful.
    elif run.num_caught == 4 and (
        ctrlr.mode == 'find path'
        and ctrlr.consecutive_resets == FIND_PATH_WINS - 1
    ):
        ctrlr.display_results(screenshot=True)
        ctrlr.send_discord_message(
            f"This path won {FIND_PATH_WINS} times against {ctrlr.boss} with "
            f"{run.lives} lives remaining.",
            path_to_picture=f'logs/{ctrlr.log_name}_cap_'
            f'{ctrlr.num_saved_images}.png',
            embed_fields=ctrlr.get_stats_for_discord(),
            level="critical"
        )
        ctrlr.log(
            f'This path won {FIND_PATH_WINS} times with {run.lives} '
            'lives remaining.')
        return None  # Return None to signal the program to end.

    # Otherwise, navigate to the summary screen of the last Pokemon caught (the
    # legendary if the run was successful)
    ctrlr.log('Checking the haul from this run.', 'DEBUG')
    ctrlr.push_buttons(
        (b'^', 1), (b'a', 1), (b'v', 1), (b'a', 3 + VIDEO_EXTRA_DELAY))

    # Check all Pokemon for shininess.
    take_pokemon = False  # Set to True if a non-legendary shiny is found.
    reset_game = False  # Set to True in some cases in non-default modes.

    if run.num_caught == 4 and (
        ctrlr.check_attack_stat or ctrlr.check_speed_stat
    ):
        ctrlr.push_button(b'>', 1)
        if ctrlr.check_stats():
            ctrlr.log('******************************')
            ctrlr.log('****Matching stats found!*****')
            ctrlr.log('******************************')
            ctrlr.display_results(screenshot=True)
            ctrlr.send_discord_message(
                f"Matching stats found for {ctrlr.boss}!",
                path_to_picture=f'logs/{ctrlr.log_name}_cap_'
                f'{ctrlr.num_saved_images}.png',
                embed_fields=ctrlr.get_stats_for_discord(),
                level="legendary"
            )
            return None  # End whenever a matching stats legendary is found

        ctrlr.push_button(b'<', 1)

    for i in range(run.num_caught):
        # First check if we need to reset immediately.
        # Note that "keep path" mode resets always unless a shiny legendary.
        # is found, and "ball saver" resets if a non-shiny legendary was
        # caught.
        if (
            (ctrlr.mode == 'keep path' and (run.num_caught < 4 or i > 0))
            or (
                (ctrlr.mode == 'ball saver' or ctrlr.mode == 'find path')
                and run.num_caught == 4 and i > 0
                )
        ):
            if (
                (ctrlr.mode == 'ball saver' or ctrlr.mode == 'find path')
                or ctrlr.check_sufficient_ore(2)
                ):
                reset_game = True
                break
            else:
                return None  # End if there isn't enough ore to reset.
        elif ctrlr.check_shiny():
            ctrlr.log('******************************')
            ctrlr.log('*********Shiny found!*********')
            ctrlr.log('******************************')
            ctrlr.log(
                f'Shiny {run.caught_pokemon[run.num_caught - 1 - i]} will be '
                'kept.'
            )
            ctrlr.log(
                "Adding information to the number of found shinies", "DEBUG")
            ctrlr.caught_shinies.append(
                run.caught_pokemon[run.num_caught - 1 - i]
            )
            ctrlr.shinies_found += 1
            ctrlr.log("Sending off to save a screenshot", "DEBUG")
            ctrlr.display_results(screenshot=True)
            ctrlr.push_buttons((b'p', 1), (b'b', 3), (b'p', 1))
            if run.num_caught == 4 and i == 0:
                # NOTE: this is when we found a legendary!
                ctrlr.send_discord_message(
                    f'Found a shiny {run.caught_pokemon[3]}!',
                    path_to_picture=f'logs/{ctrlr.log_name}_cap_'
                    f'{ctrlr.num_saved_images}.png',
                    embed_fields=ctrlr.get_stats_for_discord(),
                    level="legendary"
                )
                return None  # End whenever a shiny legendary is found.
            else:
                ctrlr.send_discord_message(
                    f'Found a shiny '
                    f'{run.caught_pokemon[run.num_caught - 1 - i]}!',
                    path_to_picture=f'logs/{ctrlr.log_name}_cap_'
                    f'{ctrlr.num_saved_images}.png',
                    embed_fields=ctrlr.get_stats_for_discord(),
                    level="shiny"
                )
                take_pokemon = True
                break
        elif i < run.num_caught - 1:
            ctrlr.push_button(b'^', 3 + VIDEO_EXTRA_DELAY)

    if (
        not take_pokemon and ctrlr.mode == 'strong boss'
        and run.num_caught == 4 and ctrlr.check_sufficient_ore(1)
    ):
        reset_game = True

    if (
        not take_pokemon and NON_LEGEND in run.caught_pokemon
        and ctrlr.check_sufficient_ore(1)
    ):
        reset_game = True
        ctrlr.log('----------------------------------')
        ctrlr.log(f'--Found {NON_LEGEND} on this path.--')
        ctrlr.log('----------------------------------')

    # After checking all the Pokemon, wrap up the run (including taking a
    # Pokemon or resetting the game, where appropriate).
    if not reset_game:
        if take_pokemon:
            ctrlr.push_buttons(
                (b'a', 1), (b'a', 1), (b'a', 1), (b'a', 1.5),
                (b'a', 3), (b'b', 2), (b'b', 10), (b'a', 2)
            )
        else:
            ctrlr.push_buttons((b'b', 3), (b'b', 1))
        ctrlr.record_ore_reward()
    else:
        ctrlr.log('Resetting the game to preserve a winning seed.')
        ctrlr.record_game_reset()
        # The original button sequence was added with the help of users fawress
        # and Miguel90 on the Pokemon Automation Discord.
        ctrlr.push_buttons((b'h', 2), (b'x', 2))

    # The button press sequences differ depending on how many Pokemon were
    # defeated and are further modified by the language.
    # Therefore, press A until the starting dialogue appears, then back out.
    while ctrlr.phrases['START_PHRASE'] not in ctrlr.read_text(
        ctrlr.get_frame(),
        ((0, 0.6), (1, 1)), threshold=False
    ):
        ctrlr.push_button(b'a', 1.5)
    ctrlr.push_buttons((b'b', 1.5), (b'b', 1.5))

    # Update statistics and reset stored information about the complete run.
    ctrlr.wins += 1 if run.lives != 0 else 0
    ctrlr.runs += 1
    # calculate the win percent
    ctrlr.win_percent = ctrlr.wins / ctrlr.runs
    # then update the time per run
    ctrlr.time_per_run = (datetime.now() - ctrlr.start_date) / ctrlr.runs
    ctrlr.reset_run()

    # Start another run if there are sufficient Poke balls to do so.
    if ctrlr.check_sufficient_balls():
        ctrlr.log('Preparing for another run.')
        ctrlr.send_discord_message(
            'Preparing for another run.',
            embed_fields=ctrlr.get_stats_for_discord(),
            level="update"
        )
        return 'join'
    else:
        ctrlr.log('Out of balls. Quitting.')
        ctrlr.send_discord_message(
            'You ran out of legendary balls! The program has exited!',
            embed_fields=ctrlr.get_stats_for_discord(),
            level="critical"
        )
        return None  # Return None to signal the program to end.


def main(log_name):
    """Main loop. Runs until a shiny is found or the user manually quits by
    pressing 'Q'.
    """

    # Map stages to the appropriate function to execute when in each stage
    actions = {
        'initialize': initialize, 'join': join, 'path': path, 'detect': detect,
        'battle': battle, 'catch': catch, 'backpacker': backpacker,
        'scientist': scientist, 'select_pokemon': select_pokemon
    }

    controller = automaxlair.da_controller.DAController(
        config, log_name, actions)
    controller.add_info('Version', VERSION)

    # Start the event loop.
    controller.event_loop()


def exception_handler(exception_type, exception_value, exception_traceback):
    """Exception hook to ensure exceptions get logged."""
    logger = logging.getLogger(LOG_NAME)
    logger.error(
        'Exception occurred:',
        exc_info=(exception_type, exception_value, exception_traceback)
    )


if __name__ == '__main__':
    # Set up the logger

    # Configure the logger.
    logger = logging.getLogger(LOG_NAME)
    logger.setLevel(logging.DEBUG if ENABLE_DEBUG_LOGS else logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s: %(message)s'
    )

    # make the console formatter easier to read with fewer bits of info
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s: %(message)s", "%H:%M:%S"
    )

    # Configure the console, which will print logged information.
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG if ENABLE_DEBUG_LOGS else logging.INFO)
    console.setFormatter(console_formatter)

    # Configure the file handler, which will save logged information.
    fileHandler = logging.FileHandler(
        filename=os.path.join('logs', LOG_NAME + '.log'),
        encoding="UTF-8"
    )
    fileHandler.setFormatter(formatter)
    fileHandler.setLevel(logging.DEBUG if ENABLE_DEBUG_LOGS else logging.INFO)

    # Add the handlers to the logger so that it will both print messages to
    # the console as well as save them to a log file.
    logger.addHandler(console)
    logger.addHandler(fileHandler)
    logger.info('Starting new series: %s.', LOG_NAME)

    # Call main
    sys.excepthook = exception_handler
    main(LOG_NAME)
