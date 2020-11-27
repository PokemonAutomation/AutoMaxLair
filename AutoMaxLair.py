#   AutoMaxLair
#       Eric Donders
#       2020-11-20

import cv2, time, serial, numpy, pytesseract, random
from datetime import datetime
from MaxLairInstance import MaxLairInstance

pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

BOSS = 'Xerneas'
BALLS = 900
COM_PORT = 'COM4'
VIDEO_INDEX = 1

join_sequence = ((0,0,b'a'),    # Initiate conversation with scientist
                 (1.5,1,b'a'),    # Click through conversation
                 (3,2,b'a'),    # "Yes, please!"
                 (4.5,3,b'a'),  # Click through conversation 
                 (6,4,b'a'),  # Click through conversation
                 (7.5,5,b'a'),  # Select Pokemon (top of the list)
                 (8.5,6,b'a'),    # "Do you want to save your adventure so far?"
                 (10,7,b'a'),   # Yes
                 (14,8,b'v'),   # Move down to "Don't invite others"
                 (15,9,b'a'),   # Confirm
                 (20,10,b'a'),  # Select starting Pokemon (top of the list)
                 (50,11,b'0'))  # Wait until end

path_sequence = ((0,0,b'a'),    # Select a path
                 (2,1,b'0'))


def join(inst):
    """Join a Dynamax Adventure and choose a Pokemon."""
    stage_time = time.time() - inst.timer
    for step in join_sequence:
        if stage_time > step[0] and inst.substage == step[1]:
            inst.com.write(step[2])
            #print(step[2])
            inst.substage += 1
    if stage_time > join_sequence[-1][0]:
        inst.timer = time.time()
        inst.substage = 0
        print('Choosing a path...')
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
    text = inst.read_text((0.6,1,0,1))
    if 'Fight' in text:
        print('Battle starting...')
        return 'battle'
    elif 'backpacker' in text:
        print('Backpacker encountered...')
        return 'backpacker'
    elif 'swapping' in text:
        print('Scientist encountered...')
        return 'scientist'
    elif 'path' in text:
        print('Choosing a path...')
        return 'path'
    return 'detect'

def battle(inst):
    """Choose moves during a battle and detect whether the battle has ended."""
    stage_time = time.time()-inst.timer
    if inst.substage == 0:
        inst.timer = time.time()
        inst.substage += 1
    elif inst.substage == 1:
        text = inst.read_text((0.6,1,0,1)) # Read text from the bottom section of the screen
        #print(text)
        if 'Fight' in text or 'Cheer On' in text:
            inst.substage += 1
        elif 'Catch' in text:
            inst.reset_stage()
            print('Catching boss...')
            return 'catch'
        elif 'blown' in text:
            inst.reset_stage()
            print('You lose :(. Quitting...')
            return 'select_pokemon'
    elif inst.substage == 2:
        # Fight
        inst.timer = time.time()
        inst.com.write(b'a')
        # Choose a random move by moving the cursor down a random number of times
        inst.substage += 1 + random.randrange(4)
    elif inst.substage == 3 and stage_time > 0.5:
        inst.com.write(b'v')
        inst.substage += 1
        inst.timer = time.time()
    elif inst.substage == 4 and stage_time > 0.5:
        inst.com.write(b'v')
        inst.substage += 1
        inst.timer = time.time()
    elif inst.substage == 5 and stage_time > 0.5:
        inst.com.write(b'v')
        inst.substage += 1
        inst.timer = time.time()
    elif inst.substage == 6 and stage_time > 0.5:
        inst.com.write(b'a')
        inst.substage += 1
        inst.timer = time.time()
    elif inst.substage == 7 and stage_time > 1:
        inst.com.write(b'a')
        inst.substage += 1
    elif inst.substage == 8 and stage_time > 3: # Attempt to escape to the "Fight" screen in case something (no PP, choice lock) went wrong
        inst.com.write(b'b')
        inst.substage += 1
    elif inst.substage == 9 and stage_time > 4:
        inst.com.write(b'b')
        inst.substage = 1 # Return to substage 1 which will decide what needs to be done next
    return 'battle'

