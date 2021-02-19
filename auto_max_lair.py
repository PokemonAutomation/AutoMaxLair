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
import threading
import time
from datetime import datetime

import cv2
import pytesseract
import serial

#import automaxlair

#from automaxlair import matchup_scoring, da_controller, pokemon_classes
import automaxlair

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
log_name = ''.join(
        (BOSS, '_', datetime.now().strftime('%Y-%m-%d %H-%M-%S')))


def initialize(c) -> str:
    """Placeholder. Immediately enter the join stage."""
    return 'join'

def join(c) -> str:
    """Join a Dynamax Adventure and choose a Pokemon."""
    # Start a new Dynamax Adventure.
    #
    # First, start a new run by talking to the scientist in the Max Lair.
    c.log(f'Run #{c.runs + 1} started!')
    c.push_buttons(
        (b'b', 2), (b'a', 1), (b'a', 1.5), (b'a', 1.5), (b'a', 1.5), (b'b', 1)
    )

    # select the right path
    for __ in range(PATH_INDEX):
        c.push_button(b'v', 1)

    c.push_buttons(
        (b'a', 1.5), (b'a', 1), (b'a', 1.5), (b'a', 4), (b'v', 1), (b'a', 3)
    )

    # Next, read what rental Pokemon are available to choose.
    # Note that pokemon_list contains preconfigured Pokemon objects with types,
    # abilities, stats, moves, et cetera.
    pokemon_list = c.read_selectable_pokemon('join')
    pokemon_scores = []

    # Then, assign a score to each of the Pokemon based on how it is estimated
    # to perform against the minibosses (other rental Pokemon) and the final
    # boss.
    for pokemon in pokemon_list:
        name_id = pokemon.name_id
        # Consider the amount of remaining minibosses when scoring each rental
        # Pokemon, at the start of the run, there are 3 minibosses and 1 final
        # boss. We weigh the boss more heavily because it is more difficult than
        # the other bosses.
        rental_weight = 3
        boss_weight = 2
        score = ((rental_weight * c.current_run.rental_scores[name_id] + boss_weight
                  * c.current_run.boss_matchups[name_id][c.boss])
                 / (rental_weight + boss_weight)
                 )
        pokemon_scores.append(score)
        c.log(f'Score for {name_id}: {score:.2f}', 'DEBUG')
    selection_index = pokemon_scores.index(max(pokemon_scores))
    for __ in range(selection_index):
        c.push_button(b'v', 1)
    c.current_run.pokemon = pokemon_list[selection_index]
    c.push_button(b'a', 25)

    # DEBUG: take some screenshots of the path
    if c.enable_debug_logs:
        # c.display_results(screenshot=True)
        c.push_button(b'8', 3.5, 3)
        # c.display_results(screenshot=True)
    c.log('Finished joining.', 'DEBUG')
    return 'path'


def path(c) -> str:
    """Choose a path to follow."""
    c.log('Choosing a path to follow.', 'DEBUG')
    # TODO: implement intelligent path selection
    c.push_buttons((b'a', 4))
    c.log('Finished choosing a path.', 'DEBUG')
    return 'detect'


def detect(c) -> str:
    """Detect whether the chosen path has led to a battle, scientist,
    backpacker, or fork in the path.
    """

    c.log('Detecting where the path led.', 'DEBUG')
    # Loop continually until an event is detected.
    # Relevant events include a battle starting, a backpacker encountered,
    # a scientist encountered, or a fork in the path.
    #
    # This function returns directly when those conditions are found.
    while True:
        text = c.read_text(
            c.get_frame(), ((0, 0.6), (1, 1)), invert=True)
        if re.search(c.phrases['FIGHT'], text):
            # Battle has started and the move selection screen is up
            return 'battle'
        elif re.search(c.phrases['BACKPACKER'], text):
            # Backpacker encountered so choose an item
            return 'backpacker'
        elif re.search(c.phrases['SCIENTIST'], text):
            # Scientist appeared to deal with that
            return 'scientist'
        elif re.search(c.phrases['PATH'], text):
            # Fork in the path appeared to choose where to go
            return 'path'


