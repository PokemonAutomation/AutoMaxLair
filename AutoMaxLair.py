#   AutoMaxLair
#       Eric Donders
#       2020-11-20

import cv2, time, serial, numpy, pytesseract, random, pickle, enchant, configparser
from datetime import datetime
from MaxLairInstance import MaxLairInstance
from Pokemon_Data import matchup_scoring

# Change this section according to your Tesseract installation
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

# Load configuration from config file
config = configparser.ConfigParser()
config.read('Config.ini')
BOSS = config['default']['BOSS']
BALLS = int(config['default']['BALLS'])
COM_PORT = config['default']['COM_PORT']
VIDEO_INDEX = int(config['default']['VIDEO_INDEX'])


# Load precalculated resources for choosing Pokemon and moves
boss_pokemon = pickle.load(open('Pokemon_Data/Boss_Pokemon.pickle', 'rb'))
rental_pokemon = pickle.load(open('Pokemon_Data/Rental_Pokemon.pickle', 'rb'))
boss_matchups = pickle.load(open('Pokemon_Data/Boss_Matchup_LUT.pickle', 'rb'))
rental_matchups = pickle.load(open('Pokemon_Data/Rental_Matchup_LUT.pickle', 'rb'))
rental_scores = pickle.load(open('Pokemon_Data/Rental_Pokemon_Scores.pickle', 'rb'))


def fix_name(text):
    """Matches OCRed Pokemon names (which are often slightly wrong) to a rental Pokemon"""
    best_match = ''
    match_value = 100
    for name in rental_pokemon.keys():
        distance = enchant.utils.levenshtein(text, name.split(' (')[0]) # Note that variants of the same Pokemon (e.g., regional variants and Lycanroc) can not be distinguished
        if distance < match_value:
            # Record the best match
            match_value = distance
            best_match = name
    if match_value > 3:
        print('WARNING: could not find a good match for Pokemom: "'+text+'"')
    return best_match


# Define button press sequences for different stages of the Dynamax Adventure
join_sequence = ((0,0,b'a'), # Initiate conversation with scientist
                 (0.5,1,b'a'), # Click again in case the first click was needed to connect the controller
                 (1.5,2,b'a'),    # Click through conversation
                 (3,3,b'a'),    # "Yes, please!"
                 (4.5,4,b'a'),  # Click through conversation 
                 (6,5,b'a'),  # Click through conversation
                 (7.5,6,b'a'),  # Select Pokemon (top of the list)
                 (8.5,7,b'a'),    # "Do you want to save your adventure so far?"
                 (10,8,b'a'),   # Yes
                 (14,9,b'v'),   # Move down to "Don't invite others"
                 (15,10,b'a'),   # Confirm
                 (20,11,b'0'))  # End this sequence and choose a Pokemon

path_sequence = ((0,0,b'a'),    # Select a path
                 (4,1,b'0'))

def join(inst):
    """Join a Dynamax Adventure and choose a Pokemon."""
    stage_time = time.time() - inst.timer
    for step in join_sequence:
        if stage_time > step[0] and inst.substage == step[1]:
            inst.com.write(step[2])
            #print(step[2])
            inst.substage += 1

    # Pokemon selection subroutine
    if stage_time > join_sequence[-1][0] and inst.substage == join_sequence[-1][1]+1:
        # Read Pokemon names from specified regtions
        pokemon_names = inst.read_selectable_pokemon('join')
        pokemon_list = []
        pokemon_scores = []
        for name in pokemon_names:
            # Match each name to a rental Pokemon object with preconfigured moves, stats, etc.
            name = fix_name(name)
            inst.log(name)
            try:
                pokemon_list.append(rental_pokemon[name])
                # Score each Pokemon by its average performance against the remaining path
                score = (3*rental_scores[name]+2*boss_matchups[name][BOSS]) / 4
                pokemon_scores.append(score)
                inst.log('Score for '+name+':\t%0.2f'%score)
            except KeyError:
                inst.log('*****WARNING*****\nPokemon name not found in dictionary: '+name)
                pokemon_list.append(None)
                inst.substage = 99
                return 'join'
        selection_index = pokemon_scores.index(max(pokemon_scores))
        inst.pokemon = pokemon_list[selection_index]
        inst.reset_stage()
        inst.substage = 99-selection_index # Go to the appropriate stage for navigating to the desired Pokemon
    elif inst.substage == 97 and stage_time > 1:
        inst.com.write(b'v')
        inst.reset_stage()
        inst.substage = 98
    elif inst.substage == 98 and stage_time > 1:
        inst.com.write(b'v')
        inst.reset_stage()
        inst.substage = 99
    elif inst.substage == 99 and stage_time > 1:
        inst.com.write(b'a')
        inst.reset_stage()
        inst.substage = 100
    elif inst.substage == 100 and stage_time > 30:
        inst.reset_stage()
        inst.log('Choosing a path...')
        return 'path'
    return 'join' # If not finished this stage, run it again next loop

