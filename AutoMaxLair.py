#   AutoMaxLair
#       Eric Donders
#       Contributions from Miguel Tavera, Discord user fawress, 
#           Discord user pifopi, and Discord user denvoros
#       Created 2020-11-20

import configparser
import logging
import logging.handlers
import os
import pickle
import re
import threading
import time
from copy import copy, deepcopy
from datetime import datetime

import cv2
import enchant
import numpy
import pytesseract
import serial

from automaxlair import MaxLairInstance, matchup_scoring

# Load configuration from config file
config = configparser.ConfigParser()

# Configparser doesn't complain if it can't find the config file,
# so manually raise an error if the file was not read.
if not config.read('Config.ini', 'utf8'):
    raise FileNotFoundError('Failed to locate the Config.ini file.')
    

COM_PORT = config['default']['COM_PORT']
VIDEO_INDEX = int(config['default']['VIDEO_INDEX'])
VIDEO_SCALE = float(config['default']['VIDEO_SCALE'])
BOSS = config['default']['BOSS'].lower().replace(' ', '-')
PATH_INDEX = int(config['default']['PATH_INDEX'])
BASE_BALL = config['default']['BASE_BALL']
BASE_BALLS = int(config['default']['BASE_BALLS'])
LEGENDARY_BALL = config['default']['LEGENDARY_BALL']
LEGENDARY_BALLS = int(config['default']['LEGENDARY_BALLS'])
MODE = config['default']['MODE'].lower()
DYNITE_ORE = int(config['default']['DYNITE_ORE'])
pytesseract.pytesseract.tesseract_cmd = config['default']['TESSERACT_PATH']

boss_pokemon_path = config['pokemon_data_paths']['Boss_Pokemon']
rental_pokemon_path = config['pokemon_data_paths']['Rental_Pokemon']
boss_matchup_LUT_path = config['pokemon_data_paths']['Boss_Matchup_LUT']
rental_matchup_LUT_path = config['pokemon_data_paths']['Rental_Matchup_LUT']
rental_pokemon_scores_path = config['pokemon_data_paths']['Rental_Pokemon_Scores']

language = config['language']['LANGUAGE']
PHRASES = config[language]

ENABLE_DEBUG_LOGS = config['default']['ENABLE_DEBUG_LOGS'] == 'True'


def join(inst) -> str:
    """Join a Dynamax Adventure and choose a Pokemon."""
    # Start a new Dynamax Adventure.
    # 
    # First, start a new run by talking to the scientist in the Max Lair.
    inst.log(f'Run #{inst.runs + 1} started!')
    inst.push_buttons(
        (b'b', 2), (b'a', 1), (b'a', 1.5), (b'a', 1.5), (b'a', 1.5), (b'b', 1)
    )

    # select the right path
    for __ in range(PATH_INDEX):
        inst.push_button(b'v', 1)

    inst.push_buttons(
        (b'a', 1.5), (b'a', 1), (b'a', 1.5), (b'a', 4), (b'v', 1), (b'a', 5)
    )

    # Next, read what rental Pokemon are available to choose.
    # Note that pokemon_list contains preconfigured Pokemon objects with types,
    # abilities, stats, moves, et cetera.
    pokemon_list = inst.read_selectable_pokemon('join')
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
        score = ((rental_weight * inst.rental_scores[name_id] + boss_weight
            * inst.boss_matchups[name_id][inst.boss])
            / (rental_weight + boss_weight)
        )
        pokemon_scores.append(score)
        inst.log(f'Score for {name_id}:\t{score:.2f}')
    selection_index = pokemon_scores.index(max(pokemon_scores))
    for __ in range(selection_index):
        inst.push_button(b'v', 1)
    inst.pokemon = pokemon_list[selection_index]
    inst.push_button(b'a',27)
    inst.log('Finished joining. Now choosing a path.')
    return 'path'


def path(inst) -> str:
    """Choose a path to follow."""
    # TODO: implement intelligent path selection
    inst.push_buttons((b'a', 4))
    print('Finished choosing a path. Now detecting where the path led.')
    return 'detect'


