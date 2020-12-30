#   MaxLairInstance
#       Eric Donders
#       2020-11-20

import cv2, time, pytesseract, enchant, pickle, sys
from datetime import datetime
from typing import TypeVar, Dict, List, Tuple
Pokemon = TypeVar('Pokemon')
Move = TypeVar('Move')
Serial = TypeVar('serial.Serial')
VideoCapture = TypeVar('cv2.VideoCapture')
DateTime = TypeVar('datetime.datetime')
Image = TypeVar('cv2 image')

class MaxLairInstance():
    def __init__(self,
                 boss: str,
                 balls: int,
                 com: Serial,
                 cap: Serial,
                 lock,
                 exit_flag,
                 datetime: DateTime,
                 pokemon_data_paths: Tuple[str, str, str, str],
                 mode: str,
                 dynite_ore: int,
                 stage: str='join') -> None:
        self.boss_pokemon_path, self.rental_pokemon_path, self.boss_matchups_path, self.rental_matchups_path, self.rental_scores_path = pokemon_data_paths
        self.reset_run()
        
        self.start_date = datetime
        self.filename = ''.join(('Logs//',boss,'_',datetime.strftime('%Y-%m-%d %H-%M-%S'),'_log.txt'))
        self.boss = boss
        self.base_ball, self.base_balls, self.legendary_ball, self.legendary_balls = balls
        self.mode = mode
        self.dynite_ore = dynite_ore
        self.stage = stage

        self.runs = 0
        self.wins = 0
        self.shinies_found = 0
        self.consecutive_resets = 0

        # Video capture and serial communication objects
        self.cap = cap
        self.cap.set(3, 1280)
        self.cap.set(4, 720)
        self.com = com
        self.lock = lock
        self.exit_flag = exit_flag

        # Rectangles for checking shininess and reading specific text
        # Shiny star rectangle
        self.shiny_rect = ((0.075,0.53), (0.105,0.58))
        # Selectable Pokemon names rectangles
        self.sel_rect_1 = ((0.485,0.28), (0.60,0.33))
        self.sel_rect_2 = ((0.485,0.54), (0.60,0.59))
        self.sel_rect_3 = ((0.485,0.80), (0.60,0.855))
        self.sel_rect_4 = ((0.485,0.59), (0.60,0.645))
        # In-battle Pokemon name & type rectangles
        self.sel_rect_5 = ((0.195,0.11), (0.39,0.16))
        self.type_rect_1 = ((0.24,0.17), (0.31,0.215))
        self.type_rect_2 = ((0.35,0.17), (0.425,0.214))
        # Selectable Pokemon abilities rectangles
        self.abil_rect_1 = ((0.485,0.33), (0.60,0.39))
        self.abil_rect_2 = ((0.485,0.59), (0.60,0.65))
        self.abil_rect_3 = ((0.485,0.85), (0.60,0.91))
        self.abil_rect_4 = ((0.485,0.645), (0.60,0.69))
        # Poke ball rectangle
        self.ball_rect = ((0.69,0.63), (0.88,0.68))


    def reset_run(self) -> None:
        """Reset in preparation for a new Dynamax Adventure."""
        self.pokemon = None
        self.HP = 1 # 1 = 100%
        self.num_caught = 0
        self.reset_stage()
        # Load precalculated resources for choosing Pokemon and moves
        self.boss_pokemon = pickle.load(open(self.boss_pokemon_path, 'rb'))
        self.rental_pokemon = pickle.load(open(self.rental_pokemon_path, 'rb'))
        self.boss_matchups = pickle.load(open(self.boss_matchups_path, 'rb'))
        self.rental_matchups = pickle.load(open(self.rental_matchups_path, 'rb'))
        self.rental_scores = pickle.load(open(self.rental_scores_path, 'rb'))
        
    def reset_stage(self) -> None:
        """Reset after a battle."""
        self.move_index = 0
        self.dmax_timer = -1
        self.opponent = None
        self.dynamax_available = False
        if self.pokemon is not None:
            if self.pokemon.name == 'Ditto':
                self.pokemon = self.rental_pokemon['Ditto']
            self.pokemon.dynamax = False
        

    def get_frame(self,
                  stage: str='') -> Image:
        """Get an annotated image of the current Switch output."""
        img = self.cap.read()[1]

        # Draw rectangles around detection areas
        h, w = img.shape[:2]
        if stage == 'select_pokemon':
            cv2.rectangle(img, (round(self.shiny_rect[0][0]*w)-2,round(self.shiny_rect[0][1]*h)-2),
                          (round(self.shiny_rect[1][0]*w)+2,round(self.shiny_rect[1][1]*h)+2), (0,255,0), 2)
        elif stage == 'join':
            cv2.rectangle(img, (round(self.sel_rect_1[0][0]*w)-2,round(self.sel_rect_1[0][1]*h)-2),
                          (round(self.sel_rect_1[1][0]*w)+2,round(self.sel_rect_1[1][1]*h)+2), (0,255,0), 2)
            cv2.rectangle(img, (round(self.sel_rect_2[0][0]*w)-2,round(self.sel_rect_2[0][1]*h)-2),
                          (round(self.sel_rect_2[1][0]*w)+2,round(self.sel_rect_2[1][1]*h)+2), (0,255,0), 2)
            cv2.rectangle(img, (round(self.sel_rect_3[0][0]*w)-2,round(self.sel_rect_3[0][1]*h)-2),
                          (round(self.sel_rect_3[1][0]*w)+2,round(self.sel_rect_3[1][1]*h)+2), (0,255,0), 2)
            cv2.rectangle(img, (round(self.abil_rect_1[0][0]*w)-2,round(self.abil_rect_1[0][1]*h)-2),
                          (round(self.abil_rect_1[1][0]*w)+2,round(self.abil_rect_1[1][1]*h)+2), (0,255,255), 2)
            cv2.rectangle(img, (round(self.abil_rect_2[0][0]*w)-2,round(self.abil_rect_2[0][1]*h)-2),
                          (round(self.abil_rect_2[1][0]*w)+2,round(self.abil_rect_2[1][1]*h)+2), (0,255,255), 2)
            cv2.rectangle(img, (round(self.abil_rect_3[0][0]*w)-2,round(self.abil_rect_3[0][1]*h)-2),
                          (round(self.abil_rect_3[1][0]*w)+2,round(self.abil_rect_3[1][1]*h)+2), (0,255,255), 2)
        elif stage == 'catch':
            cv2.rectangle(img, (round(self.sel_rect_4[0][0]*w)-2,round(self.sel_rect_4[0][1]*h)-2),
                          (round(self.sel_rect_4[1][0]*w)+2,round(self.sel_rect_4[1][1]*h)+2), (0,255,0), 2)
            cv2.rectangle(img, (round(self.abil_rect_4[0][0]*w)-2,round(self.abil_rect_4[0][1]*h)-2),
                          (round(self.abil_rect_4[1][0]*w)+2,round(self.abil_rect_4[1][1]*h)+2), (0,255,255), 2)
            cv2.rectangle(img, (round(self.ball_rect[0][0]*w)-2,round(self.ball_rect[0][1]*h)-2),
                          (round(self.ball_rect[1][0]*w)+2,round(self.ball_rect[1][1]*h)+2), (0,0,255), 2)
        elif stage == 'battle':
            cv2.rectangle(img, (round(self.sel_rect_5[0][0]*w)-2,round(self.sel_rect_5[0][1]*h)-2),
                          (round(self.sel_rect_5[1][0]*w)+2,round(self.sel_rect_5[1][1]*h)+2), (0,255,0), 2)
            cv2.rectangle(img, (round(self.type_rect_1[0][0]*w)-2,round(self.type_rect_1[0][1]*h)-2),
                          (round(self.type_rect_1[1][0]*w)+2,round(self.type_rect_1[1][1]*h)+2), (255,255,0), 2)
            cv2.rectangle(img, (round(self.type_rect_2[0][0]*w)-2,round(self.type_rect_2[0][1]*h)-2),
                          (round(self.type_rect_2[1][0]*w)+2,round(self.type_rect_2[1][1]*h)+2), (255,255,0), 2)

        # Return the scaled and annotated image
        return img


    def read_text(self,
                  img: Image,
                  section: Tuple[Tuple[float, float], Tuple[float, float]]=((0,0),(1,1)),
                  threshold: bool=True,
                  invert: bool=False,
                  language: str='eng',
                  segmentation_mode: str='--psm 11') -> str:
        """Read text from a section (default entirety) of an image using Tesseract."""
        # Image is optionally supplied, usually when multiple text areas must be read so the image only needs to be fetched once
        if img is None:
            img = self.get_frame()

        # Process image according to instructions
        h, w, channels = img.shape
        if threshold:
            img = cv2.inRange(cv2.cvtColor(img, cv2.COLOR_BGR2HSV), (0,0,100), (180,15,255))
        if invert:
            img = cv2.bitwise_not(img)
        img = img[round(section[0][1]*h):round(section[1][1]*h),
                  round(section[0][0]*w):round(section[1][0]*w)]
        #cv2.imshow('Text Area', img) # DEBUG

        # Read text using Tesseract and return the raw text
        self.lock.release()
        if self.exit_flag.is_set():
            sys.exit()
        text = pytesseract.image_to_string(img, lang=language, config=segmentation_mode)
        self.lock.acquire()

        return text

    def identify_pokemon(self,
                         name: str,
                         ability: str='',
                         types: str='') -> Pokemon:
        """Match OCRed Pokemon to a rental Pokemon."""
        text = name.replace('\n','')+ability.replace('\n','')+types.replace('\n','')
        matched_text = ''
        best_match = None
        match_value = 1000
        for key in self.rental_pokemon.keys():
            pokemon = self.rental_pokemon[key]
            string_to_match = pokemon.name.split(' (')[0]
            if ability != '':
                string_to_match += pokemon.ability
            if types != '':
                string_to_match += pokemon.types[0] + pokemon.types[1]
            distance = enchant.utils.levenshtein(text, string_to_match)
            if distance < match_value:
                match_value = distance
                best_match = pokemon
                matched_text = string_to_match
        if match_value > len(text)/3:
            print('WARNING: could not find a good match for Pokemon: "'+text+'"')
            pass
        print('OCRed Pokemon '+text+' matched to rental Pokemon '+matched_text+' with distance of '+str(match_value)) # DEBUG
        return best_match

    def read_selectable_pokemon(self,
                                stage: str) -> List[Pokemon]:
        """Return a list of available Pokemon names."""
        # Fetch the image from the Switch output
        image = self.get_frame()

        # Get a list of Pokemon names present, depending on stage
        pokemon_names = []
        abilities = []
        types = []
        pokemon_list = []
        if stage == 'join':
            pokemon_names.append(self.read_text(image, self.sel_rect_1, threshold=False, invert=True, language=None, segmentation_mode='--psm 8').strip())
            pokemon_names.append(self.read_text(image, self.sel_rect_2, threshold=False, language=None, segmentation_mode='--psm 8').strip())
            pokemon_names.append(self.read_text(image, self.sel_rect_3, threshold=False, language=None, segmentation_mode='--psm 3').strip()) # This last name shifts around between runs necessitating a bigger rectangle and different text segmentation mode
            abilities.append(self.read_text(image, self.abil_rect_1, threshold=False, invert=True, language=None, segmentation_mode='--psm 8').strip())
            abilities.append(self.read_text(image, self.abil_rect_2, threshold=False, language=None, segmentation_mode='--psm 8').strip())
            abilities.append(self.read_text(image, self.abil_rect_3, threshold=False, language=None, segmentation_mode='--psm 3').strip())
            types = ['','','']
        elif stage == 'catch':
            pokemon_names.append(self.read_text(image, self.sel_rect_4, threshold=False, language=None, segmentation_mode='--psm 3').strip().split('\n')[-1])
            abilities.append(self.read_text(image, self.abil_rect_4, threshold=False, language=None, segmentation_mode='--psm 3').strip())
            types.append('')
        elif stage == 'battle':
            pokemon_names.append(self.read_text(image, self.sel_rect_5, threshold=False, invert=False, segmentation_mode='--psm 8').strip())
            abilities.append('')
            type_1 = self.read_text(image, self.type_rect_1, threshold=False, invert=True, segmentation_mode='--psm 8').strip().title()
            type_2 = self.read_text(image, self.type_rect_2, threshold=False, invert=True, segmentation_mode='--psm 8').strip().title()
            types.append(type_1+type_2)

        # Identify the Pokemon based on its name and ability/types, where relevant
        for i in range(len(pokemon_names)):
            pokemon_list.append(self.identify_pokemon(pokemon_names[i], abilities[i], types[i]))

        # Return the list of Pokemon
        return pokemon_list
    
    def check_shiny(self) -> bool:
        """Detect whether a Pokemon is shiny by looking for the icon in the summary screen."""
        # Fetch, crop, and threshold image so the red shiny star will appear white and everything else appears black
        img = cv2.cvtColor(self.get_frame(), cv2.COLOR_BGR2HSV)
        h, w, channels = img.shape
        shiny_area = img[round(self.shiny_rect[0][1]*h):round(self.shiny_rect[1][1]*h),
                         round(self.shiny_rect[0][0]*w):round(self.shiny_rect[1][0]*w)]
        # Measure the average value in the shiny star area
        measured_value = cv2.inRange(shiny_area, (0,100,0), (180,255,255)).mean()
        # The shiny star results in a measured_value even greater than 10
        return True if measured_value > 1 else False

    def get_target_ball(self) -> str:
        """Return the name of the Poke Ball needed."""
        return self.base_ball if self.num_caught < 3 else self.legendary_ball

    def check_ball(self) -> str:
        """Detect the currently selected Poke Ball during the catch phase of the game."""
        return self.read_text(self.get_frame(), self.ball_rect, threshold=False, invert=True, language='eng', segmentation_mode='--psm 8').strip()
        
    def record_ball_use(self) -> None:
        """Decrement the number of balls in the inventory and increment the number of pokemon caught."""
        if self.base_ball == self.legendary_ball:
            self.base_balls -= 1
            self.legendary_balls -= 1
        elif self.num_caught < 3:
            self.base_balls -= 1
        else:
            self.legendary_balls -= 1
        self.num_caught += 1

    def check_sufficient_balls(self) -> bool:
        """Calculate whether sufficient balls remain for another run."""
        return False if (self.base_ball == self.legendary_ball and self.base_balls < 4) or (self.base_balls < 3) or (self.legendary_balls < 1) else True

    def calculate_ore_cost(self, num_resets: int) -> int:
        """Calculate the prospective Dynite Ore cost of resetting the game."""
        return 0 if num_resets < 3 else min(10, num_resets)

    def check_sufficient_ore(self, num_resets: int) -> bool:
        """Calculate whether sufficient Dynite Ore remains to quit the run without saving."""
        return True if self.dynite_ore >= self.calculate_ore_cost(num_resets) else False

    def push_buttons(self, *commands: Tuple[str, float]) -> None:
        """Send messages to the microcontroller telling it to press buttons on the Switch."""
        for character, duration in commands:
            self.lock.release()
            if self.exit_flag.is_set():
                sys.exit()
            self.com.write(character)
            time.sleep(duration)
            self.lock.acquire()

    def log(self,
            string: str='') -> None:
        """Print a string to the log file with a timestamp."""
        with open(self.filename, 'a') as file:
            file.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'\t'+string+'\n')
        print(string)
        
    def display_results(self, log=False):
        """Display video from the Switch alongside some annotations describing the run sequence."""
        # Calculate some statistics for display        
        win_percent = None if self.runs == 0 else round(100 * self.wins / self.runs)
        time_per_run = None if self.runs == 0 else (datetime.now() - self.start_date) / self.runs

        # Expand the image with blank space for writing results
        frame = cv2.copyMakeBorder(self.get_frame(stage=self.stage), 0, 0, 0, 200, cv2.BORDER_CONSTANT)
        width = frame.shape[1]

        # Construct arrays of text and values to display
        labels = (
        'Run #', 'Stage: ', 'Base balls: ', 'Legendary balls: ', 'Pokemon caught: ', 'Pokemon: ',
        'Opponent: ', 'Win percentage: ', 'Time per run: ', 'Shinies found: ', 'Dynite Ore: ')
        values = (str(self.runs + 1), self.stage, str(self.base_balls), str(self.legendary_balls),
                str(self.num_caught), str(self.pokemon), str(self.opponent), str(win_percent) + '%', str(time_per_run),
                str(self.shinies_found), str(self.dynite_ore))

        for i in range(len(labels)):
            cv2.putText(frame, labels[i] + values[i], (width - 195, 25 + 25 * i), cv2.FONT_HERSHEY_PLAIN, 1,
                        (255, 255, 255), 2, cv2.LINE_AA)
            if log:
                self.log(labels[i] + values[i])

        # Display
        cv2.imshow('Output', frame)
        if log:
            # Save a copy of the final image
            cv2.imwrite(self.filename[:-8] + '_cap.png', frame)