def path(inst):
    """Choose a path to follow."""
    stage_time = time.time() - inst.timer
    for step in path_sequence:
        if stage_time > step[0] and inst.substage == step[1]:
            inst.com.write(step[2])
            #print(step[2])
            inst.substage += 1
    if stage_time > path_sequence[-1][0]:
        inst.timer = time.time()
        inst.substage = 0
        print('Detecting where the path led...')
        return('detect')
    return 'path' # If not finished this stage, run it again next loop

def detect(inst):
    """Detect whether the chosen path has led to a battle, scientist, backpacker, or fork in the path."""
    text = inst.read_text(((0,0.6),(1,1)), invert=True)
    if ' appeared' in text:
        # Boss appeared so let's read what it is
        if inst.num_caught < 3 and inst.opponent == None:
            # Detect which boss appeared
            text_split = text.split(' app')
            if 'eared!' in text_split[1]:
                inst.opponent = rental_pokemon[fix_name(text_split[0].strip())]
                inst.log('Opponent detected: '+inst.opponent.name)
        inst.log('Battle starting...')
        return 'battle'       
    elif 'Fight' in text:
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
    return 'detect' # If not finished this stage, run it again next loop

def battle(inst):
    """Choose moves during a battle and detect whether the battle has ended."""
    stage_time = time.time()-inst.timer
    if inst.substage == 0:
        inst.timer = time.time()
        inst.substage += 1

    # Detection subroutine
    elif inst.substage == 1:
        text = inst.read_text(((0,0.6),(1,1)), invert=True) # Read text from the bottom section of the screen
        #print(text)
        if 'Fight' in text:
            inst.substage = 2 # Go to move selection sequence
        elif 'Cheer On' in text:
            inst.substage = 6
            inst.dmax_timer = -1
        elif 'Catch' in text:
            inst.reset_stage()
            inst.log('Catching boss...')
            return 'catch' # Go to catch sequence
        elif 'blown' in text:
            inst.reset_stage() 
            inst.log('You lose :(. Quitting...')
            return 'select_pokemon' # Go to quit sequence
        elif 'gathered around' in text:
            inst.timer = time.time()
            inst.substage = 12 # Choose to dynamax, then choose a move as usual

    # Move selection subroutine
    elif inst.substage == 2:
        # Fight
        inst.timer = time.time()+0.5
        inst.com.write(b'a')
        if inst.opponent == None:
            # Try to detect the opponent if it wasn't already detected
            if inst.num_caught < 3:
                inst.substage = 20
                return 'battle'
            else:
                inst.opponent = boss_pokemon[BOSS]
        # Choose the best move to use
        best_move_index = matchup_scoring.select_best_move(inst.pokemon, inst.opponent)
        inst.log('Best move against '+inst.opponent.name+': '+inst.pokemon.moves[best_move_index].name+' (index '+str(best_move_index)+')')
        # Reduce PP accordingly
        new_PP = list(inst.pokemon.PP)
        new_PP[best_move_index] -= 1
        if inst.opponent and inst.opponent.ability == 'Pressure':
            new_PP[best_move_index] -= 1
        inst.pokemon.PP = tuple(new_PP)
        # Handle the Dynamax timer
        if inst.dmax_timer == 0:
            inst.dmax_timer = -1
            inst.move_index = 0
        elif inst.dmax_timer > 0:
            inst.dmax_timer -= 1
        # Go to the appropriate stage for navigating to the correct move
        to_move = (best_move_index-inst.move_index)
        if to_move < 0: # Cycle back through the bottom to a previous move
            to_move += 4
        inst.substage += 4 - to_move
    elif 3 <= inst.substage <= 5 and stage_time > 0.5:
        # Navigate to the correct move
        inst.com.write(b'v')
        inst.move_index += 1
        inst.timer = time.time()
        inst.substage += 1
    elif inst.substage == 6 and stage_time > 0.5:
        inst.com.write(b'a')
        inst.substage += 1
        inst.timer = time.time()
    elif inst.substage == 7 and stage_time > 1:
        inst.com.write(b'a')
        inst.substage += 1
    elif inst.substage == 8 and stage_time > 2:
        inst.com.write(b'a') # Press A once more for good measure
        inst.substage += 1
    elif inst.substage == 9 and stage_time > 4: # Attempt to escape to the "Fight" screen in case something (no PP, choice lock) went wrong
        inst.com.write(b'b')
        inst.substage += 1
    elif inst.substage == 10 and stage_time > 5:
        inst.com.write(b'b')
        inst.substage = 1 # Return to substage 1 which will decide what needs to be done next

    # Dynamax initiation subroutine
    elif inst.substage == 12 and stage_time > 3:
        inst.com.write(b'a')
        inst.substage += 1
    elif inst.substage == 13 and stage_time > 4:
        inst.com.write(b'<')
        inst.substage += 1
    elif inst.substage == 14 and stage_time > 5:
        inst.dmax_timer = 3
        inst.substage = 2 # Dynamax and then choose a move as usual

    # Opponent detection subroutine    
    elif inst.substage == 20 and stage_time > 0.5:
        inst.com.write(b'a')
        inst.substage += 1 # Navigate to the target selection screen so the opponent name can be read
    elif inst.substage == 21 and stage_time > 4:
        inst.opponent = rental_pokemon[fix_name(inst.read_selectable_pokemon('battle')[0])]
        inst.log('Opponent detected: '+inst.opponent.name)
        inst.com.write(b'b')
        inst.substage += 1
    elif inst.substage == 22 and stage_time > 6:
        inst.com.write(b'b')
        inst.timer = time.time()
        inst.substage = 1 # Return to substage 1 which will decide what needs to be done next

    # If not finished this stage, run it again next loop
    return 'battle' 

