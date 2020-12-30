#   AutoMaxLair
#       v0.5
#       Eric Donders
#       2020-12-26

import cv2, time, serial, numpy, pytesseract, pickle, enchant, configparser, threading
from datetime import datetime
from copy import copy, deepcopy
from MaxLairInstance import MaxLairInstance
from Pokemon_Data import matchup_scoring

# Load configuration from config file
config = configparser.ConfigParser()
config.read('Config.ini')

COM_PORT = config['default']['COM_PORT']
VIDEO_INDEX = int(config['default']['VIDEO_INDEX'])
BOSS = config['default']['BOSS']
BASE_BALL = config['default']['BASE_BALL']
BASE_BALLS = int(config['default']['BASE_BALLS'])
LEGENDARY_BALL = config['default']['LEGENDARY_BALL']
LEGENDARY_BALLS = int(config['default']['LEGENDARY_BALLS'])
MODE = config['default']['MODE']
DYNITE_ORE = int(config['default']['DYNITE_ORE'])
pytesseract.pytesseract.tesseract_cmd = config['default']['TESSERACT_PATH']

boss_pokemon_path = config['pokemon_data_paths']['Boss_Pokemon']
rental_pokemon_path = config['pokemon_data_paths']['Rental_Pokemon']
boss_matchup_LUT_path = config['pokemon_data_paths']['Boss_Matchup_LUT']
rental_matchup_LUT_path = config['pokemon_data_paths']['Rental_Matchup_LUT']
rental_pokemon_scores_path = config['pokemon_data_paths']['Rental_Pokemon_Scores']



def join(inst):
    """Join a Dynamax Adventure and choose a Pokemon."""
    inst.log('Run #' + str(inst.runs + 1) + ' started!')
    inst.push_buttons((b'b', 2), (b'a', 0.5), (b'a', 1), (b'a', 1.5), (b'a', 1.5), (b'a', 1.5), (b'a', 1.5), (b'a', 1), (b'a', 1.5), (b'a', 4), (b'v', 1), (b'a', 5))
    # Read Pokemon names from specified regions
    pokemon_list = inst.read_selectable_pokemon('join')
    pokemon_scores = []
    for pokemon in pokemon_list:
        # Match each name to a rental Pokemon object with preconfigured moves, stats, etc.
        name = pokemon.name
        # Score each Pokemon by its average performance against the remaining path
        rental_weight = 3
        boss_weight = 2
        score = (rental_weight * inst.rental_scores[name] + boss_weight * inst.boss_matchups[name][inst.boss]) / (
                    rental_weight + boss_weight)
        pokemon_scores.append(score)
        inst.log('Score for ' + name + ':\t%0.2f' % score)
    selection_index = pokemon_scores.index(max(pokemon_scores))
    for _ in range(selection_index):
        inst.push_buttons((b'v', 1))
    inst.pokemon = pokemon_list[selection_index]
    inst.push_buttons((b'a',27))
    inst.log('Choosing a path...')
    return 'path'


def path(inst) -> str:
    """Choose a path to follow."""
    inst.push_buttons((b'a', 4))
    print('Detecting where the path led...')
    return 'detect'


def detect(inst) -> str:
    """Detect whether the chosen path has led to a battle, scientist, backpacker, or fork in the path.
    :type inst: MaxLairInstance
    """
    text = inst.read_text(inst.get_frame(), ((0, 0.6), (1, 1)), invert=True)
    if 'Fight' in text or 'appeared' in text:
        # Battle has started and the move selection screen is up
        inst.log('Battle starting...')
        return 'battle'
    elif 'backpacker' in text:
        # Backpacker encountered so choose an item
        inst.log('Backpacker encountered...')
        return 'backpacker'
    elif 'swapping' in text:
        # Scientist appeared to deal with that
        inst.log('Scientist encountered...')
        return 'scientist'
    elif 'path' in text:
        # Fork in the path appeared to choose where to go
        inst.log('Choosing a path...')
        return 'path'
    else:
        return 'detect'  # If not finished this stage, run it again next loop


