#   MaxLairInstance
#       Eric Donders
#       Contributions from Miguel Tavera and Discord users denvoros and pifopi
#       Last updated 2021-01-08
#       Created 2020-11-20

import logging
import pickle
import sys
import time
from datetime import datetime
from typing import List, Tuple, TypeVar, Iterable, Optional, Callable

import cv2
import enchant
import pytesseract

from .pokemon_classes import Pokemon
from .max_lair_instance import MaxLairInstance
from .switch_controller import SwitchController
from serial import Serial
from configparser import ConfigParser
from threading import Lock, Event
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

        # Read values from the config.
        self.boss = config['default']['BOSS'].lower().replace(' ', '-')

        self.base_ball = config['default']['BASE_BALL']
        self.base_balls = int(config['default']['BASE_BALLS'])
        self.legendary_ball = config['default']['LEGENDARY_BALL']
        self.legendary_balls = int(config['default']['LEGENDARY_BALLS'])
        self.mode = config['default']['MODE'].lower()
        self.dynite_ore = int(config['advanced']['DYNITE_ORE'])
        self.data_paths = (
            config['pokemon_data_paths']['Boss_Pokemon'],
            config['pokemon_data_paths']['Rental_Pokemon'],
            config['pokemon_data_paths']['Boss_Matchup_LUT'],
            config['pokemon_data_paths']['Rental_Matchup_LUT'],
            config['pokemon_data_paths']['Rental_Pokemon_Scores']
        )

        self.check_attack_stat = config['stats']['CHECK_ATTACK_STAT'].lower() == 'true'
        self.expected_attack_stats = config['stats']['ATTACK_STATS']
        self.check_speed_stat = config['stats']['CHECK_SPEED_STAT'].lower() == 'true'
        self.expected_speed_stats = config['stats']['SPEED_STATS']


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
        # In-battle Pokemon name & type rectangles.
        self.sel_rect_5 = ((0.195, 0.11), (0.39, 0.165))
        self.type_rect_1 = ((0.24, 0.175), (0.31, 0.21))
        self.type_rect_2 = ((0.35, 0.175), (0.425, 0.21))
        # Dynamax icon rectangle.
        self.dmax_symbol_rect = ((0.58, 0.80), (0.61, 0.84))
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
        # stats rectangles.
        self.attack_stat_rect = ((0.33, 0.29), (0.37, 0.33))
        self.speed_stat_rect = ((0.22, 0.54), (0.26, 0.58))

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
                f'Incorrect value: {config["default"]["BOSS"]} for BOSS '
                'supplied in Config.ini'
            )

    def reset_run(self) -> None:
        """Reset in preparation for a new Dynamax Adventure."""
        self.current_run = MaxLairInstance(self.data_paths)

    def reset_stage(self) -> None:
        """Reset after a battle."""
        self.current_run.reset_stage()

    def get_frame(self, rectangle_set: str = '', resize: bool = False) -> Image:
        """Get an annotated image of the current Switch output."""

        # Get the base image from the base class method.
        img = super().get_frame(resize=resize)

        # Draw rectangles around detection areas if debug logs are on.
        if not self.enable_debug_logs:
            pass
        elif rectangle_set == 'select_pokemon':
            self.outline_regions(
                img, (self.shiny_rect, self.attack_stat_rect, self.speed_stat_rect), (0, 255, 0))
        elif rectangle_set == 'join':
            self.outline_regions(
                img, (self.sel_rect_1, self.sel_rect_2, self.sel_rect_3),
                (0, 255, 0)
            )
            self.outline_regions(
                img, (self.abil_rect_1, self.abil_rect_2, self.abil_rect_3),
                (0, 255, 255)
            )
            self.outline_regions(
                img, (self.moves_rect_1, self.moves_rect_2, self.moves_rect_3),
                (255, 255, 0)
            )
        elif rectangle_set == 'catch':
            self.outline_region(img, self.sel_rect_4, (0, 255, 0))
            self.outline_region(img, self.abil_rect_4, (0, 255, 255))
            self.outline_region(img, self.moves_rect_4, (255, 255, 0))
            self.outline_regions(
                img, (self.ball_rect, self.ball_num_rect), (0, 0, 255)
            )
        elif rectangle_set == 'battle':
            self.outline_region(img, self.sel_rect_5, (0, 255, 0))
            self.outline_regions(
                img, (self.type_rect_1, self.type_rect_2,
                      self.dmax_symbol_rect), (255, 255, 0)
            )
        elif rectangle_set == 'backpacker':
            self.outline_regions(
                img, (self.item_rect_1, self.item_rect_2, self.item_rect_3,
                      self.item_rect_4, self.item_rect_5), (0, 255, 0)
            )

        # Return annotated image.
        return img

    def identify_pokemon(
        self,
        name: str,
        ability: str = '',
        types: str = '',
        moves: str = ''
    ) -> Pokemon:
        """Match OCRed Pokemon to a rental Pokemon."""
        # Strip line breaks from OCRed text and combine name, ability, and types
        # to make a composite identifying string.
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
            # Build the composite identifying string with the same format as the
            # OCRed text.
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

            # Then, update the best match values if the match is better than the
            # previous best match.
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
                self.read_text(image, self.sel_rect_1, threshold=False,
                               invert=True, segmentation_mode='--psm 8').strip()
            )
            pokemon_names.append(self.read_text(
                image, self.sel_rect_2, threshold=False, segmentation_mode='--psm 8').strip())
            # This last name shifts around between runs necessitating a bigger rectangle and different text segmentation mode
            pokemon_names.append(self.read_text(
                image, self.sel_rect_3, threshold=False, segmentation_mode='--psm 3').strip())
            abilities.append(self.read_text(
                image, self.abil_rect_1, threshold=False, invert=True, segmentation_mode='--psm 8').strip())
            abilities.append(self.read_text(
                image, self.abil_rect_2, threshold=False, segmentation_mode='--psm 8').strip())
            abilities.append(self.read_text(
                image, self.abil_rect_3, threshold=False, segmentation_mode='--psm 3').strip())
            types = ['', '', '']
            moves.append(self.read_text(
                image, self.moves_rect_1, threshold=False, segmentation_mode='--psm 4').strip())
            moves.append(self.read_text(
                image, self.moves_rect_2, threshold=False, segmentation_mode='--psm 4').strip())
            moves.append(self.read_text(
                image, self.moves_rect_3, threshold=False, segmentation_mode='--psm 4').strip())
        elif stage == 'catch':
            pokemon_names.append(self.read_text(
                image, self.sel_rect_4, threshold=False, segmentation_mode='--psm 3').strip().split('\n')[-1])
            abilities.append(self.read_text(
                image, self.abil_rect_4, threshold=False, segmentation_mode='--psm 3').strip())
            types.append('')
            moves.append(self.read_text(
                image, self.moves_rect_4, threshold=False, segmentation_mode='--psm 4').strip())
        elif stage == 'battle':
            pokemon_names.append(self.read_text(
                image, self.sel_rect_5, threshold=False, invert=False, segmentation_mode='--psm 8').strip())
            abilities.append('')
            type_1 = self.read_text(image, self.type_rect_1, threshold=False,
                                    invert=True, segmentation_mode='--psm 8').strip().title()
            type_2 = self.read_text(image, self.type_rect_2, threshold=False,
                                    invert=True, segmentation_mode='--psm 8').strip().title()
            types.append(type_1 + type_2)
            moves.append('')

        # Identify the Pokemon based on its name and ability/types, where
        # relevant.
        pokemon_list = []
        for i in range(len(pokemon_names)):
            pokemon_list.append(
                self.identify_pokemon(
                    pokemon_names[i], abilities[i], types[i], moves[i])
            )

        # Return the list of Pokemon.
        return pokemon_list

    def check_shiny(self) -> bool:
        """Detect whether a Pokemon is shiny by looking for the icon in the
        summary screen.
        """

        return self.check_rect_HSV_match(self.shiny_rect, (0, 100, 20),
                                         (180, 255, 255), 10
                                         )

    def check_stats(self) -> bool:
        """Detect whether a Pokemon has perfect stats.
        """

        # First check if the attack stat match one of the expected value
        is_attack_matching = True
        if self.check_attack_stat:
            is_attack_matching = False
            read_attack = self.read_text(self.get_frame(), self.attack_stat_rect, threshold=False, segmentation_mode='--psm 8')
            for expected_attack in self.expected_attack_stats.split(','):
                if expected_attack in read_attack:
                    is_attack_matching = True

            if is_attack_matching:
                self.log(f'Found a legend with the right attack stat : {self.expected_attack_stats}.')
            else:
                self.log('Found legend with the wrong attack stat.')

        # Then check if the speed stat match one of the expected value
        is_speed_matching = True
        if self.check_speed_stat:
            is_speed_matching = False
            read_speed = self.read_text(self.get_frame(), self.speed_stat_rect, threshold=False, segmentation_mode='--psm 8')
            for expected_speed in self.expected_speed_stats.split(','):
                if expected_speed in read_speed:
                    is_speed_matching = True

            if is_speed_matching:
                self.log(f'Found a legend with the right speed stat : {self.expected_speed_stats}.')
            else:
                self.log('Found legend with the wrong speed stat.')

        return is_attack_matching and is_speed_matching

    def check_dynamax_available(self) -> bool:
        """Detect whether Dynamax is available for the player."""
        return self.check_rect_HSV_match(self.dmax_symbol_rect, (0, 0, 200),
                                         (180, 50, 255), 10
                                         )

    def check_defeated(self) -> bool:
        """Detect the black screen that is characteristic of losing the run."""
        if not self.check_rect_HSV_match(((0, 0), (1, 1)), (0, 0, 0),
                                         (180, 255, 10), 250
                                         ):
            return False

        # Pause and check a second time as a rudimentary debounce filter.
        self.push_button(None, 0.2)
        return self.check_rect_HSV_match(((0, 0), (1, 1)), (0, 0, 0),
                                         (180, 255, 10), 250
                                         )

    def get_target_ball(self) -> str:
        """Return the name of the Poke Ball needed."""
        return self.base_ball if self.current_run.num_caught < 3 else self.legendary_ball

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
        elif self.current_run.num_caught < 3:
            self.base_balls -= 1
        else:
            self.legendary_balls -= 1
        self.current_run.num_caught += 1

    def check_sufficient_balls(self) -> bool:
        """Calculate whether sufficient balls remain for another run."""
        return not ((self.base_ball == self.legendary_ball and self.base_balls
                     < 4) or (self.base_balls < 3) or (self.legendary_balls < 1)
                    )

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

    def check_sufficient_ore(self, aditionnal_reset_count: int) -> bool:
        """Calculate whether sufficient Dynite Ore remains to quit the run
        without saving.
        """

        ore_after_resets = self.dynite_ore
        for i in range(aditionnal_reset_count):
            ore_after_resets -= self.calculate_ore_cost(
                self.consecutive_resets + 1 + i)
        return ore_after_resets >= 0

    def record_game_reset(self) -> None:
        """Update ball and Dynite Ore stocks resulting from a game reset."""
        if self.base_ball != self.legendary_ball:
            self.base_balls += min(3, self.current_run.num_caught)
            self.legendary_balls += 1 if self.current_run.num_caught == 4 else 0
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
        for key, value in  {
            'Run #': self.runs + 1, 'Hunting for': self.boss,
            'Stage': self.stage, 'Base balls': self.base_balls,
            'Legendary balls': self.legendary_balls,
            'Pokemon caught': self.current_run.num_caught, 'Lives': self.current_run.lives,
            'Pokemon': self.current_run.pokemon, 'Opponent': self.current_run.opponent,
            'Win percentage': win_percent, 'Time per run': time_per_run,
            'Shinies found': self.shinies_found, 'Dynite Ore': self.dynite_ore, 'Mode': self.mode
        }.items():
            self.info[key] = value

        for i in range(len(self.caught_shinies)):
            self.info[f'Shiny #{i+1}'] = self.caught_shinies[i]

        # Call the base display method.
        super().display_results(image=self.get_frame(resize=True), log=log, screenshot=screenshot)