def detect(inst) -> str:
    """Detect whether the chosen path has led to a battle, scientist,
    backpacker, or fork in the path.
    """

    # Loop continually until an event is detected.
    # Relevant events include a battle starting, a backpacker encountered,
    # a scientist encountered, or a fork in the path.
    #
    # This function returns directly when those conditions are found.
    while True:
        text = inst.read_text(inst.get_frame(), ((0, 0.6), (1, 1)), invert=True)
        if re.search(inst.phrases['FIGHT'], text):
            # Battle has started and the move selection screen is up
            inst.log('Battle starting.')
            return 'battle'
        elif re.search(inst.phrases['BACKPACKER'], text):
            # Backpacker encountered so choose an item
            inst.log('Backpacker encountered.')
            return 'backpacker'
        elif re.search(inst.phrases['SCIENTIST'], text):
            # Scientist appeared to deal with that
            inst.log('Scientist encountered.')
            return 'scientist'
        elif re.search(inst.phrases['PATH'], text):
            # Fork in the path appeared to choose where to go
            inst.log('Choosing a path.')
            return 'path'


def battle(inst) -> str:
    """Choose moves during a battle and detect whether the battle has ended."""
    # Loop continuously until an event that ends the battle is detected.
    # The battle ends either in victory (signalled by the catch screen)
    # or in defeat (signalled by "X was blown out of the den!").
    #
    # This function returns directly when those conditions are found.
    while True:
        # Read text from the bottom section of the screen.
        text = inst.read_text(inst.get_frame(), ((0, 0.6), (1, 1)), invert=True)  
            
        # Check the text for key phrases that inform the bot what to do next.
        if re.search(inst.phrases['CATCH'], text):
            inst.log('Battle finished. Now catching the boss.')
            inst.reset_stage()
            return 'catch'
        elif re.search(inst.phrases['FAINT'], text):
            inst.log('Pokemon fainted.')
            inst.lives -= 1
            inst.push_button(None, 4)
        elif inst.check_defeated():
            inst.log('You lose and the battle is finished. Now quitting.')
            inst.lives -= 1
            inst.reset_stage()
            inst.push_button(None, 7)
            return 'select_pokemon'  # Go to quit sequence
        elif re.search(inst.phrases['CHEER'], text):
            if inst.pokemon.dynamax:
                inst.pokemon.dynamax = False
                inst.move_index = 0
                inst.dmax_timer = 0
            inst.push_buttons((b'a', 1.5), (b'b', 1))
        elif re.search(inst.phrases['FIGHT'], text):
            # If we got the pokemon from the scientist, we don't know what
            # our current pokemon is, so check it first.
            if inst.pokemon is None:
                inst.push_buttons((b'y', 1), (b'a', 1))
                inst.pokemon = inst.read_selectable_pokemon('battle')[0]
                inst.push_buttons((b'b', 1), (b'b', 1.5), (b'b', 2))
                inst.log(f'Received {inst.pokemon.name_id} from the scientist.')

            # Before the bot makes a decision, it needs to know what the boss
            # is.
            if inst.opponent is None:
                # If we have defeated three oppoenents already we know the
                # opponent is the boss Pokemon.
                if inst.num_caught == 3:
                    inst.opponent = inst.boss_pokemon[BOSS]

                # Otherwise, we identify the boss using its name and types.
                else:
                    # 
                    inst.push_buttons((b'y', 1), (b'a', 1), (b'l', 3))
                    inst.opponent = inst.read_selectable_pokemon('battle')[0]
                    inst.push_buttons((b'b', 1), (b'b', 1.5), (b'b', 2))
                
                # If our Pokemon is Ditto, transform it into the boss (or vice
                # versa).
                if inst.pokemon.name_id == 'ditto':
                    inst.pokemon = matchup_scoring.transform_ditto(
                        inst.pokemon, inst.opponent
                    )
                elif inst.opponent.name_id == 'ditto':
                    inst.opponent = matchup_scoring.transform_ditto(
                        inst.opponent, inst.pokemon
                    )

            # Handle the Dynamax timer
            # The timer starts at 3 and decreases by 1 after each turn of
            # Dynamax.
            # A value of -1 indicates a pre-dynamax state (i.e., someone can
            # Dynamax).
            # A value of 0 indicates Dynamax has ended and nobody can Dynamax
            # for the remainder of the battle.
            if inst.dmax_timer == 1:
                inst.dmax_timer = 0
                inst.move_index = 0
                inst.pokemon.dynamax = False
            elif inst.dmax_timer > 1:
                inst.dmax_timer -= 1

            # Navigate to the move selection screen.
            inst.push_buttons((b'b', 2), (b'a', 0.05), (b'a', 2))

            # Then, check whether Dynamax is available.
            # Note that a dmax_timer value of -1 indicates that the player's
            # Pokemon has not Dynamaxed yet.
            # If no Pokemon has Dynamaxed yet, check_dynamax_available visually
            # detects if the player can Dynamax by observing the icon.
            inst.dynamax_available = (
                inst.dmax_timer == -1 and inst.check_dynamax_available()
            )
            # Choose the best move to use against the boss
            # TODO: use the actual teammates instead of the average of all
            # rental Pokemon.
            best_move_index, __, best_move_score = (
                matchup_scoring.select_best_move(inst.pokemon,
                inst.opponent, teammates=inst.rental_pokemon)
            )
            if inst.dynamax_available:
                default_score = best_move_score
                inst.pokemon.dynamax = True  # Temporary
                best_max_move_index, __, best_dmax_move_score = (
                    matchup_scoring.select_best_move(
                    inst.pokemon, inst.opponent, inst.rental_pokemon)
                )
                if best_dmax_move_score > default_score:
                    best_move_index = best_max_move_index
                else:
                    # Choose not to Dynamax this time by making the following
                    # code think that it isn't available.
                    inst.dynamax_available = False
                inst.pokemon.dynamax = False  # Revert previous temporary change

            # Navigate to the correct move and use it.
            # Note that inst.dynamax_available is set to false if dynamax is
            # available but not optimal.
            if inst.dynamax_available:
                # Dynamax and then choose a move as usual
                inst.push_buttons((b'<', 1), (b'a', 1))
                inst.dmax_timer = 3
                inst.pokemon.dynamax = True
                inst.dynamax_available = False
            move = (
                inst.pokemon.max_moves[best_move_index] if inst.pokemon.dynamax
                else inst.pokemon.moves[best_move_index]
            )
            inst.log(
                f'''Best move against {inst.opponent.name_id}: {move.name_id} 
                (index {best_move_index})''', 'DEBUG'
            )
            inst.move_index %= 4  # Loop index back to zero if it exceeds 3
            for __ in range((best_move_index - inst.move_index + 4) % 4):
                inst.push_button(b'v', 1)
                inst.move_index = (inst.move_index + 1) % 4
            inst.push_buttons(
                (b'a', 1), (b'a', 1), (b'a', 1), (b'v', 1), (b'a', 0.5),
                (b'b', 0.5), (b'^', 0.5), (b'b', 0.5)
            )
            inst.pokemon.PP[inst.move_index] -= (
                1 if inst.opponent.ability_name_id != 'pressure' else 2
            )
        else:
            # Press B which can speed up dialogue
            inst.push_button(b'b', 0.005)
        