def battle(inst) -> str:
    """Choose moves during a battle and detect whether the battle has ended."""
    while True:
        text = inst.read_text(inst.get_frame(), ((0, 0.6), (1, 1)), invert=True)  # Read text from the bottom section of the screen
        
        if 'Catch' in text:
            inst.log('Catching boss...')
            inst.reset_stage()
            return 'catch'
        elif 'blown' in text:
            inst.log('You lose :(. Quitting...')
            inst.reset_stage()
            inst.push_buttons((b'0', 7))
            return 'select_pokemon'  # Go to quit sequence
        elif 'gathered around' in text:
            inst.dynamax_available = True
            inst.pokemon.dynamax = False
            inst.dmax_timer = -1
        elif 'can dynamax now' in text.lower():
            inst.dynamax_available = False
            inst.pokemon.dynamax = False
            inst.dmax_timer = -1
        elif 'Cheer On' in text:
            inst.dmax_timer = -1
            inst.dynamax_available = False
            if inst.pokemon.dynamax:
                inst.pokemon.dynamax = False
                inst.move_index = 0
            inst.push_buttons((b'a', 1))
        elif 'Fight' in text:
            # Detect or infer opponent
            if inst.opponent is None:
                if inst.num_caught == 3:
                    inst.opponent = inst.boss_pokemon[BOSS]
                else:
                    inst.push_buttons((b'y', 1), (b'a', 1), (b'l', 1))
                    inst.opponent = inst.read_selectable_pokemon('battle')[0]
                    inst.push_buttons((b'0', 1), (b'b', 1.5), (b'b', 1))
                if inst.pokemon.name == 'Ditto':
                    inst.pokemon = copy(inst.opponent)
                    inst.pokemon.name = 'Ditto'
                    inst.pokemon.PP = [5,5,5,5]
            # Handle the Dynamax timer
            if inst.dmax_timer == 0:
                inst.dmax_timer = -1
                inst.move_index = 0
                inst.pokemon.dynamax = False
            elif inst.dmax_timer > 0:
                inst.dmax_timer -= 1
            # Choose the best move to use, and whether or not to Dynamax (if it's available)
            best_move_index = matchup_scoring.select_best_move(inst.pokemon, inst.opponent, inst.rental_pokemon)
            if inst.dynamax_available:
                default_score = matchup_scoring.calculate_move_score(inst.pokemon, best_move_index, inst.opponent,
                                                                    teammates=inst.rental_pokemon)
                inst.pokemon.dynamax = True  # Temporary
                best_max_move_index = matchup_scoring.select_best_move(inst.pokemon, inst.opponent, inst.rental_pokemon)
                if matchup_scoring.calculate_move_score(inst.pokemon, best_max_move_index, inst.opponent,
                                                        teammates=inst.rental_pokemon) > default_score:
                    best_move_index = best_max_move_index
                else:
                    inst.dynamax_available = False  # Choose not to Dynamax this time
                inst.pokemon.dynamax = False  # Revert previous temporary change
            # Navigate to the correct move
            inst.push_buttons((b'0', 1), (b'a', 1))
            if inst.dynamax_available:
                # Dynamax and then choose a move as usual
                inst.push_buttons((b'<', 1), (b'a', 1))
                inst.dmax_timer = 2
                inst.pokemon.dynamax = True
                inst.dynamax_available = False
            move = inst.pokemon.max_moves[best_move_index] if inst.pokemon.dynamax else inst.pokemon.moves[best_move_index]
            inst.log('Best move against ' + inst.opponent.name + ': ' + move.name + ' (index ' + str(best_move_index) + ')')
            inst.move_index %= 4  # Loop index back to zero if it exceeds 3
            for _ in range((best_move_index - inst.move_index + 4) % 4):
                inst.push_buttons((b'v', 1))
                inst.move_index = (inst.move_index + 1) % 4
            inst.push_buttons((b'a', 1), (b'a', 1), (b'a', 1), (b'b', 1), (b'b', 1))
            inst.pokemon.PP[inst.move_index] -= 1 if inst.opponent.ability != 'Pressure' else 2
        


