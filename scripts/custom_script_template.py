"""Template for creating custom scripts."""

import logging
import os
import sys
from datetime import datetime

import pytesseract
import toml

# We need to import some class definitions from the parent directory.
from os.path import dirname, abspath
base_dir = dirname(dirname(abspath(__file__)))
sys.path.insert(1, base_dir)
sys.path.insert(1, os.path.join(base_dir, 'automaxlair'))

import automaxlair


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
LOG_NAME = f"CUSTOM_SCRIPT_{datetime.now().strftime('%Y-%m-%d %H-%M-%S')}"


def initialize(__) -> None:
    """Executed once at the beginning of the sequence."""
    return 'loop'


def loop(ctrlr) -> None:
    """Main sequence that is repeated once per cycle."""
    # Add your commands here!






    return 'loop'


def main(log_name: str) -> None:
    """Entry point for the sequence."""

    actions = {'initialize': initialize, 'loop': loop}

    # Replace the controller type if you extend the basic one used below with
    # a custom class.
    controller = automaxlair.switch_controller.SwitchController(
        config, log_name, actions
    )

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