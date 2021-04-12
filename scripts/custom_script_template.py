"""Template for creating custom scripts.

To use, edit the areas enclosed in the horizontal lines. The simplest place to
edit is in the `loop` function, which runs continuously until the program ends.

You can run this script directly after making these modifications.
"""

import logging
import os
import sys
from datetime import datetime
from typing import Callable, Dict, TypeVar

import pytesseract
import toml

# We need to import some class definitions from the parent directory.
from os.path import dirname, abspath
base_dir = dirname(dirname(abspath(__file__)))
sys.path.insert(1, base_dir)
sys.path.insert(1, os.path.join(base_dir, 'automaxlair'))

import automaxlair  # noqa: E402
Image = TypeVar('cv2 image')


# load configuration from the config file
try:
    config = toml.load("Config.toml")
except FileNotFoundError:
    raise FileNotFoundError(
        "The Config.toml file was not found! Be sure to copy "
        "Config.sample.toml as Config.toml and edit it!")
except:  # noqa: E722
    raise SyntaxError(
        "Something went wrong parsing Config.toml\n" +
        "Please make sure you entered the information right " +
        "and did not modify \" or . symbols or have uppercase true or false "
        "in the settings.")

COM_PORT = config['COM_PORT']
VIDEO_INDEX = config['VIDEO_INDEX']
VIDEO_EXTRA_DELAY = config['advanced']['VIDEO_EXTRA_DELAY']
pytesseract.pytesseract.tesseract_cmd = config['TESSERACT_PATH']
ENABLE_DEBUG_LOGS = config['advanced']['ENABLE_DEBUG_LOGS']

# Set the log name
LOG_NAME = f"CUSTOM_SCRIPT_{datetime.now().strftime('%Y-%m-%d %H-%M-%S')}"


class CustomController(automaxlair.switch_controller.SwitchController):
    """Custom Switch controller that can include any functionality you want to
    add that doesn't fit in the functions below, for example extra variables
    that you want to track or new methods that you plan to use often.
    """

    def __init__(
        self,
        config_,
        log_name: str,
        actions: Dict[str, Callable]
    ) -> None:
        # Call base class constructor.
        super().__init__(config_, log_name, actions)

        # --------------------
        # Add custom initialization here.

        # --------------------

    def get_frame(
        self,
        resize: bool = False
    ) -> Image:
        """Get an annotated image of the current Switch output."""

        # Get the base image from the base class method.
        img = super().get_frame(resize=resize)
        
        # --------------------
        # Add any extra image processing you want here.

        # --------------------

        return img

    def display_results(self, log: bool = False, screenshot: bool = False):
        """Display video from the Switch alongside some annotations describing
        the run sequence.
        """

        # Construct the dictionary that will be displayed by the base method.
        for key, value in {
            # --------------------
            # You can add key: value pairs here to be displayed.

            # --------------------
        }.items():
            self.info[key] = value

        # Call the base display method.
        super().display_results(
            image=self.get_frame(resize=True), log=log,
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
    """Main sequence that is repeated once per cycle. To quit, simply return
    `None` at any point in this function.
    """

    # --------------------
    # Add your commands here!

    # --------------------

    return 'loop'


def main(log_name: str) -> None:
    """Entry point for the sequence."""

    actions = {'initialize': initialize, 'loop': loop}

    # Replace the controller name if you renamed the custom class.
    controller = CustomController(config, log_name, actions)

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