def battle(c) -> str:
    """Choose moves during a battle and detect whether the battle has ended."""
    r = c.current_run
    c.log(f'Battle {c.current_run.num_caught+1} starting.')
    # Loop continuously until an event that ends the battle is detected.
    # The battle ends either in victory (signalled by the catch screen)
    # or in defeat (signalled by "X was blown out of the den!").
    #
    # This function returns directly when those conditions are found.
    while True:
        # Read text from the bottom section of the screen.
        text = c.read_text(
            c.get_frame(), ((0, 0.6), (1, 1)), invert=True)

        # Check the text for key phrases that inform the bot what to do next.
        if re.search(c.phrases['CATCH'], text):
            c.log('Battle finished.', 'DEBUG')
            c.current_run.reset_stage()
            return 'catch'
        elif re.search(c.phrases['FAINT'], text):
            c.current_run.lives -= 1
            c.log(f'Pokemon fainted. {c.current_run.lives} lives remaining.')
            c.push_button(None, 4)
        elif c.check_defeated():
            c.log('You lose and the battle is finished.')
            c.current_run.lives -= 1
            if c.current_run.lives != 0:
                c.log('The lives counter was not 0.', 'WARNING')
                c.current_run.lives = 0
            c.current_run.reset_stage()
            c.push_button(None, 7)
            return 'select_pokemon'  # Go to quit sequence
        elif re.search(c.phrases['CHEER'], text):
            c.log('Cheering for your teammates.', 'DEBUG')
            if c.current_run.pokemon.dynamax:
                c.current_run.pokemon.dynamax = False
                c.current_run.move_index = 0
                c.current_run.dmax_timer = 0
            c.push_buttons((b'a', 1.5), (b'b', 1))
        elif re.search(c.phrases['FIGHT'], text):
            # If we got the pokemon from the scientist, we don't know what
            # our current pokemon is, so check it first.
            if c.current_run.pokemon is None:
                c.push_buttons((b'y', 1), (b'a', 1))
                c.current_run.pokemon = c.read_selectable_pokemon('battle')[0]
                c.push_buttons((b'b', 1), (b'b', 1.5), (b'b', 2))
                c.log(
                    f'Received {c.current_run.pokemon.name_id} from the scientist.')

            # Before the bot makes a decision, it needs to know what the boss
            # is.
            if c.current_run.opponent is None:
                # If we have defeated three oppoenents already we know the
                # opponent is the boss Pokemon.
                if c.current_run.num_caught == 3:
                    c.current_run.opponent = c.current_run.boss_pokemon[BOSS]

                # Otherwise, we identify the boss using its name and types.
                else:
                    #
                    c.push_buttons((b'y', 1), (b'a', 1), (b'l', 3))
                    c.current_run.opponent = c.read_selectable_pokemon('battle')[0]
                    c.push_buttons((b'b', 1), (b'b', 1.5), (b'b', 2))

                # If our Pokemon is Ditto, transform it into the boss (or vice
                # versa).
                if c.current_run.pokemon.name_id == 'ditto':
                    c.current_run.pokemon = automaxlair.matchup_scoring.transform_ditto(
                        c.current_run.pokemon, c.current_run.opponent
                    )
                elif c.current_run.opponent.name_id == 'ditto':
                    c.opponent = automaxlair.matchup_scoring.transform_ditto(
                        c.current_run.opponent, c.current_run.pokemon
                    )

            # Handle the Dynamax timer
            # The timer starts at 3 and decreases by 1 after each turn of
            # Dynamax.
            # A value of -1 indicates a pre-dynamax state (i.e., someone can
            # Dynamax).
            # A value of 0 indicates Dynamax has ended and nobody can Dynamax
            # for the remainder of the battle.
            if c.current_run.dmax_timer == 1:
                c.current_run.dmax_timer = 0
                c.current_run.move_index = 0
                c.current_run.pokemon.dynamax = False
            elif c.current_run.dmax_timer > 1:
                c.current_run.dmax_timer -= 1

            # Navigate to the move selection screen.
            c.push_buttons((b'b', 2), (b'a', 2))

            # Then, check whether Dynamax is available.
            # Note that a dmax_timer value of -1 indicates that the player's
            # Pokemon has not Dynamaxed yet.
            # If no Pokemon has Dynamaxed yet, check_dynamax_available visually
            # detects if the player can Dynamax by observing the icon.
            c.current_run.dynamax_available = (
                c.current_run.dmax_timer == -1 and c.check_dynamax_available()
            )
            # Choose the best move to use against the boss
            # TODO: use the actual teammates instead of the average of all
            # rental Pokemon.
            best_move_index, __, best_move_score = (
                automaxlair.matchup_scoring.select_best_move(c.current_run.pokemon,
                                                 c.current_run.opponent, teammates=c.current_run.rental_pokemon)
            )
            if c.current_run.dynamax_available:
                default_score = best_move_score
                c.current_run.pokemon.dynamax = True  # Temporary
                best_max_move_index, __, best_dmax_move_score = (
                    automaxlair.matchup_scoring.select_best_move(
                        c.current_run.pokemon, c.current_run.opponent, c.current_run.rental_pokemon)
                )
                if best_dmax_move_score > default_score:
                    best_move_index = best_max_move_index
                else:
                    # Choose not to Dynamax this time by making the following
                    # code think that it isn't available.
                    c.current_run.dynamax_available = False
                c.current_run.pokemon.dynamax = False  # Revert previous temporary change

            # Navigate to the correct move and use it.
            # Note that c.dynamax_available is set to false if dynamax is
            # available but not optimal.
            if c.current_run.dynamax_available:
                # Dynamax and then choose a move as usual
                c.push_buttons((b'<', 1), (b'a', 1))
                c.current_run.dmax_timer = 3
                c.current_run.pokemon.dynamax = True
                c.current_run.dynamax_available = False
            move = (
                c.current_run.pokemon.max_moves[best_move_index] if c.current_run.pokemon.dynamax
                else c.current_run.pokemon.moves[best_move_index]
            )
            c.log(
                f'Best move against {c.current_run.opponent.name_id}: {move.name_id} '
                f'(index {best_move_index})', 'DEBUG'
            )
            c.current_run.move_index %= 4  # Loop index back to zero if it exceeds 3
            for __ in range((best_move_index - c.current_run.move_index + 4) % 4):
                c.push_button(b'v', 1)
                c.current_run.move_index = (c.current_run.move_index + 1) % 4
            c.push_buttons(
                (b'a', 1), (b'a', 1), (b'a', 1), (b'v', 1), (b'a', 0.5),
                (b'b', 0.5), (b'^', 0.5), (b'b', 0.5)
            )
            c.current_run.pokemon.PP[c.current_run.move_index] -= (
                1 if c.current_run.opponent.ability_name_id != 'pressure' else 2
            )
        else:
            # Press B which can speed up dialogue
            c.push_button(b'b', 0.005)