def catch(inst):
    """Catch each boss after defeating it."""
    stage_time = time.time()-inst.timer
    if inst.substage == 0: # Click "Catch"
        inst.timer = time.time()
        inst.com.write(b'a')
        inst.num_caught += 1
        inst.balls -= 1
        inst.substage += 1
    elif inst.substage == 1 and stage_time > 1: # Select the default ball
        inst.com.write(b'a')
        inst.substage += 1
    elif inst.substage == 2 and stage_time > 30:
        # Choose whether to keep the Pokemon if it's one of the first 3 bosses, or wrap up the run otherwise
        if inst.num_caught < 4:
            pokemon_list = inst.read_selectable_pokemon('catch')
            pokemon_name = fix_name(pokemon_list[-1])
            pokemon=None
            # Match the Pokemon's name to a rental in the dictionary
            pokemon = rental_pokemon[pokemon_name]
            # Give the new and existing Pokemon a score based on their performance against the remainder of the run (including the boss)
            score = ((3-inst.num_caught)*rental_scores[pokemon_name]+boss_matchups[pokemon_name][BOSS]) / (1+3-inst.num_caught)
            existing_score = inst.HP * ((3-inst.num_caught)*rental_scores[inst.pokemon.name]+boss_matchups[inst.pokemon.name][BOSS]) / (1+3-inst.num_caught)
            inst.log('Score for '+pokemon_name+':\t%0.2f'%score)
            inst.log('Score for '+inst.pokemon.name+':\t%0.2f'%existing_score)
            if score > existing_score:
                # Choose to swap your existing Pokemon for the new Pokemon
                inst.com.write(b'a')
                inst.pokemon = pokemon
            else:
                # Choose not to take the new Pokemon
                inst.com.write(b'b')
            inst.reset_stage()
            inst.log('Detecting where the path led...')
            return 'detect'
        else:
            inst.com.write(b'a')
            inst.substage = 100
    elif inst.substage == 100 and stage_time > 35:
        # Run was successful; wrap up and check the caught Pokemon
        inst.reset_stage()
        inst.log('Congratulations! Checking the haul from this run...')
        inst.wins += 1
        inst.reset_stage()
        return 'select_pokemon'
    return 'catch' # If not finished this stage, run it again next loop

def backpacker(inst):
    """Choose an item from the backpacker."""
    stage_time = time.time() - inst.timer
    if inst.substage == 0:
        inst.timer = time.time()
        inst.substage += 1
    elif inst.substage == 1 and stage_time > 5:
        inst.com.write(b'a') # Pick whatever the first item is
        inst.substage += 1
    elif inst.substage == 2 and stage_time > 10:
        inst.reset_stage()
        inst.log('Detecting where the path led...')
        return 'detect'
    return 'backpacker' # If not finished this stage, run it again next loop

