"""Script for soft resetting to get 0 Atk IVs on gift Pokemon

This script was developed for the Poipole available in the Max Lair and may not
work for other gift Pokemon.

Instructions:
1. Your Pokemon icon must be in its default position in the menu (top row,
   second column).
2. Navigate to a box in your PC that has an opening in the default cursor
   position (top left corner of the box).
3. Press the '+' button until the IVs of Pokemon in your boxes are shown.
4. Save directly in front of the Poipole.
5. Connect the microcontroller, serial connection, and capture card, then start
   the script.
"""

import logging
import os
import sys
from datetime import datetime
from typing import Dict, Callable, Optional, TypeVar

import pytesseract
import toml

# We need to import some class definitions from the parent directory.
from os.path import dirname, abspath
base_dir = dirname(dirname(abspath(__file__)))
sys.path.insert(1, base_dir)
sys.path.insert(1, os.path.join(base_dir, 'automaxlair'))

import automaxlair

Image = TypeVar('cv2 image')


# load configuration from the config file
try:
    config = toml.load("Config.toml")
except FileNotFoundError:
    raise FileNotFoundError(
        "The Config.toml file was not found! Be sure to copy Config.sample.toml as Config.toml and edit it!")
except:
    raise SyntaxError(
        "Something went wrong parsing Config.toml\n" +
        "Please make sure you entered the information right " +
        "and did not modify \" or . symbols or have uppercase true or false in the settings.")

COM_PORT = config['COM_PORT']
VIDEO_INDEX = config['VIDEO_INDEX']
VIDEO_EXTRA_DELAY = config['advanced']['VIDEO_EXTRA_DELAY']
pytesseract.pytesseract.tesseract_cmd = config['TESSERACT_PATH']
ENABLE_DEBUG_LOGS = config['advanced']['ENABLE_DEBUG_LOGS']

# Set the log name
LOG_NAME = f"auto_gift_pokemon_{datetime.now().strftime('%Y-%m-%d %H-%M-%S')}"


class AutoGiftPokemonController(
    automaxlair.switch_controller.SwitchController
):
    """Switch controller specific to resetting for 0 Atk gift Pokemon."""
    def __init__(
        self,
        config_,
        log_name: str,
        actions: Dict[str, Callable]
    ) -> None:

        # Call base class constructor.
        super().__init__(config_, log_name, actions)

        self.resets = 0

        # Rectangles for OCR and display
        self.IV_atk_rect = ((0.78, 0.25), (0.9, 0.30))
        self.IV_spa_rect = ((0.78, 0.35), (0.9, 0.4))
    
    def get_frame(
        self,
        rectangle_set: Optional[str] = None,
        resize: bool = False
    ) -> Image:
        """Get an annotated image of the current Switch output."""

        # Get the base image from the base class method.
        img = super().get_frame(resize=resize)
        if rectangle_set is not None:
            self.outline_region(img, self.IV_atk_rect, (0, 255, 0))

        return img

    def display_results(self, log: bool = False, screenshot: bool = False):
        """Display video from the Switch alongside some annotations describing
        the run sequence.
        """

        # Construct the dictionary that will be displayed by the base method.
        for key, value in {
            'Resets: ': self.resets,
        }.items():
            self.info[key] = value

        # Call the base display method.
        super().display_results(
            image=self.get_frame(
                rectangle_set=self.stage, resize=True), log=log,
            screenshot=screenshot)


def initialize(ctrlr) -> None:
    """Executed once at the beginning of the sequence."""
    # assume we're starting from the select controller menu, connect, then
    # press home twice to return to the game
    ctrlr.push_buttons(
        (b'a', 2), (b'h', 2.0), (b'h', 2.0), (b'b', 1.5), (b'b', 1.5)
    )
    return 'loop'


def loop(ctrlr) -> None:
    """Main sequence that is repeated once per cycle."""
    # Take the gift Pokemon and navigate to its IV summary.
    ctrlr.push_buttons(
        (b'b', 1), (b'a', 1), (b'a', 1), (b'a', 1), (b'a', 1), (b'a', 1),
        (b'a', 1), (b'a', 1), (b'a', 1), (b'a', 1), (b'a', 1), (b'a', 1),
        (b'a', 1), (b'a', 1), (b'a', 1), (b'a', 1), (b'a', 1), (b'a', 1),
        (b'x', 1.5), (b'>', 0.5), (b'a', 2),
        (b'r', 3 + VIDEO_EXTRA_DELAY))

    # Check the Atk IV and quit if it's 0 ("No good")
    IV_text = ctrlr.read_text(ctrlr.get_frame(), ctrlr.IV_atk_rect)
    if 'nogood' in IV_text.lower().replace(' ', ''):
        ctrlr.log('********** Found 0 Atk target! **********')
        return None
    ctrlr.log(f'IV text detected as {IV_text}. Moving to reset {ctrlr.resets}')

    # Otherwise, reset the game and try again.
    ctrlr.push_buttons(
        (b'h', 3), (b'x', 1), (b'a', 3), (b'a', 1), (b'a', 20), (b'a', 4)
    )
    ctrlr.resets += 1
    return 'loop'


def main(log_name: str) -> None:
    """Entry point for the sequence."""

    actions = {'initialize': initialize, 'loop': loop}

    controller = AutoGiftPokemonController(config, log_name, actions)

    controller.event_loop()


def exception_handler(exception_type, exception_value, exception_traceback):
    """Exception hook to ensure exceptions get logged."""
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

    # make the console formatter easier to read with fewer bits of info
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s: %(message)s", "%H:%M:%S"
    )

    # Configure the console, which will print logged information.
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG if ENABLE_DEBUG_LOGS else logging.INFO)
    console.setFormatter(console_formatter)

    # Configure the file handler, which will save logged information.
    fileHandler = logging.FileHandler(
        filename=os.path.join(base_dir, 'logs', LOG_NAME + '.log'),
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