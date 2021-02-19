#   AutoMaxLair
#       Eric Donders
#       Contributions from Miguel Tavera, Discord user fawress,
#           Discord user pifopi, and Discord user denvoros
#       Created 2020-11-20

import configparser
import logging
import logging.handlers
import os
import re
import sys

from datetime import datetime

import pytesseract

import automaxlair

VERSION = 'v0.7-beta'

# Load configuration from config file
config = configparser.ConfigParser()

# Configparser doesn't complain if it can't find the config file,
# so manually raise an error if the file was not read.
if not config.read('Config.ini', 'utf8'):
    raise FileNotFoundError('Failed to locate the Config.ini file.')

COM_PORT = config['default']['COM_PORT']
VIDEO_INDEX = int(config['default']['VIDEO_INDEX'])
BOSS = config['default']['BOSS'].lower().replace(' ', '-')
PATH_INDEX = int(config['advanced']['BOSS_INDEX'])
pytesseract.pytesseract.tesseract_cmd = config['default']['TESSERACT_PATH']
ENABLE_DEBUG_LOGS = config['advanced']['ENABLE_DEBUG_LOGS'].lower() == 'true'

# Set the log name
LOG_NAME = ''.join(
        (BOSS, '_', datetime.now().strftime('%Y-%m-%d %H-%M-%S')))