def catch(c) -> str:
    """Catch each boss after defeating it."""

    # Check if we need to skip catching a the final boss.
    # This scenario is used by Ball Saver mode when it can't afford to reset
    # the game.
    if (
        c.current_run.num_caught == 3 and c.mode == 'ball saver'
        and not c.check_sufficient_ore(1)
    ):
        c.log('Finishing the run without wasting a ball on the boss.')
        c.push_buttons((b'v', 2), (b'a', 30))
        c.log('Congratulations!')
        return 'select_pokemon'

    # Catch the boss in almost all cases.
    c.log(f'Catching boss #{c.current_run.num_caught + 1}.')
    # Start by navigating to the ball selection screen
    c.push_button(b'a', 2)
    # then navigate to the ball specified in the config file
    while (c.get_target_ball().lower() != 'default'
           and c.get_target_ball() not in c.check_ball()
           ):
        c.push_button(b'<', 2)
    c.push_button(b'a', 30)
    c.record_ball_use()

    # If the caught Pokemon was not the final boss, check out the Pokemon and
    # decide whether to keep it.
    if c.current_run.num_caught < 4:
        # Note that read_selectable_pokemon returns a list of preconfigured
        # Pokemon objects with types, abilities, stats, moves, et cetera.
        #
        # In this stage the list contains only 1 item.
        pokemon = c.read_selectable_pokemon('catch')[0]
        # Consider the amount of remaining minibosses when scoring each rental
        # Pokemon, at the start of the run, there are 3 - num_caught minibosses
        # and 1 final boss. We weigh the boss more heavily because it is more
        # difficult than the other bosses.
        rental_weight = 3 - c.current_run.num_caught
        boss_weight = 2
        # Calculate scores for the new and existing Pokemon.
        # TODO: actually read the current Pokemon's health so the bot can decide
        # to switch if it's low.
        score = (
            (rental_weight * c.current_run.rental_scores[pokemon.name_id] + boss_weight
             * c.current_run.boss_matchups[pokemon.name_id][c.boss])
            / (rental_weight + boss_weight)
        )
        existing_score = c.current_run.HP * ((rental_weight
                                     * c.current_run.rental_scores[c.current_run.pokemon.name_id] + boss_weight
                                     * automaxlair.matchup_scoring.evaluate_matchup(c.current_run.pokemon,
                                                                        c.current_run.boss_pokemon[c.boss], c.current_run.rental_pokemon))
                                    / (rental_weight + boss_weight)
                                    )
        c.log(f'Score for {pokemon.name_id}: {score:.2f}', 'DEBUG')
        c.log(
            f'Score for {c.current_run.pokemon.name_id}: {existing_score:.2f}', 'DEBUG'
        )

        c.caught_pokemon.append(pokemon.name_id)

        # Compare the scores for the two options and choose the best one.
        if score > existing_score:
            # Choose to swap your existing Pokemon for the new Pokemon.
            c.current_run.pokemon = pokemon
            c.push_button(b'a', 3)
            c.log(f'Decided to swap for {c.current_run.pokemon.name_id}.')
        else:
            c.push_button(b'b', 3)
            c.log(f'Decided to keep going with {c.current_run.pokemon.name_id}.')

        # Move on to the detect stage.
        return 'detect'

    # If the final boss was the caught Pokemon, wrap up the run and check the
    # Pokemon caught along the way.
    else:
        c.current_run.caught_pokemon.append(c.boss)
        c.push_button(None, 10)
        c.log('Congratulations!')
        return 'select_pokemon'


