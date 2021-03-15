"""Basic controller object for interfacing with the Switch.
Contains a basic event loop as well as methods for viewing video from the
Switch, sending commands via a serial-enabled microcontroller, and logging
results.

Specific use cases can inherit from this class and add specific functionality.
"""

# SwitchController
#
# Eric Donders
# 2021-02-13

import logging
import os
import sys
import time
from datetime import datetime
from typing import Tuple, TypeVar, Iterable, Optional

import cv2
import pytesseract
import serial
import threading
import discord

Image = TypeVar('cv2 image')
Rectangle = Tuple[Tuple[float, float], Tuple[float, float]]


class SwitchController:
    """Generic class for an object that controls a Nintendo Switch through
    incoming video and an outgoing serial connection.
    """

    def __init__(self, config, log_name: str, actions):
        # Zero the start time and fetch the logger.
        self.window_name = 'SwitchController Output'
        self.start_date = datetime.now()
        self.log_name = log_name
        self.logger = logging.getLogger(self.log_name)

        # Store the configuration values.
        self.config = config

        self.phrases = config[config['language']['LANGUAGE']]
        self.tesseract_language = self.phrases['TESSERACT_LANG_NAME']
        self.lang = self.phrases['DATA_LANG_NAME']
        self.enable_debug_logs = config['advanced']['ENABLE_DEBUG_LOGS']

        self.webhook_id = config['discord']['WEBHOOK_ID']
        self.webhook_token = config['discord']['WEBHOOK_TOKEN']
        self.user_id = config['discord']['USER_ID']
        self.user_nickname = config['discord'].get('USER_SHORT_NAME', "")
        self.discord_level = config['discord'].get('UPDATE_LEVELS', "none")
        self.discord_embed_color = discord.Color.random()

        self.actions = actions
        self.info = {}  # To be overwritten later.

        # Store references to the video capture, serial communication, and lock
        # objects used.

        # Connect to the Teensy over a serial port.
        self.com = serial.Serial(
            config['COM_PORT'], 9600, timeout=0.05)
        self.logger.info(f'Attempting to connect to {self.com.port}.')
        timeout_fails = 0
        while not self.com.is_open:
            try:
                self.com.open()
            except serial.SerialException:
                if timeout_fails > 10:
                    # if the serial device won't open after 10 times, we might as well raise and exception and abort
                    raise Exception("Could not connect to the serial device. Check your device.")
                timeout_fails += 1
                pass
        self.logger.info('Connected to the serial device successfully.')

        # Open the video capture.
        vid_index = config['VIDEO_INDEX']
        vid_scale = float(config['advanced']['VIDEO_SCALE'])
        self.cap = VideoCaptureHelper(
            vid_index, (1920, 1080), log_name, vid_scale)

        self.lock = threading.Lock()
        self.exit_flag = threading.Event()
        self.stage = 'initialize'
        self.num_saved_images = 0

    def __del__(self):
        """On destruction, release the serial port and video capture."""
        self.cap.release()
        self.com.close()
        cv2.destroyAllWindows()

    def _button_control_task(self):
        """Loop called by a thread which handles the main button detecting and
        detection aspects of the bot.
        """

        while not self.exit_flag.is_set() and self.stage is not None:
            # Note that this task holds the lock by default but drops it while
            # waiting for Tesseract to respond or while delaying after a button
            # push.
            if self.stage is not None:
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
            # Wait until the button control thread releases the lock, then use
            # the idle time to update the graphical display.
            with self.lock:
                self.display_results()

            # Add a brief delay between each frame so the button control thread
            # has some time to acquire the lock.
            time.sleep(0.01)

            # Tell the button control thread to quit if the Q key is pressed.
            if (
                (cv2.waitKey(1) & 0xFF == ord('q'))
                or cv2.getWindowProperty(self.window_name, 0) == -1
            ):
                self.exit_flag.set()
                # After setting the exit flag, we need to wait for the button
                # control thread to exit because it only checks the flag at the
                # start of a new button push or OCR call.
                self.button_control_thread.join()

    def log(
        self,
        text: str,
        level: str = 'INFO'
    ) -> None:
        """Print a string to the console and log file with a timestamp."""
        self.logger.log(getattr(logging, level), text)

    def add_info(self, key, value) -> None:
        """Add some information to display as part of the video output."""
        self.info[key] = value

    def outline_region(
        self,
        image: Image,
        rect: Rectangle,
        bgr: Tuple[int, int, int] = (255, 255, 255),
        thickness: int = 1
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
        thickness: int = 1
    ):
        """Draw multiple rectangles around detection areas."""
        for rect in rects:
            self.outline_region(image, rect, bgr, thickness)

    def get_frame(self, resize: bool = False) -> Image:
        """Get an image of the current Switch output. This method will usually
        be expanded upon by inheriting classes.
        """

        return self.cap.read(resize=resize)

    def get_image_slice(self, img: Image, section: Rectangle) -> Image:
        """Return the portion of the input image defined by the input
        rectangle. Note the coordinates range from (0, 0) at the top left
        corner to (1, 1) at the bottom right corner.
        """

        h, w = img.shape[:2]
        img = img[round(section[0][1] * h):round(section[1][1] * h),
                  round(section[0][0] * w):round(section[1][0] * w)]
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
        if threshold:
            img = cv2.inRange(cv2.cvtColor(
                img, cv2.COLOR_BGR2HSV), (0, 0, 160), (180, 15, 255))
        if invert:
            img = cv2.bitwise_not(img)
        img = self.get_image_slice(img, section)

        # Then, read text using Tesseract.
        # Note that we need to check for the main thread exiting here.
        if self.exit_flag.is_set():
            sys.exit()
        # We release the lock so that the display thread can continue while
        # Tesseract processes the image.
        self.lock.release()
        text = pytesseract.image_to_string(
            img, lang=self.tesseract_language, config=segmentation_mode
        ).replace('\n', '').strip()
        if text:
            self.log(f'Read text from screen: {text}', 'DEBUG')
        self.lock.acquire()

        # Finally, return the OCRed text.
        return text

    def get_rect_HSV_value(
        self,
        img: Image,
        lower_threshold: Tuple[int, int, int],
        upper_threshold: Tuple[int, int, int],
        is_HSV: bool = False
    ) -> float:
        """Threshold an image and return the average value afterwards."""
        if not is_HSV:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        img_thresholded = cv2.inRange(img, lower_threshold, upper_threshold)

        return img_thresholded.mean()

    def check_rect_HSV_match(
        self,
        rect: Rectangle,
        lower_threshold: Tuple[int, int, int],
        upper_threshold: Tuple[int, int, int],
        mean_value_threshold: float,
        img: Image = None
    ) -> bool:
        """Check a specified section of the screen for values within a certain
        HSV range.
        """

        # Fetch, convert, crop, and threshold image so the feature of interest
        # is white (value 255) and everything else appears black (0)
        if img is None:
            img = self.get_frame()
        h, w = img.shape[:2]
        cropped_area = img[round(rect[0][1] * h):round(rect[1][1] * h),
                           round(rect[0][0] * w):round(rect[1][0] * w)]
        measured_value = self.get_rect_HSV_value(
            cropped_area, lower_threshold, upper_threshold)

        # Return True if the mean value is above the supplied threshold
        return measured_value > mean_value_threshold

    def match_template(
        self,
        img: Image,
        template: Image,
    ) -> Tuple[float, Tuple[int, int]]:
        """Search for a certain pattern within an image. Return the maximum
        match value and the coordinates of the best location.
        """

        # Use OpenCV to get a best match and the location of the match.
        result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        __, max_val, __, max_loc = cv2.minMaxLoc(result, None)

        return max_val, max_loc

    def push_button(
        self,
        char: Optional[str],
        delay: float,  # Seconds
        hold_ticks: int = 1  # Ticks @ 12.5 tick/s
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
            hold_ticks = bytes([round(hold_ticks)])
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
        # optional length of time to hold the button (default is 0.08 seconds
        # or 10 ticks).
        for command in commands:
            self.push_button(*command)

    def display_results(
        self,
        image: Optional[Image] = None,
        log: bool = False,
        screenshot: bool = False
    ):
        """Display video from the Switch alongside some annotations describing
        the run sequence.
        """

        if image is None:
            image = self.get_frame(resize=True)

        # Expand the image with blank space for writing results
        frame = cv2.copyMakeBorder(
            image, 0, 0, 0, 250, cv2.BORDER_CONSTANT
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

        if log or screenshot:
            # Save a screenshot
            self.save_screenshot(frame)
        else:
            # if it's not a screenshot, we'll display the frame
            # Display
            cv2.imshow(self.window_name, frame)

    def save_screenshot(
        self,
        img: Image,
        title: str = 'cap'
    ) -> None:
        """Save a screenshot in the logs folder."""
        self.num_saved_images += 1
        filename = os.path.join(
            'logs', f'{self.log_name}_{title}_{self.num_saved_images}.png')
        self.log(
            f'Saving a screenshot to {filename}', 'DEBUG')
        cv2.imwrite(filename, img)

    def send_discord_message(
        self, ping_yourself: bool, text: str, path_to_picture: str = None,
        embed_fields: dict = None, level: str = "update") -> None:
        """Send a notification via Discord.

        Parameters
        ----------
        ping_yourself : bool
            This input controls if you want to send a ping to the user in the
            settings.
        text : str
            The basic text string to send to the webhook, not included in
            the embed.
        path_to_picture : str, optional
            The path to the picture that should be uploaded and thrown inside
            the embed object.
        embed_fields : dict, optional
            Fields to add to the embed object, should be a dictionary
            where the keys are the titles to give and the items are the text
            for that field.
        level : str, optional
            What type of update this is. Currently accepts "update", "shiny", and
            "critical", which helps the program determine if it should send based
            on settings provided by the user.
        """

        if self.discord_level == 'none':
            # if they don't want discord information, just return and pass by
            return
        elif self.discord_level == 'only_shiny' and level == "update":
            # if they don't want the discord update information, we can also
            # return
            return

        # Do nothing if user did not setup the Discord information.
        if self.webhook_id == '' or self.webhook_token == '' or (
            self.user_id == '' and ping_yourself
        ):
            self.log(
                'You need to setup the discord section to be able to use the '
                'ping feature.', 'DEBUG')
            return

        # construct the webhook object
        webhook = discord.Webhook.partial(
            self.webhook_id, self.webhook_token,
            adapter=discord.RequestsWebhookAdapter()
        )

        # then build up our embed object
        embed = discord.Embed(
            title="AutoMaxLair Update",
            colour=self.discord_embed_color,
            timestamp=datetime.utcnow()
        )

        embed.set_thumbnail(url=f"https://img.pokemondb.net/sprites/home/shiny/{self.boss}.png")
        embed.set_footer(text="AutoMaxLair")

        # if we have fields that we want to add, we can!
        if embed_fields:
            for name, item in embed_fields.items():
                embed.add_field(name=name, value=item, inline=True)

        # construct the proper string
        send_str = f"<@{self.user_id}>" if ping_yourself else f'{self.user_nickname}'
        send_str += f': {text}'

        # add the image to the embed if it was included
        if path_to_picture is not None:
            with open(file=f'{path_to_picture}', mode='rb') as f:
                my_file = discord.File(f, filename="image.png")
            embed.set_image(url="attachment://image.png")
        else:
            my_file = None

        # Open the image to be sent.
        try:
            webhook.send(send_str, embed=embed, file=my_file)
        except Exception as e:
            self.log("The Discord webhook failed to send: " + str(e), "ERROR")


class VideoCaptureHelper:
    """A wrapper for an OpenCV VideoCapture object that assists in
    restarting the video stream in the event of an error and resizing the video
    when necessary.
    """

    def __init__(
        self,
        video_index: int,
        base_resolution: Tuple[int, int],
        log_name: str,
        display_scale: float = 1.0
    ) -> None:
        self.video_index = video_index
        self.base_resolution = base_resolution
        self.logger = logging.getLogger(log_name)
        self.display_scale = display_scale
        self.display_resolution = (
            round(base_resolution[0] * display_scale),
            round(base_resolution[1] * display_scale)
        )
        self.last_image = None
        self.init_video_capture()

    def init_video_capture(self) -> None:
        """Initialize the OpenCV VideoCapture object."""
        self.cap = cv2.VideoCapture(self.video_index)
        if not self.cap.isOpened():
            self.logger.error(
                'Failed to open the video connection. Check the config file '
                'and ensure no other application is using the video input.'
            )
            raise RuntimeError("Failed to initialize video capture.")

        self.cap.set(3, self.base_resolution[0])
        self.cap.set(4, self.base_resolution[1])
        self.failed_count = 0
        self.logger.info('Connected to the video stream.')

    def read(self, resize: bool = False) -> Image:
        """Fetch a frame from the VideoCapture object."""
        ret, img = self.cap.read()

        # Try to handle a dropped frame gracefully. Note that multiple dropped
        # frames may cause the program to appear to freeze.
        if ret:
            self.last_image = img
            self.failed_count = 0  # Clear count on consecutive failed frames
        else:
            self.logger.warning('Failed to read a frame from VideoCapture.')
            img = self.last_image

            self.failed_count = self.failed_count + 1
            # If failed for too long, reiniitalize video capture connection
            if self.failed_count == 10:
                self.logger.warning(
                    'Too many failed frames. Reinitializing VideoCapture.')
                self.release()
                self.init_video_capture()

        if resize:
            img = cv2.resize(img, self.display_resolution)

        return img

    def release(self):
        """Release the OpenCV VideoCapture object."""
        self.cap.release()