def initialize(ctrlr) -> str:
    """Placeholder. Immediately enter the join stage."""
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
    for __ in range(PATH_INDEX):
        ctrlr.push_button(b'v', 1)

    ctrlr.push_buttons(
        (b'a', 1.5), (b'a', 1), (b'a', 1.5), (b'a', 4), (b'v', 1), (b'a', 3)
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
        score = ((rental_weight * run.rental_scores[name_id] + boss_weight
                  * run.boss_matchups[name_id][ctrlr.boss])
                 / (rental_weight + boss_weight)
                 )
        pokemon_scores.append(score)
        ctrlr.log(f'Score for {name_id}: {score:.2f}', 'DEBUG')
    selection_index = pokemon_scores.index(max(pokemon_scores))
    for __ in range(selection_index):
        ctrlr.push_button(b'v', 1)
    run.pokemon = pokemon_list[selection_index]
    ctrlr.push_button(b'a', 25)

    # DEBUG: take some screenshots of the path
    if ctrlr.enable_debug_logs:
        # ctrlr.display_results(screenshot=True)
        ctrlr.push_button(b'8', 3.5, 3)
        # ctrlr.display_results(screenshot=True)
    ctrlr.log('Finished joining.', 'DEBUG')
    return 'path'


def path(ctrlr) -> str:
    """Choose a path to follow."""
    ctrlr.log('Choosing a path to follow.', 'DEBUG')
    # TODO: implement intelligent path selection
    ctrlr.push_buttons((b'a', 4))
    ctrlr.log('Finished choosing a path.', 'DEBUG')
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
        text = ctrlr.read_text(
            ctrlr.get_frame(), ((0, 0.6), (1, 1)), invert=True)
        if re.search(ctrlr.phrases['FIGHT'], text):
            # Battle has started and the move selection screen is up
            return 'battle'
        elif re.search(ctrlr.phrases['BACKPACKER'], text):
            # Backpacker encountered so choose an item
            return 'backpacker'
        elif re.search(ctrlr.phrases['SCIENTIST'], text):
            # Scientist appeared to deal with that
            return 'scientist'
        elif re.search(ctrlr.phrases['PATH'], text):
            # Fork in the path appeared to choose where to go
            return 'path'


def battle(ctrlr) -> str:
    """Choose moves during a battle and detect whether the battle has ended."""
    run = ctrlr.current_run
    ctrlr.log(f'Battle {run.num_caught+1} starting.')
    # Loop continuously until an event that ends the battle is detected.
    # The battle ends either in victory (signalled by the catch screen)
    # or in defeat (signalled by "X was blown out of the den!").
    #
    # This function returns directly when those conditions are found.
    while True:
        # Read text from the bottom section of the screen.
        text = ctrlr.read_text(
            ctrlr.get_frame(), ((0, 0.6), (1, 1)), invert=True)

        # Check the text for key phrases that inform the bot what to do next.
        if re.search(ctrlr.phrases['CATCH'], text):
            ctrlr.log('Battle finished.', 'DEBUG')
            run.reset_stage()
            return 'catch'
        if re.search(ctrlr.phrases['FAINT'], text):
            run.lives -= 1
            ctrlr.log(f'Pokemon fainted. {run.lives} lives remaining.')
            ctrlr.push_button(None, 4)
        elif ctrlr.check_defeated():
            ctrlr.log('You lose and the battle is finished.')
            run.lives -= 1
            if run.lives != 0:
                ctrlr.log('The lives counter was not 0.', 'WARNING')
                run.lives = 0
            run.reset_stage()
            ctrlr.push_button(None, 7)
            return 'select_pokemon'  # Go to quit sequence
        if re.search(ctrlr.phrases['CHEER'], text):
            ctrlr.log('Cheering for your teammates.', 'DEBUG')
            if run.pokemon.dynamax:
                run.pokemon.dynamax = False
                run.move_index = 0
                run.dmax_timer = 0
            ctrlr.push_buttons((b'a', 1.5), (b'b', 1))
        elif re.search(ctrlr.phrases['FIGHT'], text):
            # If we got the pokemon from the scientist, we don't know what
            # our current pokemon is, so check it first.
            if run.pokemon is None:
                ctrlr.push_buttons((b'y', 1), (b'a', 1))
                run.pokemon = ctrlr.read_selectable_pokemon('battle')[0]
                ctrlr.push_buttons((b'b', 1), (b'b', 1.5), (b'b', 2))
                ctrlr.log(
                    f'Received {run.pokemon.name_id} from the scientist.')

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
                    ctrlr.push_buttons((b'y', 1), (b'a', 1), (b'l', 3))
                    run.opponent = ctrlr.read_selectable_pokemon('battle')[0]
                    ctrlr.push_buttons((b'b', 1), (b'b', 1.5), (b'b', 2))

                # If our Pokemon is Ditto, transform it into the boss (or vice
                # versa).
                if run.pokemon.name_id == 'ditto':
                    run.pokemon = automaxlair.matchup_scoring.transform_ditto(
                        run.pokemon, run.opponent)
                elif run.opponent.name_id == 'ditto':
                    ctrlr.opponent = (
                        automaxlair.matchup_scoring.transform_ditto(
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
            ctrlr.push_buttons((b'b', 2), (b'a', 2))

            # Then, check whether Dynamax is available.
            # Note that a dmax_timer value of -1 indicates that the player's
            # Pokemon has not Dynamaxed yet.
            # If no Pokemon has Dynamaxed yet, check_dynamax_available visually
            # detects if the player can Dynamax by observing the icon.
            run.dynamax_available = (
                run.dmax_timer == -1 and ctrlr.check_dynamax_available()
            )
            # Choose the best move to use against the boss
            # TODO: use the actual teammates instead of the average of all
            # rental Pokemon.
            best_move_index, __, best_move_score = (
                automaxlair.matchup_scoring.select_best_move(
                    run.pokemon, run.opponent, teammates=run.rental_pokemon)
            )
            if run.dynamax_available:
                default_score = best_move_score
                run.pokemon.dynamax = True  # Temporary
                best_max_move_index, __, best_dmax_move_score = (
                    automaxlair.matchup_scoring.select_best_move(
                        run.pokemon, run.opponent, run.rental_pokemon)
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
                ctrlr.push_button(b'v', 1)
                run.move_index = (run.move_index + 1) % 4
            ctrlr.push_buttons(
                (b'a', 1), (b'a', 1), (b'a', 1), (b'v', 1), (b'a', 0.5),
                (b'b', 0.5), (b'^', 0.5), (b'b', 0.5)
            )
            run.pokemon.PP[run.move_index] -= (
                1 if run.opponent.ability_name_id != 'pressure' else 2
            )
        else:
            # Press B which can speed up dialogue
            ctrlr.push_button(b'b', 0.005)


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
        ctrlr.push_buttons((b'v', 2), (b'a', 30))
        ctrlr.log('Congratulations!')
        return 'select_pokemon'

    # Catch the boss in almost all cases.
    ctrlr.log(f'Catching boss #{run.num_caught + 1}.')
    # Start by navigating to the ball selection screen
    ctrlr.push_button(b'a', 2)
    # then navigate to the ball specified in the config file
    while (ctrlr.get_target_ball().lower() != 'default'
           and ctrlr.get_target_ball() not in ctrlr.check_ball()
           ):
        ctrlr.push_button(b'<', 2)
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
        # Consider the amount of remaining minibosses when scoring each rental
        # Pokemon, at the start of the run, there are 3 - num_caught minibosses
        # and 1 final boss. We weigh the boss more heavily because it is more
        # difficult than the other bosses.
        rental_weight = 3 - run.num_caught
        boss_weight = 2
        # Calculate scores for the new and existing Pokemon.
        # TODO: actually read the current Pokemon's health so the bot can
        # decide to switch if it's low.
        score = (
            (rental_weight * run.rental_scores[pokemon.name_id] + boss_weight
             * run.boss_matchups[pokemon.name_id][ctrlr.boss])
            / (rental_weight + boss_weight)
        )
        existing_score = run.HP * ((
            rental_weight * run.rental_scores[run.pokemon.name_id]
            + boss_weight * automaxlair.matchup_scoring.evaluate_matchup(
                run.pokemon, run.boss_pokemon[ctrlr.boss], run.rental_pokemon))
            / (rental_weight + boss_weight)
        )
        ctrlr.log(f'Score for {pokemon.name_id}: {score:.2f}', 'DEBUG')
        ctrlr.log(
            f'Score for {run.pokemon.name_id}: {existing_score:.2f}', 'DEBUG'
        )

        run.caught_pokemon.append(pokemon.name_id)

        # Compare the scores for the two options and choose the best one.
        if score > existing_score:
            # Choose to swap your existing Pokemon for the new Pokemon.
            run.pokemon = pokemon
            ctrlr.push_button(b'a', 3)
            ctrlr.log(f'Decided to swap for {run.pokemon.name_id}.')
        else:
            ctrlr.push_button(b'b', 3)
            ctrlr.log(f'Decided to keep going with {run.pokemon.name_id}.')

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
    ctrlr.push_button(None, 5)

    ctrlr.log("Reading the backpacker's items.")

    items = []
    items.append(
        ctrlr.read_text(
            ctrlr.get_frame(), ctrlr.item_rect_1, threshold=False, invert=True,
            segmentation_mode='--psm 7').strip()
    )
    items.append(
        ctrlr.read_text(
            ctrlr.get_frame(), ctrlr.item_rect_2, threshold=False,
            segmentation_mode='--psm 7').strip()
    )
    items.append(
        ctrlr.read_text(
            ctrlr.get_frame(), ctrlr.item_rect_3, threshold=False,
            segmentation_mode='--psm 7').strip()
    )
    items.append(
        ctrlr.read_text(
            ctrlr.get_frame(), ctrlr.item_rect_4, threshold=False,
            segmentation_mode='--psm 7').strip()
    )
    items.append(
        ctrlr.read_text(
            ctrlr.get_frame(), ctrlr.item_rect_5, threshold=False,
            segmentation_mode='--psm 7').strip()
    )
    for item in items:
        ctrlr.log(f'Detected item: {item}', 'DEBUG')

    ctrlr.push_button(b'a', 5)

    ctrlr.log('Finished choosing an item.', 'DEBUG')
    return 'detect'


def scientist(ctrlr) -> str:
    """Take (or not) a Pokemon from the scientist."""
    run = ctrlr.current_run

    ctrlr.log('Scientist encountered.', 'DEBUG')

    if run.pokemon is not None:
        # Consider the amount of remaining minibosses when scoring each rental
        # Pokemon, at the start of the run, there are 3 - num_caught minibosses
        # and 1 final boss. We weigh the boss more heavily because it is more
        # difficult than the other bosses.
        rental_weight = 3 - run.num_caught
        boss_weight = 2

        # Calculate scores for an average and existing Pokemon.
        pokemon_scores = []
        for pokemon in run.rental_pokemon:
            score = ((rental_weight * run.rental_scores[pokemon] + boss_weight
                      * run.boss_matchups[pokemon][ctrlr.boss])
                     / (rental_weight + boss_weight)
                     )
            pokemon_scores.append(score)
        average_score = sum(pokemon_scores) / len(pokemon_scores)

        # TODO: actually read the current Pokemon's health so the bot can
        # decide to switch if it's low.
        existing_score = run.HP * ((
            rental_weight * run.rental_scores[run.pokemon.name_id]
            + boss_weight * automaxlair.matchup_scoring.evaluate_matchup(
                run.pokemon, run.boss_pokemon[ctrlr.boss], run.rental_pokemon))
            / (rental_weight + boss_weight)
        )
        ctrlr.log(f'Score for average pokemon: {average_score:.2f}', 'DEBUG')
        ctrlr.log(
            f'Score for {run.pokemon.name_id}: {existing_score:.2f}', 'DEBUG')

    # If current pokemon is None, it means we just already talked to scientist
    # Also it means we took the pokemon from scientist.
    # So let's try to pick it up again
    if run.pokemon is None or average_score > existing_score:
        ctrlr.push_buttons((None, 3), (b'a', 1))
        run.pokemon = None
        ctrlr.log('Took a Pokemon from the scientist.')
    else:
        ctrlr.push_buttons((None, 3), (b'b', 1))
        ctrlr.log(f'Decided to keep going with {run.pokemon.name_id}')
    return 'detect'


def select_pokemon(ctrlr) -> str:
    """Check Pokemon caught during the run and keep one if it's shiny.

    Note that this function returns 'done', causing the program to quit, if a
    shiny legendary Pokemon is found.
    """

    run = ctrlr.current_run
    # If the bot lost against the first boss, skip the checking process since
    # there are no Pokemon to check.
    if run.num_caught == 0:
        ctrlr.log('No Pokemon caught.')
        ctrlr.push_buttons((None, 10), (b'b', 1))
        ctrlr.runs += 1
        ctrlr.reset_run()
        ctrlr.record_ore_reward()
        ctrlr.log('Preparing for another run.')
        # No Pokemon to review, so go back to the beginning.
        # Note that the "keep path" mode is meant to be used on a good path, so
        # although the path would be lost that situation should never arise.
        return 'join'
    # "find path" mode quits if the run is successful.
    elif run.num_caught == 4 and ctrlr.mode == 'find path':
        ctrlr.log(f'This path won with {run.lives} lives remaining.')
        return 'done'

    # Otherwise, navigate to the summary screen of the last Pokemon caught (the
    # legendary if the run was successful)
    ctrlr.log('Checking the haul from this run.', 'DEBUG')
    ctrlr.push_buttons((b'^', 1), (b'a', 1), (b'v', 1), (b'a', 3))

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
            return 'done'  # End whenever a matching stats legendary is found

        ctrlr.push_button(b'<', 1)

    for i in range(run.num_caught):
        # First check if we need to reset immediately.
        # Note that "keep path" mode resets always unless a shiny legendary.
        # is found, and "ball saver" resets if a non-shiny legendary was
        # caught.
        if (
            (ctrlr.mode == 'keep path' and (run.num_caught < 4 or i > 0))
            or (ctrlr.mode == 'ball saver' and run.num_caught == 4 and i > 0)
        ):
            if ctrlr.mode == 'ball saver' or ctrlr.check_sufficient_ore(2):
                reset_game = True
                break
            else:
                return 'done'  # End if there isn't enough ore to reset.
        elif ctrlr.check_shiny():
            ctrlr.log('******************************')
            ctrlr.log('*********Shiny found!*********')
            ctrlr.log('******************************')
            ctrlr.log(
                f'Shiny {run.caught_pokemon[run.num_caught - 1 - i]} will be '
                'kept.'
            )
            ctrlr.caught_shinies.append(
                run.caught_pokemon[run.num_caught - 1 - i]
            )
            ctrlr.shinies_found += 1
            ctrlr.display_results(screenshot=True)
            ctrlr.push_buttons((b'p', 1), (b'b', 3), (b'p', 1))
            if run.num_caught == 4 and i == 0:
                return 'done'  # End whenever a shiny legendary is found
            else:
                take_pokemon = True
                break
        elif i < run.num_caught - 1:
            ctrlr.push_button(b'^', 3)

    if (
        not take_pokemon and ctrlr.mode == (
            'strong boss' and run.num_caught == 4)
        and ctrlr.check_sufficient_ore(1)
    ):
        reset_game = True

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
    ctrlr.reset_run()

    # Start another run if there are sufficient Poke balls to do so.
    if ctrlr.check_sufficient_balls():
        ctrlr.log('Preparing for another run.')
        return 'join'
    else:
        ctrlr.log('Out of balls. Quitting.')
        return 'done'


def button_control_task(ctrlr, actions) -> None:
    """Loop called by a thread which handles the main button detecting and
    detection aspects of the bot.
    """

    while ctrlr.stage != 'done':
        # Note that this task holds the lock by default but drops it while
        # waiting for Tesseract to respond or while delaying after a button
        # push.
        with ctrlr.lock:
            ctrlr.stage = actions[ctrlr.stage](ctrlr)


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

    # Configure the console, which will print logged information.
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG if ENABLE_DEBUG_LOGS else logging.INFO)
    console.setFormatter(formatter)

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
