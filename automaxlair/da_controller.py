"""Controller object for automating Dynamax Adventures on the Nintendo Switch.
Inherits basic methods from SwitchController and adds others for navigating the
den.
"""

#   MaxLairInstance
#       Eric Donders
#       Contributions from Miguel Tavera and Discord users denvoros and pifopi
#       Last updated 2021-01-08
#       Created 2020-11-20

import re
import pickle

from datetime import datetime
from typing import List, Tuple, TypeVar, Callable, Dict, Optional

import cv2
import enchant

from .pokemon_classes import Pokemon
from .max_lair_instance import MaxLairInstance
from .switch_controller import SwitchController
from configparser import ConfigParser
Image = TypeVar('cv2 image')
Rectangle = Tuple[Tuple[float, float], Tuple[float, float]]


class DAController(SwitchController):
    """An object for storing and processing information related to a Dynamax
    Adventure in Pokemon Sword and Shield: the Crown Tundra.
    """

    def __init__(
        self,
        config: ConfigParser,
        log_name: str,
        actions: Dict[str, Callable]
    ) -> None:

        # Call base class constructor.
        super().__init__(config, log_name, actions)

        # Then, configure everything specific to Dynamax Adventures.
        self.window_name = 'AutoMaxLair Output'

        # Read values from the config.
        self.boss = config['BOSS'].lower().replace(' ', '-')

        self.base_ball = config['BASE_BALL']
        self.base_balls = int(config['BASE_BALLS'])
        self.legendary_ball = config['LEGENDARY_BALL']
        self.legendary_balls = config['LEGENDARY_BALLS']
        self.mode = config['MODE'].lower()
        self.dynite_ore = int(config['advanced']['DYNITE_ORE'])
        self.data_paths = (
            config['pokemon_data_paths']['Boss_Pokemon'],
            config['pokemon_data_paths']['Rental_Pokemon'],
            config['pokemon_data_paths']['Boss_Matchup_LUT'],
            config['pokemon_data_paths']['Rental_Matchup_LUT'],
            config['pokemon_data_paths']['Rental_Pokemon_Scores'],
            config['pokemon_data_paths']['path_tree_path']
        )

        self.check_attack_stat = config['stats']['CHECK_ATTACK_STAT']
        self.expected_attack_stats = config['stats']['ATTACK_STATS']
        # only need to run this assertion if we're checking the attack stat
        if self.check_attack_stat:
            assert 'positive' in self.expected_attack_stats.keys(), "No positive value found in expected attack stats"
            assert 'negative' in self.expected_attack_stats.keys(), "No negative value found in expected attack stats"
            assert 'neutral' in self.expected_attack_stats.keys(), "No neutral value found in expected attack stats"
            assert type(self.expected_attack_stats['positive']) is list, "You must provide multiple values for positive attack stats"
            assert type(self.expected_attack_stats['negative']) is list, "You must provide multiple values for negative attack stats"
            assert type(self.expected_attack_stats['neutral']) is list, "You must provide multiple values for neutral attack stats"

        self.check_speed_stat = config['stats']['CHECK_SPEED_STAT']
        self.expected_speed_stats = config['stats']['SPEED_STATS']
        # only need to run this assertion if we're checking the speed stat
        if self.check_speed_stat:
            assert 'positive' in self.expected_speed_stats.keys(), "No positive value found in expected speed stats"
            assert 'negative' in self.expected_speed_stats.keys(), "No negative value found in expected speed stats"
            assert 'neutral' in self.expected_speed_stats.keys(), "No neutral value found in expected speed stats"
            assert type(self.expected_speed_stats['positive']) is list, "You must provide multiple values for positive speed stats"
            assert type(self.expected_speed_stats['negative']) is list, "You must provide multiple values for negative speed stats"
            assert type(self.expected_speed_stats['neutral']) is list, "You must provide multiple values for neutral speed stats"

        # Initialize starting values.
        self.num_saved_images = 0
        self.runs = 0
        self.wins = 0
        self.shinies_found = 0
        self.caught_shinies: List[str] = []
        self.consecutive_resets = int(config['advanced']['CONSECUTIVE_RESETS'])
        self.reset_run()  # Some values are initialized in here.

        # Define rectangles for checking shininess and reading specific text.
        # Shiny star rectangle.
        self.shiny_rect = ((0.075, 0.53), (0.105, 0.58))
        # Selectable Pokemon names rectangles.
        self.sel_rect_1 = ((0.485, 0.28), (0.60, 0.33))
        self.sel_rect_2 = ((0.485, 0.54), (0.60, 0.59))
        self.sel_rect_3 = ((0.485, 0.80), (0.60, 0.855))
        self.sel_rect_4 = ((0.485, 0.59), (0.60, 0.645))
        # In-battle rectangles.
        self.sel_rect_5 = ((0.195, 0.11), (0.39, 0.165))
        self.type_rect_1 = ((0.24, 0.175), (0.31, 0.21))
        self.type_rect_2 = ((0.35, 0.175), (0.425, 0.21))
        self.menu_rect_1 = ((0.84, 0.685), (0.91, 0.695))
        self.menu_rect_2 = ((0.92, 0.69), (0.98, 0.75))
        self.menu_rect_3 = ((0.82, 0.85), (0.98, 0.88))
        self.menu_rect_4 = ((0.82, 0.93), (0.98, 0.96))
        self.battle_text_rect = ((0.05, 0.805), (0.95, 0.95))
        self.dmax_symbol_rect = ((0.58, 0.805), (0.61, 0.84))
        # In-den rectangles.
        self.den_text_rect = ((0.27, 0.80), (0.72, 0.92))
        self.paths_2_1_rect = ((0.2, 0), (0.4, 1))
        self.paths_2_2_rect = ((0.6, 0), (0.8, 1))
        self.paths_4_1_rect = ((0.1, 0), (0.28, 1))
        self.paths_4_2_rect = ((0.28, 0), (0.5, 1))
        self.paths_4_3_rect = ((0.5, 0), (0.75, 1))
        self.paths_4_4_rect = ((0.75, 0), (1, 1))
        # Selectable Pokemon abilities rectangles.
        self.abil_rect_1 = ((0.485, 0.33), (0.60, 0.39))
        self.abil_rect_2 = ((0.485, 0.59), (0.60, 0.65))
        self.abil_rect_3 = ((0.485, 0.85), (0.60, 0.91))
        self.abil_rect_4 = ((0.485, 0.645), (0.60, 0.69))
        # Selectable Pokemon moves rectangles.
        self.moves_rect_1 = ((0.71, 0.15), (0.91, 0.38))
        self.moves_rect_2 = ((0.71, 0.41), (0.91, 0.64))
        self.moves_rect_3 = ((0.71, 0.67), (0.91, 0.90))
        self.moves_rect_4 = ((0.71, 0.46), (0.91, 0.69))
        # Poke ball rectangles.
        self.ball_rect = ((0.69, 0.63), (0.88, 0.68))
        self.ball_num_rect = ((0.915, 0.63), (0.95, 0.68))
        # Backpacker item rectangles.
        self.item_rect_1 = ((0.549, 0.11), (0.745, 0.16))
        self.item_rect_2 = ((0.549, 0.19), (0.745, 0.24))
        self.item_rect_3 = ((0.549, 0.27), (0.745, 0.32))
        self.item_rect_4 = ((0.549, 0.35), (0.745, 0.40))
        self.item_rect_5 = ((0.549, 0.43), (0.745, 0.48))
        # Stats rectangles.
        self.attack_stat_rect = ((0.33, 0.29), (0.37, 0.33))
        self.attack_label_rect = ((0.31, 0.24), (0.39, 0.29))
        self.speed_stat_rect = ((0.22, 0.54), (0.26, 0.58))
        self.speed_label_rect = ((0.20, 0.58), (0.28, 0.63))

        # Load image assets.
        with open(
            self.config['pokemon_data_paths']['type_icon_path'], 'rb'
        ) as image_file:
            self.type_icons = pickle.load(image_file)

        # Validate starting values.
        if self.mode not in (
            'default', 'strong boss', 'ball saver', 'keep path', 'find path'
        ):
            self.log(
                f'Supplied mode {self.mode} not understood; '
                'using default mode.', 'WARNING'
            )
        if self.boss not in self.current_run.boss_pokemon:
            raise KeyError(
                f'Incorrect value: {config["BOSS"]} for BOSS '
                'supplied in Config.ini'
            )

    def reset_run(self) -> None:
        """Reset in preparation for a new Dynamax Adventure."""
        self.current_run = MaxLairInstance(self.boss, self.data_paths)

    def reset_stage(self) -> None:
        """Reset after a battle."""
        self.current_run.reset_stage()

    def get_frame(
        self,
        rectangle_set: Optional[str] = None,
        resize: bool = False
    ) -> Image:
        """Get an annotated image of the current Switch output."""

        # Get the base image from the base class method.
        img = super().get_frame(resize=resize)

        # Draw rectangles around detection areas if debug logs are on.
        if not self.enable_debug_logs or rectangle_set is None:
            pass
        elif rectangle_set == 'detect':
            self.outline_region(img, self.den_text_rect, (255, 255, 0))
        elif rectangle_set == 'select_pokemon':
            self.outline_regions(
                img, (
                    self.shiny_rect, self.attack_stat_rect,
                    self.attack_label_rect, self.speed_stat_rect,
                    self.speed_label_rect), (0, 255, 0))
        elif rectangle_set == 'join':
            self.outline_regions(
                img, (self.sel_rect_1, self.sel_rect_2, self.sel_rect_3),
                (0, 255, 0))
            self.outline_regions(
                img, (self.abil_rect_1, self.abil_rect_2, self.abil_rect_3),
                (0, 255, 255))
            self.outline_regions(
                img, (self.moves_rect_1, self.moves_rect_2, self.moves_rect_3),
                (255, 255, 0))
        elif rectangle_set == 'catch':
            self.outline_region(img, self.sel_rect_4, (0, 255, 0))
            self.outline_region(img, self.abil_rect_4, (0, 255, 255))
            self.outline_region(img, self.moves_rect_4, (255, 255, 0))
            self.outline_regions(
                img, (self.ball_rect, self.ball_num_rect), (0, 0, 255))
        elif rectangle_set == 'battle':
            self.outline_region(img, self.sel_rect_5, (0, 255, 0))
            self.outline_regions(
                img, (
                    self.type_rect_1, self.type_rect_2, self.menu_rect_1,
                    self.menu_rect_2, self.menu_rect_3, self.menu_rect_4,
                    self.dmax_symbol_rect, self.battle_text_rect
                ), (255, 255, 0))
        elif rectangle_set == 'backpacker':
            self.outline_regions(
                img, (self.item_rect_1, self.item_rect_2, self.item_rect_3,
                      self.item_rect_4, self.item_rect_5), (0, 255, 0))

        # Return annotated image.
        return img

    def read_path_information(
        self,
        stage_index: int
    ) -> None:
        """Read information about the path through the lair. This method should
        be called three times, once at each of the three stages of bosses.
        """

        img = self.get_frame(resize=False)

        # Get a subset of images relevant to the stage index
        images = []
        if stage_index == 1:
            images.append(self.get_image_slice(img, self.paths_2_1_rect))
            images.append(self.get_image_slice(img, self.paths_2_2_rect))
        elif stage_index in (2, 3):
            images.append(self.get_image_slice(img, self.paths_4_1_rect))
            images.append(self.get_image_slice(img, self.paths_4_2_rect))
            images.append(self.get_image_slice(img, self.paths_4_3_rect))
            images.append(self.get_image_slice(img, self.paths_4_4_rect))
        else:
            raise ValueError('Parameter "stage_index" must be 1, 2, or 3')

        type_data = []
        for img in images:
            type_data.append(self.identify_path_pokemon(img))

        # Finally, update the path information with the matched types.
        self.current_run.update_paths(type_data, stage_index)

    def identify_path_pokemon(
        self,
        img: Image
    ) -> Tuple[str, Tuple[float, Tuple[int, int]]]:
        """Read type symbols to idenfity path shape and potential bosses."""
        # Threshold the image the same as the stored type icons.
        img_thresholded = cv2.inRange(
            cv2.cvtColor(img, cv2.COLOR_BGR2HSV), (0, 0, 200), (180, 50, 255))

        # Check every type image for a match within the image
        # TODO: try to look at the shadow of the Pokemon for more hints
        best_match_value = 0
        for type_id in (
            'normal', 'fire', 'water', 'electric', 'grass', 'ice', 'fighting',
            'poison', 'ground', 'flying', 'psychic', 'bug', 'rock', 'ghost',
            'dragon', 'steel', 'dark', 'fairy'
        ):
            result = self.match_template(
                img_thresholded, self.type_icons[type_id])
            # If the result is a better match than the previous type, store it.
            if result[0] > best_match_value:
                best_match_value = result[0]
                match_result = (type_id, result)

        return match_result

    def identify_pokemon(
        self,
        name: str,
        ability: str = '',
        types: str = '',
        moves: str = ''
    ) -> Pokemon:
        """Match OCRed Pokemon to a rental Pokemon."""
        # Strip line breaks from OCRed text and combine name, ability, and
        # types to make a composite identifying string.
        text = (name + ability + types + moves).replace('\n', '')

        # Then, initialize the matched text variable in case it is somehow not
        # assigned later.
        matched_text = ''

        # Thenn initialize values that will store the best match of the OCRed
        # text.
        match_value = 1000

        # Then, loop through all the possible rental pokemon looking for the
        # best match with the OCRed text.
        for pokemon in self.current_run.rental_pokemon.values():
            # Build the composite identifying string with the same format as
            # the OCRed text.
            # Note that some OCR strings omit the ability and others omit the
            # types so don't include these identifiers in these cases.
            string_to_match = pokemon.names[self.lang]
            if ability != '':
                string_to_match += pokemon.abilities[self.lang]
            if types != '':
                for type_name_dict in pokemon.types:
                    string_to_match += type_name_dict[self.lang]
            if moves != '':
                for move in pokemon.moves:
                    string_to_match += move.names.get(self.lang, move.name_id)

            # After building the identifying string, calculate how different it
            # is from the OCRed string.
            distance = enchant.utils.levenshtein(text, string_to_match)

            # Then, update the best match values if the match is better than
            # the previous best match.
            if distance < match_value:
                match_value = distance
                best_match = pokemon
                matched_text = string_to_match

        # Raise a warning if the OCRed text didn't closely match any stored
        # value.
        if match_value > len(text) / 3:
            self.log(
                f'Could not find a good match for Pokemon: "{text}"', 'WARNING'
            )

        self.log(
            f'OCRed Pokemon {text} matched to rental Pokemon {matched_text} '
            f'with distance of {match_value}', 'DEBUG'
        )

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
        moves = []
        if stage == 'join':
            pokemon_names.append(
                self.read_text(
                    image, self.sel_rect_1, threshold=False,
                    invert=True, segmentation_mode='--psm 8').strip()
            )
            pokemon_names.append(
                self.read_text(
                    image, self.sel_rect_2, threshold=False,
                    segmentation_mode='--psm 8'
                ).strip())
            # This last name shifts around between runs necessitating a larger
            # rectangle and different text segmentation mode.
            pokemon_names.append(
                self.read_text(
                    image, self.sel_rect_3, threshold=False,
                    segmentation_mode='--psm 3').strip())
            abilities.append(
                self.read_text(
                    image, self.abil_rect_1, threshold=False, invert=True,
                    segmentation_mode='--psm 8').strip())
            abilities.append(
                self.read_text(
                    image, self.abil_rect_2, threshold=False,
                    segmentation_mode='--psm 8').strip())
            abilities.append(
                self.read_text(
                    image, self.abil_rect_3, threshold=False,
                    segmentation_mode='--psm 3').strip())
            types = ['', '', '']
            moves.append(
                self.read_text(
                    image, self.moves_rect_1, threshold=False,
                    segmentation_mode='--psm 4').strip())
            moves.append(
                self.read_text(
                    image, self.moves_rect_2, threshold=False,
                    segmentation_mode='--psm 4').strip())
            moves.append(
                self.read_text(
                    image, self.moves_rect_3, threshold=False,
                    segmentation_mode='--psm 4').strip())
        elif stage == 'catch':
            pokemon_names.append(
                self.read_text(
                    image, self.sel_rect_4, threshold=False,
                    segmentation_mode='--psm 3').strip().split('\n')[-1])
            abilities.append(
                self.read_text(
                    image, self.abil_rect_4, threshold=False,
                    segmentation_mode='--psm 3').strip())
            types.append('')
            moves.append(
                self.read_text(
                    image, self.moves_rect_4, threshold=False,
                    segmentation_mode='--psm 4').strip())
        elif stage == 'battle':
            pokemon_names.append(
                self.read_text(
                    image, self.sel_rect_5, threshold=False, invert=False,
                    segmentation_mode='--psm 8').strip())
            abilities.append('')
            type_1 = self.read_text(
                image, self.type_rect_1, threshold=False, invert=True,
                segmentation_mode='--psm 8').strip().title()
            type_2 = self.read_text(
                image, self.type_rect_2, threshold=False, invert=True,
                segmentation_mode='--psm 8').strip().title()
            types.append(type_1 + type_2)
            moves.append('')

        # Identify the Pokemon based on its name and ability/types, where
        # relevant.
        pokemon_list = []
        for i in range(len(pokemon_names)):
            pokemon_list.append(
                self.identify_pokemon(
                    pokemon_names[i], abilities[i], types[i], moves[i]))

        # Return the list of Pokemon.
        return pokemon_list

    def read_in_den_state(self) -> Optional[str]:
        """Detect states encountered when traversing the den. Note that this
        function returns the names of actions. If nothing is detected, None is
        returned instead.
        """

        # Get a frame from the VideoCapture that we will check for the state.
        img = self.get_frame()

        # First, check if a battle started.
        if self.check_black_screen(img):
            return 'battle'
        # Otherwise, check for other text.
        if self.check_rect_HSV_match(
            self.den_text_rect, (0, 0, 0,), (180, 55, 255), 220, img
        ):
            text = self.read_text(img, self.den_text_rect, invert=True)
            if re.search(self.phrases['BACKPACKER'], text):
                return 'backpacker'
            if re.search(self.phrases['SCIENTIST'], text):
                return 'scientist'
            if re.search(self.phrases['PATH'], text):
                return 'path'
        # else
        return None

    def read_in_battle_state(self) -> Optional[str]:
        """Detect states encountered within battle, such as the Fight menu
        appearing, a Pokemon fainting, et cetera. If nothing is detected, None
        is returned instead.
        """

        # Get a frame from the VideoCapture that we will check for the state.
        img = self.get_frame()
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # First, check if the player was defeated.
        if self.check_black_screen(img):
            return 'LOSS'
        # Then, check for the presence of the Fight or Cheer menu.
        if self.check_rect_HSV_match(
            self.menu_rect_1, (0, 0, 0), (180, 10, 10), 240, img_hsv, already_HSV=True
        ):
            if self.check_rect_HSV_match(
                self.menu_rect_2, (170, 120, 0), (180, 255, 255), 20, img_hsv, already_HSV=True
            ):
                return 'FIGHT'
            elif self.check_rect_HSV_match(
                self.menu_rect_2, (95, 220, 120), (105, 255, 255), 20, img_hsv, already_HSV=True
            ):
                return 'CHEER'
        # Then, check for the presence of the Catch menu.
        if self.check_rect_HSV_match(
            self.menu_rect_3, (0, 0, 0), (180, 5, 10), 180, img_hsv, already_HSV=True
        ) and self.check_rect_HSV_match(
            self.menu_rect_4, (0, 0, 250), (180, 5, 255), 20, img_hsv, already_HSV=True
        ):
            return 'CATCH'
        # Finally, check for other text.
        if self.check_rect_HSV_match(
            self.battle_text_rect, (0, 0, 0,), (180, 60, 255), 240, img_hsv, already_HSV=True
        ):
            text = self.read_text(img, self.battle_text_rect, invert=True)
            if re.search(self.phrases['FAINT'], text):
                return 'FAINT'
            elif re.search(self.phrases['WEATHER_CLEAR'], text):
                self.current_run.field.set_weather_clear()
                self.log('WEATHER_CLEAR has been detected.', 'DEBUG')
            elif re.search(self.phrases['WEATHER_SUNLIGHT'], text):
                self.current_run.field.set_weather_sunlight()
                self.log('WEATHER_SUNLIGHT has been detected.', 'DEBUG')
            elif re.search(self.phrases['WEATHER_RAIN'], text):
                self.current_run.field.set_weather_rain()
                self.log('WEATHER_RAIN has been detected.', 'DEBUG')
            elif re.search(self.phrases['WEATHER_SANDSTORM'], text):
                self.current_run.field.set_weather_sandstorm()
                self.log('WEATHER_SANDSTORM has been detected.', 'DEBUG')
            elif re.search(self.phrases['WEATHER_HAIL'], text):
                self.current_run.field.set_weather_hail()
                self.log('WEATHER_HAIL has been detected.', 'DEBUG')
            elif re.search(self.phrases['TERRAIN_CLEAR'], text):
                self.current_run.field.set_terrain_clear()
                self.log('TERRAIN_CLEAR has been detected.', 'DEBUG')
            elif re.search(self.phrases['TERRAIN_ELECTRIC'], text):
                self.current_run.field.set_terrain_electric()
                self.log('TERRAIN_ELECTRIC has been detected.', 'DEBUG')
            elif re.search(self.phrases['TERRAIN_GRASSY'], text):
                self.current_run.field.set_terrain_grassy()
                self.log('TERRAIN_GRASSY has been detected.', 'DEBUG')
            elif re.search(self.phrases['TERRAIN_MISTY'], text):
                self.current_run.field.set_terrain_misty()
                self.log('TERRAIN_MISTY has been detected.', 'DEBUG')
            elif re.search(self.phrases['TERRAIN_PSYCHIC'], text):
                self.current_run.field.set_terrain_psychic()
                self.log('TERRAIN_PSYCHIC has been detected.', 'DEBUG')
        return None

    def check_shiny(self) -> bool:
        """Detect whether a Pokemon is shiny by looking for the icon in the
        summary screen.
        """

        return self.check_rect_HSV_match(
            self.shiny_rect, (0, 100, 20), (180, 255, 255), 10)

    def check_stats(self) -> bool:
        """Detect whether a Pokemon has perfect stats.
        """

        # First check if the attack stat match one of the expected value
        is_attack_matching = True
        if self.check_attack_stat:
            is_attack_matching = False
            read_attack = self.read_text(
                self.get_frame(), self.attack_stat_rect, threshold=False,
                segmentation_mode='--psm 8'
            )
            for nature_type, expected_attacks in self.expected_attack_stats.items():
                nature_plus_expected = False if nature_type != 'positive' else True
                nature_minus_expected = False if nature_type != 'negative' else True
                
                # then iterate through the stats
                for expected_attack in expected_attacks:
                    expected_attack = str(expected_attack)
                
                    if expected_attack in read_attack:
                        if (
                            (nature_minus_expected and self.check_rect_HSV_match(
                                self.attack_label_rect, (80, 30, 0),
                                (110, 255, 255), 10)) or (
                                nature_plus_expected and self.check_rect_HSV_match(
                                    self.attack_label_rect, (150, 30, 0),
                                    (180, 255, 255), 10)
                            )
                            or (
                                not nature_minus_expected
                                and not nature_plus_expected)
                        ):
                            is_attack_matching = True

            if is_attack_matching:
                self.log(
                    'Found a legend with the right attack stat : '
                    f'{self.expected_attack_stats}.')
            else:
                self.log('Found legend with the wrong attack stat.')

        # Then check if the speed stat match one of the expected value
        is_speed_matching = True
        if self.check_speed_stat:
            is_speed_matching = False
            read_speed = self.read_text(
                self.get_frame(), self.speed_stat_rect, threshold=False,
                segmentation_mode='--psm 8'
            )
            for nature_type, expected_speeds in self.expected_speed_stats.items():
                nature_plus_expected = False if nature_type != 'positive' else True
                nature_minus_expected = False if nature_type != 'negative' else True
            
                for expected_speed in expected_speeds:
                    expected_speed = str(expected_speed)
                    if expected_speed in read_speed:
                        if (
                            (nature_minus_expected and self.check_rect_HSV_match(
                                self.speed_label_rect, (80, 30, 0),
                                (110, 255, 255), 10))
                            or (nature_plus_expected and self.check_rect_HSV_match(
                            self.speed_label_rect, (150, 30, 0),
                            (180, 255, 255), 10))
                            or (
                            not nature_minus_expected
                            and not nature_plus_expected)
                        ):
                            is_speed_matching = True

            if is_speed_matching:
                self.log(
                    'Found a legend with the right speed stat : '
                    f'{self.expected_speed_stats}.')
            else:
                self.log('Found legend with the wrong speed stat.')

        return is_attack_matching and is_speed_matching

    def check_dynamax_available(self) -> bool:
        """Detect whether Dynamax is available for the player."""
        return self.check_rect_HSV_match(
            self.dmax_symbol_rect, (0, 0, 200), (180, 50, 255), 10)

    def check_black_screen(self, img: Image = None) -> bool:
        """Detect the black screen that is characteristic of losing the run."""
        if not self.check_rect_HSV_match(
            ((0, 0), (1, 1)), (0, 0, 0), (180, 255, 10), 250, img
        ):
            return False

        # Pause and check a second time as a rudimentary debounce filter.
        self.push_button(None, 0.2)
        return self.check_rect_HSV_match(
            ((0, 0), (1, 1)), (0, 0, 0), (180, 255, 10), 250)

    def get_target_ball(self) -> str:
        """Return the name of the Poke Ball needed."""
        return (
            self.base_ball if self.current_run.num_caught < 3
            else self.legendary_ball)

    def check_ball(self) -> str:
        """Detect the currently selected Poke Ball during the catch phase of the
        game.
        """

        return self.read_text(
            self.get_frame(), self.ball_rect, threshold=False, invert=True,
            segmentation_mode='--psm 7').strip()

    def record_ball_use(self) -> None:
        """Decrement the number of balls in the inventory and increment the
        number of pokemon caught.
        """

        if self.base_ball == self.legendary_ball:
            self.base_balls -= 1
            self.legendary_balls -= 1
        elif self.current_run.num_caught < 3:
            self.base_balls -= 1
        else:
            self.legendary_balls -= 1
        self.current_run.num_caught += 1

    def check_sufficient_balls(self) -> bool:
        """Calculate whether sufficient balls remain for another run."""
        return not (
            (self.base_ball == self.legendary_ball and self.base_balls < 4)
            or (self.base_balls < 3) or (self.legendary_balls < 1))

    def record_ore_reward(self) -> None:
        """Award Dynite Ore depending on how the run went."""
        self.consecutive_resets = 0
        if self.current_run.lives == 0:
            self.dynite_ore += self.current_run.num_caught
        else:
            self.dynite_ore += 6 + (2 if self.current_run.lives == 4 else 0)
        self.dynite_ore = min(self.dynite_ore, 999)

    def calculate_ore_cost(self, num_resets: int) -> int:
        """Calculate the prospective Dynite Ore cost of resetting the game."""
        return 0 if num_resets < 3 else min(10, num_resets)

    def check_sufficient_ore(self, additionnal_reset_count: int) -> bool:
        """Calculate whether sufficient Dynite Ore remains to quit the run
        without saving.
        """

        # If the ore cost of resetting is zero, resett regardless of the ore
        # count.
        if self.calculate_ore_cost(
            self.consecutive_resets + additionnal_reset_count
        ) == 0:
            return True
        # Otherwise, calculate whether the ore amount would still be positive
        # after resetting.
        ore_after_resets = self.dynite_ore
        for i in range(additionnal_reset_count):
            ore_after_resets -= self.calculate_ore_cost(
                self.consecutive_resets + 1 + i)
        return ore_after_resets >= 0

    def record_game_reset(self) -> None:
        """Update ball and Dynite Ore stocks resulting from a game reset."""
        if self.base_ball != self.legendary_ball:
            self.base_balls += min(3, self.current_run.num_caught)
            self.legendary_balls += (
                1 if self.current_run.num_caught == 4 else 0)
        else:
            self.base_balls += self.current_run.num_caught
            self.legendary_balls += self.current_run.num_caught
        self.consecutive_resets += 1
        ore_cost = self.calculate_ore_cost(self.consecutive_resets)
        self.dynite_ore -= ore_cost
        self.log(
            f'Spending {ore_cost} dynite ore after {self.consecutive_resets}'
            ' reset.', 'DEBUG'
        )

    def display_results(self, log: bool = False, screenshot: bool = False):
        """Display video from the Switch alongside some annotations describing
        the run sequence.
        """

        # Calculate some statistics for display
        win_percent = (
            'N/A' if self.runs == 0 else (
                str(round(100 * self.wins / self.runs)) + '%'
            )
        )
        time_per_run = (
            'N/A' if self.runs == 0 else str((datetime.now() - self.start_date)
                                             / self.runs)[2:7]
        )

        # Construct the dictionary that will be displayed by the base method.
        for key, value in {
            'Run #': self.runs + 1,
            'Hunting for': self.boss,
            'Mode': self.mode,
            'Stage': self.stage,
            'Base balls': self.base_balls,
            'Legendary balls': self.legendary_balls,
            'Dynite Ore': self.dynite_ore,
            'Pokemon caught': self.current_run.num_caught,
            'Lives': self.current_run.lives,
            'Pokemon': self.current_run.pokemon,
            'Opponent': self.current_run.opponent,
            'Win percentage': win_percent,
            'Time per run': time_per_run,
            'Shinies found': self.shinies_found
        }.items():
            self.info[key] = value

        for i in range(len(self.caught_shinies)):
            self.info[f'Shiny #{i+1}'] = self.caught_shinies[i]

        # Call the base display method.
        super().display_results(
            image=self.get_frame(
                rectangle_set=self.stage, resize=True), log=log,
            screenshot=screenshot)
        
    def get_stats_for_discord(self) -> dict:
        """This method takes information from the run and returns a nice dictionary
        for embedding to Discord
        
        increment_one is only for a win with a shiny, so that we can get the nice
        status screen with the screenshot.
        """

        the_dict = {
            "Boss": self.boss,
            "Wins/Runs": f"{self.wins}/{self.runs}",
            "Base Balls": self.base_balls,
            "Legendary Balls": self.legendary_balls,
            "Dynite Ore": self.dynite_ore,
        }

        if self.shinies_found > 0:
            the_dict["Shinies Found"] = self.shinies_found
        
        return the_dict