def catch(inst) -> str:
    """Catch each boss after defeating it."""
    # Start by navigating to the ball selection screen
    inst.push_button(b'a', 2)
    # then navigate to the ball specified in the config file
    while (inst.get_target_ball() != 'DEFAULT'
        and inst.get_target_ball() not in inst.check_ball()
    ):
        inst.push_button(b'<', 2)
    inst.push_button(b'a', 30)
    inst.record_ball_use()

    # If the caught Pokemon was not the final boss, check out the Pokemon and
    # decide whether to keep it.
    if inst.num_caught < 4:
        # Note that read_selectable_pokemon returns a list of preconfigured
        # Pokemon objects with types, abilities, stats, moves, et cetera.
        # 
        # In this stage the list contains only 1 item.
        pokemon = inst.read_selectable_pokemon('catch')[0]
        # Consider the amount of remaining minibosses when scoring each rental
        # Pokemon, at the start of the run, there are 3 - num_caught minibosses
        # and 1 final boss. We weigh the boss more heavily because it is more
        # difficult than the other bosses.
        rental_weight = 3 - inst.num_caught
        boss_weight = 2
        # Calculate scores for the new and existing Pokemon.
        # TODO: actually read the current Pokemon's health so the bot can decide
        # to switch if it's low.
        score = (
            (rental_weight * inst.rental_scores[pokemon.name_id] + boss_weight
            * inst.boss_matchups[pokemon.name_id][inst.boss])
            / (rental_weight+boss_weight)
        )
        existing_score = inst.HP * ((rental_weight
            * inst.rental_scores[inst.pokemon.name_id] + boss_weight
            * matchup_scoring.evaluate_matchup(inst.pokemon,
            inst.boss_pokemon[inst.boss],inst.rental_pokemon))
            / (rental_weight+boss_weight)
        )
        inst.log(f'Score for {pokemon.name_id}:\t{score:.2f}', 'DEBUG')
        inst.log(
            f'Score for {inst.pokemon.name_id}:\t{existing_score:.2f}', 'DEBUG'
        )

        inst.caught_pokemon.append(pokemon.name_id)

        # Compare the scores for the two options and choose the best one.
        if score > existing_score:
            # Choose to swap your existing Pokemon for the new Pokemon.
            inst.pokemon = pokemon
            inst.push_button(b'a', 3)
            
        else:
            inst.push_button(b'b', 3)

        # Move on to the detect stage.
        inst.log(
            f'''Decided to take {inst.pokemon.name_id}.
            Now detecting where the path led.'''
        )
        return 'detect'

    # If the final boss was the caught Pokemon, wrap up the run and check the
    # Pokemon caught along the way.
    else:
        inst.caught_pokemon.append(inst.boss)
        inst.push_button(None,10)
        inst.log('Congratulations! Checking the haul from this run.')
        return 'select_pokemon'