def scientist(inst):
    """Take (or not) a Pokemon from the scientist."""
    stage_time = time.time() - inst.timer
    if inst.substage == 0:
        inst.timer = time.time()
        inst.substage += 1
    elif inst.substage == 1 and stage_time > 3:
        inst.com.write(b'b') # Don't take a new Pokemon for now
        inst.substage += 1
    elif inst.substage == 2 and stage_time > 4:
        inst.reset_stage()
        inst.log('Detecting where the path led')
        return 'detect'
    return 'scientist' # If not finished this stage, run it again next loop


def select_pokemon(inst):
    """Check Pokemon caught during the run and keep one if it's shiny."""
    stage_time = time.time() - inst.timer
    if inst.substage == 0 and stage_time > 5:
        inst.runs += 1
        inst.log('Checking caught Pokemon...')
        inst.com.write(b'^') # Put cursor on last Pokemon
        inst.substage += 1
    elif inst.substage == 1 and stage_time > 6:
        inst.com.write(b'a') # Click Pokemon
        inst.substage += 1
    elif inst.substage == 2 and stage_time > 7:
        inst.com.write(b'v') # Move the cursor down
        inst.substage += 1
    elif inst.substage == 3 and stage_time > 8:
        inst.com.write(b'a') # Summary screen
        inst.timer = time.time()
        inst.substage += (5 - inst.num_caught)
    elif (4 <= inst.substage <=7) and stage_time > 2:
        # Check for shininess and move to the next Pokemon if not
        if inst.check_shiny():
            inst.timer = time.time()
            inst.log('******************************\n\nShiny found!\n\n******************************')
            if inst.substage == 4:
                return 'done' # End whenever a shiny legendary is found
            else:
                inst.substage = 50 # Goto take Pokemon
        elif stage_time > 3:
            if inst.substage < 7:
                inst.com.write(b'^') # Check next Pokemon
            inst.timer = time.time()
            inst.substage += 1
    elif inst.substage == 8 and stage_time > 1:
        # Don't take any Pokemon
        inst.com.write(b'b')
        inst.substage += 1
    elif inst.substage == 9 and stage_time > 4:
        inst.com.write(b'b')
        inst.substage += 1
    elif inst.substage == 10 and stage_time > 5:
        inst.com.write(b'a')
        inst.substage += 1
    elif inst.substage == 11 and stage_time > 7:
        inst.com.write(b'a')
        inst.substage += 1
    elif inst.substage == 12 and stage_time > 9:
        inst.com.write(b'a')
        inst.substage += 1
    elif inst.substage == 13 and stage_time > 21:
        inst.com.write(b'a')
        inst.substage += 1
    elif inst.substage == 14 and stage_time > 22:
        inst.com.write(b'a')
        # Depending on how well the run went, the dialogue changes. Adjust the stage to account for this behaviour
        if inst.num_caught < 1:
            return 'done' # Debug; winning 0 battles currently breaks the bot
        if inst.num_caught < 3:
            inst.substage = 100
        elif inst.num_caught < 4:
            inst.substage = 18
        else:
            inst.substage += 2
        inst.timer = time.time()
    elif inst.substage == 15 and stage_time > 2:
        inst.com.write(b'a')
        inst.substage += 1
    elif inst.substage == 16 and stage_time > 4:
        inst.com.write(b'a')
        inst.substage += 1
    elif inst.substage == 17 and stage_time > 6:
        inst.com.write(b'a')
        inst.substage += 1
    elif inst.substage == 18 and stage_time > 8:
        inst.com.write(b'a')
        inst.substage = 100
        inst.timer = time.time()

    # Take selected Pokemon subroutine
    elif inst.substage == 50 and stage_time > 1:
        inst.com.write(b'b')
        inst.substage += 1
    elif inst.substage == 51 and stage_time > 4:
        inst.com.write(b'a')
        inst.substage += 1
    elif inst.substage == 52 and stage_time > 5:
        inst.com.write(b'a')
        inst.substage += 1
    elif inst.substage == 53 and stage_time > 6:
        inst.com.write(b'a')
        inst.substage += 1
    elif inst.substage == 54 and stage_time > 7:
        inst.com.write(b'a')
        inst.substage += 1
    elif inst.substage == 55 and stage_time > 8:
        inst.com.write(b'a')
        inst.substage += 1
    elif inst.substage == 56 and stage_time > 12:
        inst.com.write(b'a')
        inst.substage += 1
    elif inst.substage == 57 and stage_time > 22:
        inst.substage = 13
        inst.timer = time.time()

    # Wrap up and prepare for the next run (or quit if out of balls)
    elif inst.substage == 100 and stage_time > 2:
        inst.reset_run()
        if inst.balls >=4:
            inst.log('Preparing for another run...')
            return 'initialize'
        else:
            inst.log('Out of balls. Quitting...')
            return 'done'
    return 'select_pokemon' # If not finished this stage, run it again next loop
        


