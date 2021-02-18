# SwitchController
#
# Eric Donders
# 2021-02-13

import logging
import pickle
import sys
import time
from datetime import datetime
from typing import List, Tuple, TypeVar, Iterable, Optional

import cv2
import enchant
import pytesseract
import serial
import threading

from .pokemon_classes import Pokemon
from configparser import ConfigParser
Image = TypeVar('cv2 image')
Rectangle = Tuple[Tuple[float, float], Tuple[float, float]]

class SwitchController:
    """Generic class for an object that controls a Nintendo Switch through
    incoming video and an outgoing serial connection.
    """

    def __init__(self, config, log_name: str, actions):
        # Zero the start time and fetch the logger.
        self.start_date = datetime.now()
        self.log_name = log_name
        self.logger = logging.getLogger(self.log_name)

        # Store the configuration values.
        self.config = config

        self.phrases = config[config['language']['LANGUAGE']]
        self.tesseract_language = self.phrases['TESSERACT_LANG_NAME']
        self.lang = self.phrases['DATA_LANG_NAME']
        self.enable_debug_logs = config['advanced']['ENABLE_DEBUG_LOGS'].lower() == 'true'


        self.actions = actions
        self.info = {}  # To be overwritten later.

        # Store references to the video capture, serial communication, and lock
        # objects used.

        # Connect to the Teensy over a serial port.
        self.com = serial.Serial(config['default']['COM_PORT'], 9600, timeout=0.05)
        self.logger.info(f'Attempting to connect to {self.com.port}.')
        while not self.com.is_open:
            try:
                self.com.open()
            except serial.SerialException:
                pass
        self.logger.info('Connected to the serial device successfully.')

        # Open the video capture.
        self.logger.info('Attempting to open the video connection.')
        self.cap = cv2.VideoCapture(int(config['default']['VIDEO_INDEX']))
        if not self.cap.isOpened():
            self.com.close()
            self.cap.release()
            raise Exception('Failed to open the video connection. Check the config file and '
                'ensure no other application is using the video input.')

        vid_scale = float(config['advanced']['VIDEO_SCALE'])
        self.base_resolution = (1920, 1080)
        self.display_resolution = (
            round(1920 * vid_scale), round(1080 * vid_scale))
        self.cap.set(3, self.base_resolution[0])
        self.cap.set(4, self.base_resolution[1])
        self.last_image = None
        self.lock = threading.Lock()
        self.exit_flag = threading.Event()
        self.stage = 'initialize'
        self.num_saved_images = 0

    def _button_control_task(self):
        """Loop called by a thread which handles the main button detecting and
        detection aspects of the bot.
        """

        while not self.exit_flag.is_set():
            # Note that this task holds the lock by default but drops it while
            # waiting for Tesseract to respond or while delaying after a button
            # push.
            with self.lock:
                self.stage = self.actions[self.stage](self)

    def event_loop(self):
        """Method called to kick off the event loop. Note that this method is
        blocking and will not return until the program terminates.
        """

        # Start a thread that will control all the button press sequences
        self.button_control_thread = threading.Thread(
            target=self._button_control_task
        )
        self.button_control_thread.start()

        # Start event loop which handles the display and checks for the user
        # manually quitting.
        # The loop ends when the button control thread ends naturally or when
        # signalled by the user pressing the Q key.
        while self.button_control_thread.is_alive():
            # Wait until the button control thread releases the lock, then use the
            # idle time to update the graphical display.
            with self.lock:
                self.display_results()

            # Add a brief delay between each frame so the button control thread has
            # some time to acquire the lock.
            time.sleep(0.01)

            # Tell the button control thread to quit if the Q key is pressed.
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.exit_flag.set()
                # After setting the exit flag, we need to wait for the button
                # control thread to exit because it only checks the flag at the
                # start of a new button push or OCR call.
                self.button_control_thread.join()

        self.cap.release()
        self.com.close()


    def log(
        self,
        text: str,
        level: str = 'INFO'
    ) -> None:
        """Print a string to the console and log file with a timestamp."""
        self.logger.log(getattr(logging, level), text)

    def outline_region(
        self,
        image: Image,
        rect: Rectangle,
        bgr: Tuple[int, int, int] = (255, 255, 255),
        thickness: int = 2
    ) -> None:
        """Draw a rectangle around a detection area for debug purposes."""
        h, w = image.shape[:2]
        top_left = (round(rect[0][0] * w) - 1, round(rect[0][1] * h) - 1)
        bottom_right = (round(rect[1][0] * w) + 1, round(rect[1][1] * h) + 1)
        cv2.rectangle(image, top_left, bottom_right, bgr, thickness)

    def outline_regions(
        self,
        image: Image,
        rects: Iterable[Rectangle],
        bgr: Tuple[int, int, int] = (255, 255, 255),
        thickness: int = 2
    ):
        """Draw multiple rectangles around detection areas."""
        for rect in rects:
            self.outline_region(image, rect, bgr, thickness)

    def get_frame(self) -> Image:
        """Get an annotated image of the current Switch output."""

        # Fetch a frame from the VideoCapture object.
        ret, img = self.cap.read()

        # Try to handle a dropped frame gracefully. Note that multiple dropped
        # frames may cause the program to appear to freeze.
        if ret:
            self.last_image = img
        else:
            self.log('Failed to read a frame from VideoCapture.', 'WARNING')
            img = self.last_image

        # Return annotated image.
        return img

    def read_text(
        self,
        img: Image,
        section: Rectangle = ((0, 0), (1, 1)),
        threshold: bool = True,
        invert: bool = False,
        segmentation_mode: str = '--psm 11'
    ) -> str:
        """Read text from a section (default entirety) of an image using
        Tesseract.
        """

        # Process image according to instructions
        h, w = img.shape[:2]
        if threshold:
            img = cv2.inRange(cv2.cvtColor(
                img, cv2.COLOR_BGR2HSV), (0, 0, 100), (180, 15, 255))
        if invert:
            img = cv2.bitwise_not(img)
        img = img[round(section[0][1] * h):round(section[1][1] * h),
                  round(section[0][0] * w):round(section[1][0] * w)]

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

    def check_rect_HSV_match(
        self,
        rect: Rectangle,
        lower_threshold: Tuple[int, int, int],
        upper_threshold: Tuple[int, int, int],
        mean_value_threshold: float
    ) -> bool:
        """Check a specified section of the screen for values within a certain
        HSV range.
        """

        # Fetch, convert, crop, and threshold image so the feature of interest
        # is white (value 255) and everything else appears black (0)
        img = cv2.cvtColor(self.get_frame(), cv2.COLOR_BGR2HSV)
        h, w = img.shape[:2]
        cropped_area = img[round(rect[0][1] * h):round(rect[1][1] * h),
                           round(rect[0][0] * w):round(rect[1][0] * w)]
        measured_value = cv2.inRange(cropped_area, lower_threshold,
                                     upper_threshold).mean()

        # Return True if the mean value is above the supplied threshold
        return measured_value > mean_value_threshold

    def push_button(
        self,
        char: Optional[str],
        delay: float,  # Seconds
        hold_time: float = 0.08  # Seconds
    ) -> None:
        """Send a message to the microcontroller telling it to press buttons on
        the Switch.
        """

        # Check whether the main thread has called for the button pushing
        # thread to terminate.
        if self.exit_flag.is_set():
            sys.exit()

        # Then we release the lock so the display thread can run while we
        # complete the button press and subsequent delay.
        self.lock.release()

        # Clear extra characters from the serial buffer.
        while self.com.in_waiting > 0:
            self.log(
                f'Unexpected byte received: "{self.com.read()}"', 'WARNING'
            )

        # Send the command to the microcontroller using the serial port.
        if char is not None:
            self.com.write(char)
            hold_ticks = bytes([int(hold_time * 12.5)])
            self.com.write(hold_ticks)
            char_echo = self.com.read()
            hold_echo = self.com.read()
            # Check whether the microcontroller successfully echoed back the
            # command, and raise a warning if it did not.
            if char_echo != char:
                self.log(
                    f'Received "{char_echo}" instead of sent "{char}".',
                    'WARNING'
                )
            if hold_echo != hold_ticks:
                self.log(
                    f'Received "{hold_echo}" instead of sent "{hold_ticks}".',
                    'WARNING'
                )

        # Delay for the specified time.
        time.sleep(delay)

        # Reacquire the lock before the next iteration.
        # This step is needed here because calling sys.exit() in a
        # subsequent command will attempt to release the lock.
        self.lock.acquire()

    def push_buttons(self, *commands: Tuple[str, float]) -> None:
        """Send a sequence of messages to the microcontroller telling it to
        press buttons on the Switch.
        """

        # Commands are supplied as tuples consisting of a character
        # corresponding to a button push, a delay that follows the push, and an
        # optional number of repeats (default is 1).
        for command in commands:
            self.push_button(*command)

    def display_results(self, log: bool = False, screenshot: bool = False):
        """Display video from the Switch alongside some annotations describing
        the run sequence.
        """

        # Expand the image with blank space for writing results
        frame = cv2.copyMakeBorder(
            cv2.resize(self.get_frame(),
                       self.display_resolution), 0, 0, 0, 250, cv2.BORDER_CONSTANT
        )
        width = frame.shape[1]

        # Place the text on the newly created black space in the image.
        i = 0
        for key, value in self.info.items():
            cv2.putText(
                frame, key + ': ' + str(value), (width - 245, 25 + 25 * i),
                cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 2, cv2.LINE_AA
            )
            if log:
                self.log(key + ': ' + str(value))
            i += 1

        # Display
        cv2.imshow('Output', frame)

        if log or screenshot:
            # Save a screenshot
            self.num_saved_images += 1
            cv2.imwrite(f'logs/{self.log_name}_cap_{self.num_saved_images}.png', frame)


        