def backpacker(c) -> str:
    """Choose an item from the backpacker."""
    c.push_button(None, 5)

    c.log("Reading the backpacker's items.")

    items = []
    items.append(c.read_text(c.get_frame(), c.item_rect_1,
                                threshold=False, invert=True, segmentation_mode='--psm 7').strip())
    items.append(c.read_text(c.get_frame(), c.item_rect_2,
                                threshold=False, segmentation_mode='--psm 7').strip())
    items.append(c.read_text(c.get_frame(), c.item_rect_3,
                                threshold=False, segmentation_mode='--psm 7').strip())
    items.append(c.read_text(c.get_frame(), c.item_rect_4,
                                threshold=False, segmentation_mode='--psm 7').strip())
    items.append(c.read_text(c.get_frame(), c.item_rect_5,
                                threshold=False, segmentation_mode='--psm 7').strip())
    for item in items:
        c.log(f'Detected item: {item}', 'DEBUG')

    c.push_button(b'a', 5)

    c.log('Finished choosing an item.', 'DEBUG')
    return 'detect'


def scientist(c) -> str:
    """Take (or not) a Pokemon from the scientist."""

    c.log('Scientist encountered.', 'DEBUG')

    if c.current_run.pokemon is not None:
        # Consider the amount of remaining minibosses when scoring each rental
        # Pokemon, at the start of the run, there are 3 - num_caught minibosses
        # and 1 final boss. We weigh the boss more heavily because it is more
        # difficult than the other bosses.
        rental_weight = 3 - c.current_run.num_caught
        boss_weight = 2

        # Calculate scores for an average and existing Pokemon.
        pokemon_scores = []
        for pokemon in c.current_run.rental_pokemon:
            score = ((rental_weight * c.current_run.rental_scores[pokemon] + boss_weight
                      * c.current_run.boss_matchups[pokemon][c.boss])
                     / (rental_weight + boss_weight)
                     )
            pokemon_scores.append(score)
        average_score = sum(pokemon_scores) / len(pokemon_scores)

        # TODO: actually read the current Pokemon's health so the bot can decide
        # to switch if it's low.
        existing_score = c.current_run.HP * ((rental_weight
                                     * c.current_run.rental_scores[c.current_run.pokemon.name_id] + boss_weight
                                     * automaxlair.matchup_scoring.evaluate_matchup(c.current_run.pokemon,
                                                                        c.current_run.boss_pokemon[c.boss], c.current_run.rental_pokemon))
                                    / (rental_weight + boss_weight)
                                    )
        c.log(f'Score for average pokemon: {average_score:.2f}', 'DEBUG')
        c.log(
            f'Score for {c.current_run.pokemon.name_id}: {existing_score:.2f}', 'DEBUG')

    # If current pokemon is None, it means we just already talked to scientist
    # Also it means we took the pokemon from scientist.
    # So let's try to pick it up again
    if c.current_run.pokemon is None or average_score > existing_score:
        c.push_buttons((None, 3), (b'a', 1))
        c.current_run.pokemon = None
        c.log('Took a Pokemon from the scientist.')
    else:
        c.push_buttons((None, 3), (b'b', 1))
        c.log(f'Decided to keep going with {c.current_run.pokemon.name_id}')
    return 'detect'


