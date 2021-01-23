#   MaxLairInstance
#       Eric Donders
#       Contributions from Miguel Tavera and Discord users denvoros and pirofpi
#       Last updated 2021-01-08
#       Created 2020-11-20

import cv2
import time
import pytesseract
import enchant
import pickle
import sys
from datetime import datetime
from typing import TypeVar, Dict, List, Tuple
Pokemon = TypeVar('Pokemon')
Move = TypeVar('Move')
Serial = TypeVar('serial.Serial')
VideoCapture = TypeVar('cv2.VideoCapture')
DateTime = TypeVar('datetime.datetime')
Image = TypeVar('cv2 image')


class MaxLairInstance():
    """An object for storing and processing information related to a Dynamax
    Adventure in Pokemon Sword and Shield: the Crown Tundra.
    """
    def __init__(
        self,
        boss: str,
        balls: int,
        com: Serial,
        cap: VideoCapture,
        video_scale: float,
        lock,
        exit_flag,
        datetime: DateTime,
        data_paths: Tuple[str],
        phrases: Dict[str, str],
        mode: str,
        dynite_ore: int,
        stage: str='join'
     ) -> None:
        self.data_paths = data_paths
        self.phrases = phrases
        self.tesseract_language = phrases['TESSERACT_LANG_NAME']
        self.lang = phrases['DATA_LANG_NAME']
        self.reset_run()
        
        self.start_date = datetime
        self.filename = ''.join(('logs//',boss,'_',datetime.strftime('%Y-%m-%d %H-%M-%S'),'_log.txt'))
        self.boss = boss.lower().replace(' ', '-')
        self.base_ball, self.base_balls, self.legendary_ball, self.legendary_balls = balls
        self.mode = mode
        self.dynite_ore = dynite_ore
        self.stage = stage
        self.num_saved_images = 0

        self.runs = 0
        self.wins = 0
        self.shinies_found = 0
        self.caught_shinies = []
        self.consecutive_resets = 0

        # Video capture and serial communication objects
        self.cap = cap
        self.base_resolution = (1920, 1080)
        self.display_resolution = (round(1920*video_scale), round(1080*video_scale))
        self.cap.set(3, self.base_resolution[0])
        self.cap.set(4, self.base_resolution[1])
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
        self.sel_rect_5 = ((0.195,0.11), (0.39,0.165))
        self.type_rect_1 = ((0.24,0.175), (0.31,0.21))
        self.type_rect_2 = ((0.35,0.175), (0.425,0.21))
        # Dynamax icon rectangle
        self.dmax_symbol_rect = ((0.58, 0.80), (0.61 ,0.84))
        # Selectable Pokemon abilities rectangles
        self.abil_rect_1 = ((0.485,0.33), (0.60,0.39))
        self.abil_rect_2 = ((0.485,0.59), (0.60,0.65))
        self.abil_rect_3 = ((0.485,0.85), (0.60,0.91))
        self.abil_rect_4 = ((0.485,0.645), (0.60,0.69))
        # Poke ball rectangle
        self.ball_rect = ((0.69,0.63), (0.88,0.68))
        self.ball_num_rect = ((0.915,0.63), (0.95,0.68))
        # Backpacker
        self.item_rect_1 = ((0.549,0.1270), (0.745,0.1770)) 
        self.item_rect_2 = ((0.549,0.2035), (0.745,0.2535))
        self.item_rect_3 = ((0.549,0.2800), (0.745,0.3300))
        self.item_rect_4 = ((0.549,0.3565), (0.745,0.4065))
        self.item_rect_5 = ((0.549,0.4330), (0.745,0.4830))

    def reset_run(self) -> None:
        """Reset in preparation for a new Dynamax Adventure."""
        self.pokemon = None
        self.HP = 1  # 1 = 100%
        self.num_caught = 0
        self.caught_pokemon = []
        self.lives = 4
        self.reset_stage()
        # Load precalculated resources for choosing Pokemon and moves
        self.boss_pokemon = pickle.load(open(self.data_paths[0], 'rb'))
        self.rental_pokemon = pickle.load(open(self.data_paths[1], 'rb'))
        self.boss_matchups = pickle.load(open(self.data_paths[2], 'rb'))
        self.rental_matchups = pickle.load(open(self.data_paths[3], 'rb'))
        self.rental_scores = pickle.load(open(self.data_paths[4], 'rb'))
        
    def reset_stage(self) -> None:
        """Reset after a battle."""
        self.move_index = 0
        self.dmax_timer = -1
        self.opponent = None
        self.dynamax_available = False
        if self.pokemon is not None:
            if self.pokemon.name_id == 'ditto':
                self.pokemon = self.rental_pokemon['ditto']
            self.pokemon.dynamax = False
        
    def get_frame(self, stage: str='') -> Image:
        """Get an annotated image of the current Switch output."""
        ret, img = self.cap.read()

        if not ret:
            self.log('ERROR: failed to read frame from VideoCapture.')

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
            cv2.rectangle(img, (round(self.ball_num_rect[0][0]*w)-2,round(self.ball_num_rect[0][1]*h)-2),
                          (round(self.ball_num_rect[1][0]*w)+2,round(self.ball_num_rect[1][1]*h)+2), (0,0,255), 2)
        elif stage == 'battle':
            cv2.rectangle(img, (round(self.sel_rect_5[0][0]*w)-2,round(self.sel_rect_5[0][1]*h)-2),
                          (round(self.sel_rect_5[1][0]*w)+2,round(self.sel_rect_5[1][1]*h)+2), (0,255,0), 2)
            cv2.rectangle(img, (round(self.type_rect_1[0][0]*w)-2,round(self.type_rect_1[0][1]*h)-2),
                          (round(self.type_rect_1[1][0]*w)+2,round(self.type_rect_1[1][1]*h)+2), (255,255,0), 2)
            cv2.rectangle(img, (round(self.type_rect_2[0][0]*w)-2,round(self.type_rect_2[0][1]*h)-2),
                          (round(self.type_rect_2[1][0]*w)+2,round(self.type_rect_2[1][1]*h)+2), (255,255,0), 2)
            cv2.rectangle(img, (round(self.dmax_symbol_rect[0][0]*w)-2,round(self.dmax_symbol_rect[0][1]*h)-2),
                          (round(self.dmax_symbol_rect[1][0]*w)+2,round(self.dmax_symbol_rect[1][1]*h)+2), (255,255,0), 2)
        elif stage == 'backpacker':
            cv2.rectangle(img, (round(self.item_rect_1[0][0]*w)-2,round(self.item_rect_1[0][1]*h)-2),
                          (round(self.item_rect_1[1][0]*w)+2,round(self.item_rect_1[1][1]*h)+2), (0,255,0), 2)
            cv2.rectangle(img, (round(self.item_rect_2[0][0]*w)-2,round(self.item_rect_2[0][1]*h)-2),
                          (round(self.item_rect_2[1][0]*w)+2,round(self.item_rect_2[1][1]*h)+2), (0,255,0), 2)
            cv2.rectangle(img, (round(self.item_rect_3[0][0]*w)-2,round(self.item_rect_3[0][1]*h)-2),
                          (round(self.item_rect_3[1][0]*w)+2,round(self.item_rect_3[1][1]*h)+2), (0,255,0), 2)
            cv2.rectangle(img, (round(self.item_rect_4[0][0]*w)-2,round(self.item_rect_4[0][1]*h)-2),
                          (round(self.item_rect_4[1][0]*w)+2,round(self.item_rect_4[1][1]*h)+2), (0,255,0), 2)
            cv2.rectangle(img, (round(self.item_rect_5[0][0]*w)-2,round(self.item_rect_5[0][1]*h)-2),
                          (round(self.item_rect_5[1][0]*w)+2,round(self.item_rect_5[1][1]*h)+2), (0,255,0), 2)

        # Return and annotated image.
        return img

    def read_text(
        self,
        img: Image,
        section: Tuple[Tuple[float, float], Tuple[float, float]]=((0,0),(1,1)),
        threshold: bool=True,
        invert: bool=False,
        segmentation_mode: str='--psm 11'
    ) -> str:
        """Read text from a section (default entirety) of an image using Tesseract."""
        # Process image according to instructions
        h, w = img.shape[:2]
        if threshold:
            img = cv2.inRange(cv2.cvtColor(img, cv2.COLOR_BGR2HSV), (0,0,100), (180,15,255))
        if invert:
            img = cv2.bitwise_not(img)
        img = img[round(section[0][1]*h):round(section[1][1]*h),
                  round(section[0][0]*w):round(section[1][0]*w)]
        #cv2.imshow('Text Area', img) # DEBUG

        # Then, read text using Tesseract.
        # Note that we need to check for the main thread exiting here.
        if self.exit_flag.is_set():
            sys.exit()
        # We release the lock so that the display thread can continue while
        # Tesseract processes the image.
        self.lock.release()
        text = pytesseract.image_to_string(
            img, lang=self.tesseract_language, config=segmentation_mode
        )
        self.lock.acquire()

        # Finally, return the OCRed text.
        return text

    def identify_pokemon(
        self,
        name: str,
        ability: str='',
        types: str=''
    ) -> Pokemon:
        """Match OCRed Pokemon to a rental Pokemon."""
        # Strip line breaks from OCRed text and combine name, ability, and types
        # to make a composite identifying string.
        text = (name+ability+types).replace('\n','')

        # Then, initialize the matched text variable in case it is somehow not
        # assigned later.
        matched_text = ''

        # Thenn initialize values that will store the best match of the OCRed
        # text.
        best_match = None
        match_value = 1000

        # Then, loop through all the possible rental pokemon looking for the
        # best match with the OCRed text.
        for pokemon in self.rental_pokemon.values():
            # Build the composite identifying string with the same format as the
            # OCRed text.
            # Note that some OCR strings omit the ability and others omit the
            # types so don't include these identifiers in these cases.
            string_to_match = pokemon.names[self.lang]  #.split(' (')[0]
            if ability != '':
                string_to_match += pokemon.abilities[self.lang]
            if types != '':
                for type_name_dict in pokemon.types:
                    string_to_match += type_name_dict[self.lang]

            # After building the identifying string, calculate how different it
            # is from the OCRed string.
            distance = enchant.utils.levenshtein(text, string_to_match)

            # Then, update the best match values if the match is better than the
            # previous best match.
            if distance < match_value:
                match_value = distance
                best_match = pokemon
                matched_text = string_to_match

        # Raise a warning if the OCRed text didn't closely match any stored
        # value.
        if match_value > len(text)/3:
            self.log(f'WARNING: could not find a good match for Pokemon: "{text}"')


        self.log(f'OCRed Pokemon {text} matched to rental Pokemon {matched_text} with distance of {match_value}')  # DEBUG

        # finally, return the Pokemon that matched best with the OCRed text
        return best_match

    def read_selectable_pokemon(self, stage: str) -> List[Pokemon]:
        """Return a list of available Pokemon names."""
        # Fetch the image from the Switch output.
        image = self.get_frame()

        # Get a list of Pokemon names present, depending on stage.
        pokemon_names = []
        abilities = []
        types = []
        if stage == 'join':
            pokemon_names.append(
                self.read_text(image, self.sel_rect_1, threshold=False,
                invert=True, segmentation_mode='--psm 8').strip()
            )
            pokemon_names.append(self.read_text(image, self.sel_rect_2, threshold=False, segmentation_mode='--psm 8').strip())
            pokemon_names.append(self.read_text(image, self.sel_rect_3, threshold=False, segmentation_mode='--psm 3').strip()) # This last name shifts around between runs necessitating a bigger rectangle and different text segmentation mode
            abilities.append(self.read_text(image, self.abil_rect_1, threshold=False, invert=True, segmentation_mode='--psm 8').strip())
            abilities.append(self.read_text(image, self.abil_rect_2, threshold=False, segmentation_mode='--psm 8').strip())
            abilities.append(self.read_text(image, self.abil_rect_3, threshold=False, segmentation_mode='--psm 3').strip())
            types = ['','','']
        elif stage == 'catch':
            pokemon_names.append(self.read_text(image, self.sel_rect_4, threshold=False, segmentation_mode='--psm 3').strip().split('\n')[-1])
            abilities.append(self.read_text(image, self.abil_rect_4, threshold=False, segmentation_mode='--psm 3').strip())
            types.append('')
        elif stage == 'battle':
            pokemon_names.append(self.read_text(image, self.sel_rect_5, threshold=False, invert=False, segmentation_mode='--psm 8').strip())
            abilities.append('')
            type_1 = self.read_text(image, self.type_rect_1, threshold=False, invert=True, segmentation_mode='--psm 8').strip().title()
            type_2 = self.read_text(image, self.type_rect_2, threshold=False, invert=True, segmentation_mode='--psm 8').strip().title()
            types.append(type_1 + type_2)

        # Identify the Pokemon based on its name and ability/types, where
        # relevant.
        pokemon_list = []
        for i in range(len(pokemon_names)):
            pokemon_list.append(
                self.identify_pokemon(pokemon_names[i], abilities[i], types[i])
            )

        # Return the list of Pokemon.
        return pokemon_list

    def check_rect_HSV_match(
        self,
        rect: Tuple[Tuple[float, float], Tuple[float, float]],
        lower_threshold: Tuple[int, int, int],
        upper_threshold: Tuple[int, int, int],
        mean_value_threshold: int
    ) -> bool:
        """Check a specified section of the screen for values within a certain
        HSV range.
        """
        
        # Fetch, convert, crop, and threshold image so the feature of interest
        # is white (value 255) and everything else appears black (0)
        img = cv2.cvtColor(self.get_frame(), cv2.COLOR_BGR2HSV)
        h, w = img.shape[:2]
        cropped_area = img[round(rect[0][1]*h):round(rect[1][1]*h),
                         round(rect[0][0]*w):round(rect[1][0]*w)]
        measured_value = cv2.inRange(cropped_area, lower_threshold,
            upper_threshold).mean()

        # Return True if the mean value is above the supplied threshold
        return measured_value > mean_value_threshold
    
    def check_shiny(self) -> bool:
        """Detect whether a Pokemon is shiny by looking for the icon in the
        summary screen.
        """
        return self.check_rect_HSV_match(self.shiny_rect, (0,100,20),
            (180,255,255), 10
        )

    def check_dynamax_available(self) -> bool:
        """Detect whether Dynamax is available for the player."""
        return self.check_rect_HSV_match(self.dmax_symbol_rect, (0, 0, 200),
            (180, 50, 255), 10
        )

    def check_defeated(self) -> bool:
        """Detect the black screen that is characteristic of losing the run."""
        if not self.check_rect_HSV_match(((0,0), (1,1)), (0,0,0),
            (180,255,10), 250
        ):
            return False

        # Pause and check a second time as a rudimentary debounce filter.
        self.push_buttons((b'0', 0.2))
        return self.check_rect_HSV_match(((0,0), (1,1)), (0,0,0),
            (180,255,10), 250
        )

    def get_target_ball(self) -> str:
        """Return the name of the Poke Ball needed."""
        return self.base_ball if self.num_caught < 3 else self.legendary_ball

    def check_ball(self) -> str:
        """Detect the currently selected Poke Ball during the catch phase of the
        game.
        """

        return self.read_text(self.get_frame(), self.ball_rect, threshold=False,
            invert=True, segmentation_mode='--psm 8').strip()
        
    def record_ball_use(self) -> None:
        """Decrement the number of balls in the inventory and increment the
        number of pokemon caught.
        """

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
        return not ((self.base_ball == self.legendary_ball and self.base_balls
            < 4) or (self.base_balls < 3) or (self.legendary_balls < 1)
        )

    def record_ore_reward(self) -> None:
        """Award Dynite Ore depending on how the run went."""
        self.consecutive_resets = 0
        self.dynite_ore += (self.num_caught + (2 if self.num_caught == 4 else 0)
            + (2 if self.lives == 4 else 0)
        )
        self.dynite_ore = min(self.dynite_ore, 999)

    def calculate_ore_cost(self, num_resets: int) -> int:
        """Calculate the prospective Dynite Ore cost of resetting the game."""
        return 0 if num_resets < 3 else min(10, num_resets)

    def check_sufficient_ore(self, aditionnal_reset_count: int) -> bool:
        """Calculate whether sufficient Dynite Ore remains to quit the run without saving."""
        ore_after_resets = self.dynite_ore
        for i in range(aditionnal_reset_count):
            ore_after_resets -= self.calculate_ore_cost(self.consecutive_resets + 1 + i)
        return ore_after_resets >= 0
    
    def record_game_reset(self) -> None:
        """Update ball and Dynite Ore stocks resulting from a game reset."""
        if self.base_ball != self.legendary_ball:
            self.base_balls += min(3, self.num_caught)
            self.legendary_balls += 1 if self.num_caught == 4 else 0
        else:
            self.base_balls += self.num_caught
            self.legendary_balls += self.num_caught
        self.consecutive_resets += 1
        self.dynite_ore -= self.calculate_ore_cost(self.consecutive_resets)

    def push_button(self, character: str, duration: float) -> None:
        """Send a message to the microcontroller telling it to press buttons on
        the Switch.
        """

        # Check whether the main thread has called for the button pushing
        # thread to terminate.
        if self.exit_flag.is_set():
            sys.exit()

        # DEBUG: check for interruption of video feed while trying to send a
        # command.
        if self.check_rect_HSV_match(((0,0), (1,1)), (0,0,0),
            (180,255,10), 250
        ):
            self.log('WARNING: Loss of video detected while sending command.')

        # Then we release the lock so the display thread can run while we
        # complete the button press and subsequent delay.
        self.lock.release()

        # Clear extra characters from the serial buffer.
        while self.com.in_waiting > 0:
            self.log(f'WARNING: Unexpected byte received: "{self.com.read()}"')
        
        if character is not None:
            # Send the command to the microcontroller using the serial port.
            self.com.write(character)
            # Check whether the microcontroller successfully echoed back the
            # command, and raise a warning if it did not.
            response = self.com.read()
            if response != character:
                self.log(
                    f'WARNING: Received "{response}" instead of sent command "{character}".'
                )

        # Delay for the specified time.
        time.sleep(duration)

        # Reacquire the lock before the next iteration.
        # This step is needed here because calling sys.exit() in a
        # subsequent command will attempt to release the lock.
        self.lock.acquire()

    def push_buttons(self, *commands: Tuple[str, float]) -> None:
        """Send a sequence of messages to the microcontroller telling it to
        press buttons on the Switch.
        """

        # Commands are supplied as tuples consisting of a character
        # corresponding to a button push and a delay that follows the push.
        for character, duration in commands:
            self.push_button(character, duration)

    def log(self,
            string: str='') -> None:
        """Print a string to the log file with a timestamp."""
        with open(self.filename, 'a', encoding='utf-8') as file:
            file.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'\t'+string+'\n')
        print(string)
        
    def display_results(self, log=False, screenshot=False):
        """Display video from the Switch alongside some annotations describing the run sequence."""
        # Calculate some statistics for display        
        win_percent = 'N/A' if self.runs == 0 else round(100 * self.wins / self.runs)
        time_per_run = 'N/A' if self.runs == 0 else str((datetime.now() - self.start_date) / self.runs)[2:7]

        # Expand the image with blank space for writing results
        frame = cv2.copyMakeBorder(cv2.resize(self.get_frame(stage=self.stage), self.display_resolution), 0, 0, 0, 250, cv2.BORDER_CONSTANT)
        width = frame.shape[1]

        # Construct arrays of text and values to display
        labels = [
        'Run #', 'Hunting for: ', 'Stage: ', 'Base balls: ', 'Legendary balls: ', 'Pokemon caught: ', 'Lives: ', 'Pokemon: ',
        'Opponent: ', 'Win percentage: ', 'Time per run: ', 'Shinies found: ', 'Dynite Ore: ']
        values = [str(self.runs + 1), self.boss, self.stage, str(self.base_balls), str(self.legendary_balls),
                str(self.num_caught), str(self.lives), str(self.pokemon), str(self.opponent), str(win_percent) + '%', time_per_run,
                str(self.shinies_found), str(self.dynite_ore)]

        for i in range(len(self.caught_shinies)):
            labels.append('shiny #' + str(i) + ': ')
            values.append(self.caught_shinies[i])

        for i in range(len(labels)):
            cv2.putText(frame, labels[i] + values[i], (width - 245, 25 + 25 * i), cv2.FONT_HERSHEY_PLAIN, 1,
                        (255, 255, 255), 2, cv2.LINE_AA)
            if log:
                self.log(labels[i] + values[i])

        # Display
        cv2.imshow('Output', frame)
        
        if log or screenshot:
            # Save a screenshot
            self.num_saved_images += 1
            cv2.imwrite(self.filename[:-8] + '_cap_'+str(self.num_saved_images)+'.png', frame)