def catch(inst):
    """Catch each boss after defeating it."""
    inst.push_buttons((b'a', 1.5))
    while inst.get_target_ball() != 'DEFAULT' and inst.get_target_ball() not in inst.check_ball():
        inst.push_buttons((b'<', 1.5))
    inst.push_buttons((b'a', 30))
    inst.record_ball_use()
    if inst.num_caught < 4:
        # Check caught rental Pokemon and decide whether to swap for it
        pokemon = inst.read_selectable_pokemon('catch')[0]
        # Give the new and existing Pokemon a score based on their performance against the remainder of the run (including the boss)
        rental_weight = 3 - inst.num_caught
        boss_weight = 2
        score = (rental_weight * inst.rental_scores[pokemon.name] + boss_weight * inst.boss_matchups[pokemon.name][inst.boss]) / (rental_weight + boss_weight)
        existing_score = inst.HP * (rental_weight * inst.rental_scores[inst.pokemon.name] + boss_weight * matchup_scoring.evaluate_matchup(inst.pokemon,inst.boss_pokemon[inst.boss],inst.rental_pokemon)) / (rental_weight + boss_weight)
        inst.log('Score for ' + pokemon.name + ':\t%0.2f' % score)
        inst.log('Score for ' + inst.pokemon.name + ':\t%0.2f' % existing_score)
        if score > existing_score:
            # Choose to swap your existing Pokemon for the new Pokemon
            inst.pokemon = pokemon
            inst.push_buttons((b'a', 3))
        else:
            inst.push_buttons((b'b', 3))
        inst.log('Detecting where the path led...')
        return 'detect'
    else:
        # Run was successful; wrap up and check the caught Pokemon
        inst.push_buttons((b'0',10))
        inst.log('Congratulations! Checking the haul from this run...')
        return 'select_pokemon'


def backpacker(inst):
    """Choose an item from the backpacker."""
    inst.push_buttons((b'0', 5), (b'a', 5))
    inst.log('Detecting where the path led...')
    return 'detect'


def scientist(inst):
    """Take (or not) a Pokemon from the scientist."""
    inst.push_buttons((b'0', 3), (b'b', 1))  # Don't take a Pokemon for now
    inst.log('Detecting where the path led...')
    return 'detect'


def select_pokemon(inst):
    """Check Pokemon caught during the run and keep one if it's shiny."""
    if inst.num_caught == 0:
        inst.push_buttons((b'o', 10), (b'b', 1))
        return 'done'

    inst.push_buttons((b'^', 1), (b'a', 1), (b'v', 1), (b'a', 3))

    # Check all Pokemon for shininess
    take_pokemon = False
    reset_game = False
    for i in range(inst.num_caught):
        if inst.check_shiny():
            inst.log('******************************\n\nShiny found!\n\n******************************')
            inst.shinies_found += 1
            inst.display_results(log=True)
            if inst.num_caught == 4 and i == 0:
                inst.display_results(log=True)
                inst.push_buttons((b'b', 3))
                return 'done'  # End whenever a shiny legendary is found
            else:
                take_pokemon = True
                break
        elif inst.num_caught == 4 and 'ball saver' in inst.mode.lower():
            if inst.check_sufficient_ore(inst.consecutive_resets + 2):
                reset_game = True
                break
            else:
                return 'done' # End if there isn't enough ore to keep resetting
        elif i < inst.num_caught - 1:
            inst.push_buttons((b'^',3))
        elif 'strong boss' in inst.mode.lower() and inst.num_caught == 4 and inst.check_sufficient_ore(inst.consecutive_resets + 1):
            reset_game = True

    # Wrap up at the end of the run        
    if not reset_game:
        if take_pokemon:
            inst.push_buttons((b'b', 3), (b'a', 1), (b'a', 1), (b'a', 1), (b'a', 1.5), (b'a', 3), (b'b', 2), (b'b', 10), (b'a', 2))
        else:
            inst.push_buttons((b'b', 3), (b'b', 1), (b'a', 2), (b'a', 2), (b'a', 11), (b'a', 1), (b'a', 2))
        inst.consecutive_resets = 0
        inst.dynite_ore += inst.num_caught + (2 if inst.num_caught == 4 else 0)
        if inst.num_caught > 1:
            inst.push_buttons((b'a', 2))
            if inst.num_caught == 4:
                inst.push_buttons((b'a', 2), (b'a', 2), (b'a', 2))
    else:
        inst.log('Resetting game...')
        inst.base_balls += min(3, inst.num_caught)
        inst.legendary_balls += 1 if inst.num_caught == 4 else 0
        inst.consecutive_resets += 1
        inst.dynite_ore -= inst.calculate_ore_cost(inst.consecutive_resets)
        inst.push_buttons((b'h', 2), (b'x', 2), (b'a', 3), (b'a', 2), (b'a', 20), (b'a', 10), (b'a', 3), (b'b', 3), (b'b', 3), (b'b', 3), (b'b', 3), (b'a', 3), (b'b', 3))
    inst.wins += 1 if inst.num_caught == 4 else 0
    inst.runs += 1
    inst.reset_run()
    if inst.check_sufficient_balls():
        inst.log('Preparing for another run...')
        return 'join'
    else:
        inst.log('Out of balls. Quitting...')
        return 'done'

    