def backpacker(inst) -> str:
    """Choose an item from the backpacker."""
    inst.push_button(None, 4)

    inst.log("Reading the backpacker's items.")

    f = open("itemsList.txt", "a", encoding='utf8')
    items = []
    items.append(inst.read_text(inst.get_frame(), inst.item_rect_1, threshold=False, invert=True, segmentation_mode='--psm 7').strip())
    items.append(inst.read_text(inst.get_frame(), inst.item_rect_2, threshold=False, segmentation_mode='--psm 7').strip())
    items.append(inst.read_text(inst.get_frame(), inst.item_rect_3, threshold=False, segmentation_mode='--psm 7').strip())
    items.append(inst.read_text(inst.get_frame(), inst.item_rect_4, threshold=False, segmentation_mode='--psm 7').strip())
    items.append(inst.read_text(inst.get_frame(), inst.item_rect_5, threshold=False, segmentation_mode='--psm 7').strip())
    for item in items:
        f.write(f'{item}\n')
        inst.log(f'Detected item: {item}', 'DEBUG')
    f.close()

    inst.push_button(b'a', 5)

    inst.log('Finished choosing an item. Now detecting where the path led.')
    return 'detect'


def scientist(inst) -> str:
    """Take (or not) a Pokemon from the scientist."""
    # Consider the amount of remaining minibosses when scoring each rental
    # Pokemon, at the start of the run, there are 3 - num_caught minibosses
    # and 1 final boss. We weigh the boss more heavily because it is more
    # difficult than the other bosses.
    rental_weight = 3 - inst.num_caught
    boss_weight = 2

    # Calculate scores for an average and existing Pokemon.
    pokemon_scores = []
    for pokemon in inst.rental_pokemon:
        score = ((rental_weight * inst.rental_scores[pokemon] + boss_weight
            * inst.boss_matchups[pokemon][inst.boss])
            / (rental_weight+boss_weight)
        )
        pokemon_scores.append(score)
    average_score = sum(pokemon_scores) / len(pokemon_scores)

    # TODO: actually read the current Pokemon's health so the bot can decide
    # to switch if it's low.
    existing_score = inst.HP * ((rental_weight
        * inst.rental_scores[inst.pokemon.name_id] + boss_weight
        * matchup_scoring.evaluate_matchup(inst.pokemon,
        inst.boss_pokemon[inst.boss],inst.rental_pokemon))
        / (rental_weight+boss_weight)
    )
    inst.log(f'Score for average pokemon:\t{average_score:.2f}', 'DEBUG')
    inst.log(
        f'Score for {inst.pokemon.name_id}:\t{existing_score:.2f}', 'DEBUG'
    )

    if average_score > existing_score:
        inst.push_buttons((None, 3), (b'a', 5))
        inst.pokemon = None
    else:
        inst.push_buttons((None, 3), (b'b', 5))
    inst.log('Finished with the scientist. Now detecting where the path led.')
    return 'detect'