def display_results(inst, stage, frame_start, runs, log=False):
    """Display video from the Switch alongside some annotations describing the run sequence."""
    # Calculate some statistics for display
    elapsed_time = time.time()-frame_start
    if elapsed_time > 0:
        fps = '%0.1f' % (1 / (time.time()-frame_start))
    else:
        fps = 'High'
    if inst.runs == 0:
        win_percent = None
        time_per_run = None
    else:
        win_percent = round(100*inst.wins/inst.runs)
        time_per_run = (datetime.now()-inst.start_date)/inst.runs

    # Expand the image with blank space for writing results
    frame = cv2.copyMakeBorder(inst.get_frame(stage=stage), 0, 0, 0, 200, cv2.BORDER_CONSTANT)
    height, width, channels = frame.shape

    # Construct arrays of text and values to display
    labels = ('Run #','Stage: ', 'Substage: ', 'FPS: ', 'Balls: ', 'Pokemon caught: ', 'Pokemon: ', 'HP: ', 'Opponent: ', 'Win percentage: ', 'Time per run: ')
    values = (str(runs), stage, str(inst.substage), fps, str(inst.balls), str(inst.num_caught), str(inst.pokemon), str(inst.HP), str(inst.opponent), str(win_percent)+'%', str(time_per_run))

    for i in range(len(labels)):
        cv2.putText(frame, labels[i]+values[i], (width-195,25+25*i), cv2.FONT_HERSHEY_PLAIN,1,(255,255,255),2,cv2.LINE_AA)
        if log:
            inst.log(labels[i]+values[i])

    # Display
    cv2.imshow('Output',frame)
    if log:
        # Save a copy of the final image
        cv2.imwrite(inst.filename[:-8]+'_cap.png', frame)
    

def main_loop():
    """Main loop. Runs until a shiny is found or the user manually quits by pressing 'Q'."""
    global rental_pokemon

    # Connect to the Teensy over a serial port
    com = serial.Serial(COM_PORT, 9600, timeout=0.05)
    print('Connecting to '+com.port+'...')
    while not com.is_open:
        try:
            com.open()
        except SerialException:
            pass
    print('Connected!')

    # Open the video capture
    print('Opening the video connection...')
    cap = cv2.VideoCapture(VIDEO_INDEX)

    # Create a Max Lair Instance object to store information about each run and the entire sequence of runs
    instance = MaxLairInstance(BOSS, BALLS, com, cap, datetime.now())
    #instance.pokemon = rental_pokemon['Nidoking']
    #instance.num_caught = 1
    
    stage = 'initialize'
    runs = 0

    # Start event loop after initializing the timer
    frame_start = time.time()
    while stage != 'done':
        if stage == 'initialize':
            # Instantiate a new Max Lair instance
            runs += 1
            instance.log('Run #'+str(runs)+' started!')
            time.sleep(1)
            instance.reset_stage()
            rental_pokemon = pickle.load(open('Pokemon_Data/Rental_Pokemon.pickle', 'rb')) # Reload in case previous runs modify some of the Pokemon
            stage = 'join'
        elif stage == 'join':
            stage = join(instance)
        elif stage == 'path':
            stage = path(instance)
        elif stage == 'detect':
            stage = detect(instance)
        elif stage == 'battle':
            stage = battle(instance)
        elif stage == 'catch':
            stage = catch(instance)
        elif stage == 'backpacker':
            stage = backpacker(instance)
        elif stage == 'scientist':
            stage = scientist(instance)
        elif stage == 'select_pokemon':
            stage = select_pokemon(instance)


        # Display a frame of the incoming video and some stats after each loop
        display_results(instance, stage, frame_start, runs)
        frame_start = time.time()

        # Quit if the Q key is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


    # When finished, clean up video and serial connections
    display_results(instance, stage, frame_start, runs, log=True)
    instance.cap.release()
    com.close()
    #input('Press Enter to exit.')
    cv2.destroyAllWindows()
    


if __name__ == '__main__':
    main_loop()