def button_control_task(inst, actions):
    while inst.stage != 'done':
        with inst.lock:
            inst.stage = actions[inst.stage](inst)


def main_loop():
    """Main loop. Runs until a shiny is found or the user manually quits by pressing 'Q'."""

    # Connect to the Teensy over a serial port
    com = serial.Serial(COM_PORT, 9600, timeout=0.05)
    print('Connecting to ' + com.port + '...')
    while not com.is_open:
        try:
            com.open()
        except serial.SerialException:
            pass
    print('Connected!')

    # Open the video capture
    print('Opening the video connection...')
    cap = cv2.VideoCapture(VIDEO_INDEX)
    if str(cap) is None:
        print(
            'Failed to open the video connection. Check the config file and ensure no other application is using the video input.')
        return

    # Create a Max Lair Instance object to store information about each run and the entire sequence of runs
    instance = MaxLairInstance(BOSS, (BASE_BALL, BASE_BALLS, LEGENDARY_BALL, LEGENDARY_BALLS), com, cap, threading.Lock(),threading.Event(), datetime.now(),
                               (boss_pokemon_path, rental_pokemon_path, boss_matchup_LUT_path, rental_matchup_LUT_path,
                                rental_pokemon_scores_path), MODE, DYNITE_ORE, 'join')

    # DEBUG overrides for starting the script mid-run
    # instance.pokemon = instance.rental_pokemon['Electabuzz']
    ##    instance.num_caught = 1
    # instance.stage = 'detect'
    ##    instance.consecutive_resets = 1

    # Map stages to the appropriate function to execute when in each stage
    actions = {'join': join, 'path': path, 'detect': detect, 'battle': battle, 'catch': catch, 'backpacker': backpacker,
               'scientist': scientist, 'select_pokemon': select_pokemon}
    
    button_control_thread = threading.Thread(target=button_control_task, args=(instance,actions,))
    button_control_thread.start()
    

    # Start event loop after initializing the timer
    
    while instance.stage != 'done':

        # Execute the appropriate function for the current stage, and store the returned stage for the next loop
        with instance.lock:
            instance.display_results()
            # Quit if the Q key is pressed or if the button control thread finishes
            if cv2.waitKey(1) & 0xFF == ord('q') or not button_control_thread.is_alive():
                instance.exit_flag.set()
                break

        # Read responses from microcontroller
        instance.com.read(instance.com.inWaiting())

        
        time.sleep(0.02)

    # When finished, clean up video and serial connections
    instance.display_results(log=True)
    cap.release()
    com.close()
    # input('Press Enter to exit.')
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main_loop()