def select_pokemon(inst) -> str:
    """Check Pokemon caught during the run and keep one if it's shiny.
    
    Note that this function returns 'done', causing the program to quit, if a
    shiny legendary Pokemon is found.
    """
    # If the bot lost against the first boss, skip the checking process since
    # there are no Pokemon to check.
    if inst.num_caught == 0:
        inst.push_buttons((None, 10), (b'b', 1))
        # No Pokemon to review, so go back to the beginning.
        # Note that the "keep path" mode is meant to be used on a good path, so
        # although the path would be lost that situation should never arise.
        return 'join'

    # Otherwise, navigate to the summary screen of the last Pokemon caught (the
    # legendary if the run was successful)
    inst.push_buttons((b'^', 1), (b'a', 1), (b'v', 1), (b'a', 3))

    # Check all Pokemon for shininess
    take_pokemon = False  # Set to True if a non-legendary shiny is found
    reset_game = False  # Set to True in some cases in non-default modes
    for i in range(inst.num_caught):
        # First check if we need to reset immediately.
        # Note that "keep path" mode resets always unless a shiny legendary
        # is found, and "ball saver" resets if a non-shiny legendary was caught.
        if (
            (inst.mode == 'keep path' and (inst.num_caught < 4 or i > 0))
            or (inst.mode == 'ball saver' and inst.num_caught == 4 and i > 0)
        ):
            if inst.check_sufficient_ore(2):
                reset_game = True
                break
            else:
                return 'done'  # End if there isn't enough ore to keep resetting
        elif inst.check_shiny():
            inst.log('''******************************
                \n\nShiny found!\n\n******************************'''
            )
            inst.log(
                f'''Shiny {inst.caught_pokemon[inst.num_caught - 1 - i]} will be
                 kept.'''
            )
            inst.caught_shinies.append(
                inst.caught_pokemon[inst.num_caught - 1 - i]
            )
            inst.shinies_found += 1
            inst.display_results(screenshot=True)
            inst.push_buttons((b'p', 1), (b'b', 3), (b'p', 1))
            if inst.num_caught == 4 and i == 0:
                return 'done'  # End whenever a shiny legendary is found
            else:
                take_pokemon = True
                break
        elif i < inst.num_caught - 1:
            inst.push_button(b'^',3)
    
    if (
        not take_pokemon and inst.mode == 'strong boss' and inst.num_caught == 4
        and inst.check_sufficient_ore(1)
    ):
        reset_game = True

    # After checking all the Pokemon, wrap up the run (including taking a
    # Pokemon or resetting the game, where appropriate).     
    if not reset_game:
        if take_pokemon:
            inst.push_buttons(
                (b'a', 1), (b'a', 1), (b'a', 1), (b'a', 1.5),
                (b'a', 3), (b'b', 2), (b'b', 10), (b'a', 2)
            )
        else:
            inst.push_buttons((b'b', 3), (b'b', 1))
        inst.record_ore_reward()
    else:
        inst.log('Resetting the game to preserve a winning seed.')
        inst.record_game_reset()
        # The original button sequence was added with the help of users fawress
        # and Miguel90 on the Pokemon Automation Discord.
        inst.push_buttons((b'h', 2), (b'x', 2))

    # The button press sequences differ depending on how many Pokemon were
    # defeated and are further modified by the language.
    # Therefore, press A until the starting dialogue appears, then back out.
    while inst.phrases['START_PHRASE'] not in inst.read_text(
        inst.get_frame(),
        ((0, 0.6), (1, 1)), threshold=False
    ):
        inst.push_button(b'a', 1.5)
    inst.push_buttons((b'b', 1.5), (b'b', 1.5))
    
    # Update statistics and reset stored information about the complete run.
    inst.wins += 1 if inst.num_caught == 4 else 0
    inst.runs += 1
    inst.reset_run()

    # Start another run if there are sufficient Poke balls to do so.
    if inst.check_sufficient_balls():
        inst.log('Preparing for another run.')
        return 'join'
    else:
        inst.log('Out of balls. Quitting.')
        return 'done'

    