def select_pokemon(c) -> str:
    """Check Pokemon caught during the run and keep one if it's shiny.

    Note that this function returns 'done', causing the program to quit, if a
    shiny legendary Pokemon is found.
    """

    # If the bot lost against the first boss, skip the checking process since
    # there are no Pokemon to check.
    if c.current_run.num_caught == 0:
        c.log('No Pokemon caught.')
        c.push_buttons((None, 10), (b'b', 1))
        c.runs += 1
        c.reset_run()
        c.record_ore_reward()
        c.log('Preparing for another run.')
        # No Pokemon to review, so go back to the beginning.
        # Note that the "keep path" mode is meant to be used on a good path, so
        # although the path would be lost that situation should never arise.
        return 'join'
    # "find path" mode quits if the run is successful.
    elif c.current_run.num_caught == 4 and c.mode == 'find path':
        c.log(f'This path won with {c.current_run.lives} lives remaining.')
        return 'done'

    # Otherwise, navigate to the summary screen of the last Pokemon caught (the
    # legendary if the run was successful)
    c.log('Checking the haul from this run.', 'DEBUG')
    c.push_buttons((b'^', 1), (b'a', 1), (b'v', 1), (b'a', 3))

    # Check all Pokemon for shininess.
    take_pokemon = False  # Set to True if a non-legendary shiny is found.
    reset_game = False  # Set to True in some cases in non-default modes.

    if c.current_run.num_caught == 4 and (c.check_attack_stat or c.check_speed_stat):
        c.push_button(b'>', 1)
        if c.check_stats():
            c.log('******************************')
            c.log('****Matching stats found!*****')
            c.log('******************************')
            c.display_results(screenshot=True)
            return 'done'  # End whenever a matching stats legendary is found

        c.push_button(b'<', 1)

    for i in range(c.current_run.num_caught):
        # First check if we need to reset immediately.
        # Note that "keep path" mode resets always unless a shiny legendary.
        # is found, and "ball saver" resets if a non-shiny legendary was caught.
        if (
            (c.mode == 'keep path' and (c.current_run.num_caught < 4 or i > 0))
            or (c.mode == 'ball saver' and c.current_run.num_caught == 4 and i > 0)
        ):
            if c.mode == 'ball saver' or c.check_sufficient_ore(2):
                reset_game = True
                break
            else:
                return 'done'  # End if there isn't enough ore to reset.
        elif c.check_shiny():
            c.log('******************************')
            c.log('*********Shiny found!*********')
            c.log('******************************')
            c.log(
                f'Shiny {c.current_run.caught_pokemon[c.current_run.num_caught - 1 - i]} will be '
                'kept.'
            )
            c.caught_shinies.append(
                c.current_run.caught_pokemon[c.current_run.num_caught - 1 - i]
            )
            c.shinies_found += 1
            c.display_results(screenshot=True)
            c.push_buttons((b'p', 1), (b'b', 3), (b'p', 1))
            if c.current_run.num_caught == 4 and i == 0:
                return 'done'  # End whenever a shiny legendary is found
            else:
                take_pokemon = True
                break
        elif i < c.current_run.num_caught - 1:
            c.push_button(b'^', 3)

    if (
        not take_pokemon and c.mode == 'strong boss' and c.current_run.num_caught == 4
        and c.check_sufficient_ore(1)
    ):
        reset_game = True

    # After checking all the Pokemon, wrap up the run (including taking a
    # Pokemon or resetting the game, where appropriate).
    if not reset_game:
        if take_pokemon:
            c.push_buttons(
                (b'a', 1), (b'a', 1), (b'a', 1), (b'a', 1.5),
                (b'a', 3), (b'b', 2), (b'b', 10), (b'a', 2)
            )
        else:
            c.push_buttons((b'b', 3), (b'b', 1))
        c.record_ore_reward()
    else:
        c.log('Resetting the game to preserve a winning seed.')
        c.record_game_reset()
        # The original button sequence was added with the help of users fawress
        # and Miguel90 on the Pokemon Automation Discord.
        c.push_buttons((b'h', 2), (b'x', 2))

    # The button press sequences differ depending on how many Pokemon were
    # defeated and are further modified by the language.
    # Therefore, press A until the starting dialogue appears, then back out.
    while c.phrases['START_PHRASE'] not in c.read_text(
        c.get_frame(),
        ((0, 0.6), (1, 1)), threshold=False
    ):
        c.push_button(b'a', 1.5)
    c.push_buttons((b'b', 1.5), (b'b', 1.5))

    # Update statistics and reset stored information about the complete run.
    c.wins += 1 if c.current_run.lives != 0 else 0
    c.runs += 1
    c.reset_run()

    # Start another run if there are sufficient Poke balls to do so.
    if c.check_sufficient_balls():
        c.log('Preparing for another run.')
        return 'join'
    else:
        c.log('Out of balls. Quitting.')
        return 'done'