def catch(inst):
    """Catch each boss after defeating it."""
    stage_time = time.time()-inst.timer
    if inst.substage == 0:
        inst.timer = time.time()
        inst.com.write(b'a')
        inst.num_caught += 1
        inst.balls -= 1
        inst.substage += 1
    elif inst.substage == 1 and stage_time > 1:
        inst.com.write(b'a')
        inst.substage += 1
    elif inst.substage == 2 and stage_time > 30:
        # Swap Pokemon every time until a better solution is found
        inst.com.write(b'a')
        inst.substage += 1
    elif inst.substage == 3 and stage_time > 35:
        inst.reset_stage()
        if inst.num_caught < 4:
            print('Detecting where the path led...')
            return 'detect'
        else:
            print('Congratulations! Checking the haul from this run...')
            inst.wins += 1
            inst.reset_stage()
            return 'select_pokemon'
    return 'catch'

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
        print('Detecting where the path led...')
        return 'detect'
    return 'backpacker'

def scientist(inst):
    """Take (or not) a Pokemon from the scientist."""
    stage_time = time.time() - inst.timer
    if inst.substage == 0:
        inst.timer = time.time()
        inst.substage += 1
    elif inst.substage == 1 and stage_time > 3:
        inst.com.write(b'b')
        inst.substage += 1
    elif inst.substage == 2 and stage_time > 4:
        inst.reset_stage()
        print('Detecting where the path led')
        return 'detect'
    return 'scientist'


def select_pokemon(inst):
    """Check Pokemon caught during the run and keep one if it's shiny."""
    stage_time = time.time() - inst.timer
    if inst.substage == 0 and stage_time > 5:
        inst.runs += 1
        print('Checking caught Pokemon...')
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
        if inst.check_shiny():
            inst.substage = 100 # Goto take Pokemon
            inst.timer = time.time()
            print('Shiny found!')
            return 'done' # Pause whenever a shiny is found for now
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
        if inst.num_caught < 3:
            inst.substage = 19
        elif inst.num_caught < 4:
            inst.substage = 17
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
        inst.substage += 1
    elif inst.substage == 19 and stage_time > 10:
        inst.reset_run()
        if inst.balls >=4:
            print('Preparing for another run...')
            return 'initialize'
        else:
            print('Out of balls. Quitting...')
            return 'done'
    return 'select_pokemon'
        


def display_results(inst, stage, frame_start, runs):
    """Display video from the Switch alongside some annotations describing the run sequence."""
    elapsed_time = time.time()-frame_start
    if elapsed_time > 0:
        fps = '%0.1f' % (1 / (time.time()-frame_start))
    else:
        fps = 'High'
    if inst.runs == 0:
        win_percent = 0
    else:
        win_percent = round(100*inst.wins/inst.runs)
    frame = cv2.copyMakeBorder(inst.get_frame(), 0, 0, 0, 200, cv2.BORDER_CONSTANT)
    height, width, channels = frame.shape

    labels = ('Run #','Stage: ', 'Substage: ', 'FPS: ', 'Balls: ', 'Pokemon caught: ', 'Pokemon: ', 'HP: ', 'Win percentage: ')
    values = (str(runs), stage, str(inst.substage), fps, str(inst.balls), str(inst.num_caught), str(inst.pokemon), str(inst.HP), str(win_percent)+'%')

    for i in range(len(labels)):
        cv2.putText(frame, labels[i]+values[i], (width-185,25+25*i), cv2.FONT_HERSHEY_PLAIN,1,(255,255,255),2,cv2.LINE_AA)
    cv2.imshow('Output',frame)
    

def main_loop():
    """Main loop. Runs until a shiny is found or the user manually quits by pressing 'Q'."""
    com = serial.Serial(COM_PORT, 9600, timeout=0.05)
    print('Connecting to '+com.port+'...')
    while not com.is_open:
        try:
            com.open()
        except SerialException:
            pass
    print('Connected!')

    print('Opening the video connection...')
    cap = cv2.VideoCapture(VIDEO_INDEX)

    stage = 'initialize'
    runs = 0

    instance = MaxLairInstance(BOSS, BALLS, com, cap)

    frame_start = time.time()
    while stage != 'done':
        if stage == 'initialize':
            # Instantiate a new Max Lair instance
            runs += 1
            print('Run #'+str(runs)+' started!')
            time.sleep(2)
            instance.reset_stage()
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


        display_results(instance, stage, frame_start, runs)
        frame_start = time.time()


        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


    # When finished, clean up video and serial connections
    instance.cap.release()
    cv2.destroyAllWindows()
    com.close()



main_loop()