def button_control_task(inst, actions) -> None:
    """Loop called by a thread which handles the main button detecting and
    detection aspects of the bot.
    """

    while inst.stage != 'done':
        # Note that this task holds the lock by default but drops it while
        # waiting for Tesseract to respond or while delaying after a button
        # push.
        with inst.lock:
            inst.stage = actions[inst.stage](inst)


def main_loop():
    """Main loop. Runs until a shiny is found or the user manually quits by
    pressing 'Q'.
    """

    # Set up the logger
    log_name = ''.join((BOSS,'_',datetime.now().strftime('%Y-%m-%d %H-%M-%S')))
    # Configure the logger.
    logger = logging.getLogger(log_name)
    logger.setLevel(
        logging.DEBUG if config['default']['ENABLE_DEBUG_LOGS'] == 'True'
        else logging.INFO
    )
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s: %(message)s'
    )
    
    # Configure the console, which will print logged information.
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)

    # Configure the file handler, which will save logged information.
    fileHandler = logging.handlers.TimedRotatingFileHandler(
        filename=os.path.join('logs', log_name+'.log'),
        when='midnight',
        backupCount=30
    )
    fileHandler.setFormatter(formatter)
    fileHandler.setLevel(logging.DEBUG if ENABLE_DEBUG_LOGS else logging.INFO)

    # Add the handlers to the logger so that it will both print messages to
    # the console as well as save them to a log file.
    logger.addHandler(console)
    logger.addHandler(fileHandler)
    logger.info(f'Starting new series: {log_name}.')

    # Connect to the Teensy over a serial port
    com = serial.Serial(COM_PORT, 9600, timeout=0.05)
    logger.info(f'Attempting to connect to {com.port}.')
    while not com.is_open:
        try:
            com.open()
        except serial.SerialException:
            pass
    logger.info('Connected to the serial device successfully.')

    # Open the video capture
    logger.info('Attempting to open the video connection.')
    cap = cv2.VideoCapture(VIDEO_INDEX)
    if not cap.isOpened():
        logger.error(
            '''Failed to open the video connection. Check the config file and
            ensure no other application is using the video input.'''
        )
        com.close()
        return

    # Create a Max Lair Instance object to store information about each run
    # and the entire sequence of runs
    instance = MaxLairInstance(
        config, com, cap, threading.Lock(), threading.Event(), log_name,
        ENABLE_DEBUG_LOGS   
    )

    # Map stages to the appropriate function to execute when in each stage
    actions = {'join': join, 'path': path, 'detect': detect, 'battle': battle,
        'catch': catch, 'backpacker': backpacker, 'scientist': scientist,
        'select_pokemon': select_pokemon
    }
    

    # Start a thread that will control all the button press sequences
    button_control_thread = threading.Thread(
        target=button_control_task, args=(instance,actions,)
    )
    button_control_thread.start()
    

    
    # Start event loop which handles the display and checks for the user
    # manually quitting.
    # The loop ends when the button control thread ends naturally or when
    # signalled by the user pressing the Q key.
    while button_control_thread.is_alive():

        # Wait until the button control thread releases the lock, then use the
        # idle time to update the graphical display.
        with instance.lock:
            instance.display_results()
        
        # Add a brief delay between each frame so the button control thread has
        # some time to acquire the lock.
        time.sleep(0.01)

        # Tell the button control thread to quit if the Q key is pressed.
        if cv2.waitKey(1) & 0xFF == ord('q'):
            instance.exit_flag.set()
            # After setting the exit flag, we need to wait for the button
            # control thread to exit because it only checks the flag at the
            # start of a new button push or OCR call.
            button_control_thread.join()


    # When finished, clean up video and serial connections
    instance.display_results(log=True)
    cap.release()
    com.close()
    #cv2.destroyAllWindows()


if __name__ == '__main__':
    main_loop()