def button_control_task(c, actions) -> None:
    """Loop called by a thread which handles the main button detecting and
    detection aspects of the bot.
    """

    while c.stage != 'done':
        # Note that this task holds the lock by default but drops it while
        # waiting for Tesseract to respond or while delaying after a button
        # push.
        with c.lock:
            c.stage = actions[c.stage](c)


def main(log_name):
    """Main loop. Runs until a shiny is found or the user manually quits by
    pressing 'Q'.
    """

    # Map stages to the appropriate function to execute when in each stage
    actions = {'initialize': initialize, 'join': join, 'path': path, 'detect': detect, 'battle': battle,
               'catch': catch, 'backpacker': backpacker, 'scientist': scientist,
               'select_pokemon': select_pokemon
               }

    controller = automaxlair.da_controller.DAController(config, log_name, actions)
    
    # Start the event loop, 
    controller.event_loop()


def exception_handler(exception_type, exception_value, exception_traceback):
    """Exception hook to ensure exceptions get logged."""
    logger = logging.getLogger(log_name)
    logger.error(
        'Exception occurred:',
        exc_info=(exception_type, exception_value, exception_traceback)
    )


if __name__ == '__main__':
    # Set up the logger
    
    # Configure the logger.
    logger = logging.getLogger(log_name)
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
        filename=os.path.join('logs', log_name + '.log'),
        encoding="UTF-8"
    )
    fileHandler.setFormatter(formatter)
    fileHandler.setLevel(logging.DEBUG if ENABLE_DEBUG_LOGS else logging.INFO)

    # Add the handlers to the logger so that it will both print messages to
    # the console as well as save them to a log file.
    logger.addHandler(console)
    logger.addHandler(fileHandler)
    logger.info(f'Starting new series: {log_name}.')

    # Call main
    sys.excepthook = exception_handler
    main(log_name)

