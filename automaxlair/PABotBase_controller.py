"""Interface for bridging the command format intended for RemoteControl.hex
with the command format required by PABotBase.

PABotBase code can be found on GitHub:
https://github.com/PokemonAutomation/SwSh-Arduino
"""

import binascii
import time

import serial
from crccheck import crc

FORCE_DEBUG_MODE = False

# Constants used by PABotBase.
PROTOCOL_VERSION = 2021032200  # Match of all but last 2 digits required
PABB_MSG_ERROR_WARNING = b'\x07'
PABB_MSG_ACK_REQUEST = b'\x11'
PABB_MSG_SEQNUM_RESET = b'\x40'
PABB_MSG_REQUEST_PROTOCOL_VERSION = b'\x41'
PABB_MSG_REQUEST_COMMAND_FINISHED = b'\x45'
PABB_MSG_REQUEST_STOP = b'\x46'
PABB_MSG_CONTROLLER_STATE = b'\x9f'
PABB_MSG_COMMAND_PBF_PRESS_BUTTON = b'\x91'
PABB_MSG_COMMAND_PBF_MOVE_JOYSTICK_L = b'\x93'
PABB_MSG_COMMAND_PBF_MOVE_JOYSTICK_R = b'\x94'

GLOBAL_RELEASE_TICKS = 10

# Overrides for the parameters used by the regular serial port.
BAUD_RATE = 115200


# Functions to convert series of parameters into commands.
def _get_button_command(
    seqnum: int,
    button: int,
    hold_ticks: int,
    release_ticks: int
):
    """Get a bytestring corresponding to the desired button press."""
    return (
        PABB_MSG_COMMAND_PBF_PRESS_BUTTON
        + seqnum.to_bytes(4, byteorder='little')
        + button.to_bytes(2, byteorder='little')
        + hold_ticks.to_bytes(2, byteorder='little')
        + release_ticks.to_bytes(2, byteorder='little')
    )


def _get_joystick_command(
    stick_type: bytes,
    seqnum: int,
    x: int,
    y: int,
    hold_ticks: int,
    release_ticks: int
):
    """Get a bytestring corresponding to the desired joystick movement."""
    return (
        stick_type
        + seqnum.to_bytes(4, byteorder='little')
        + x.to_bytes(1, byteorder='little')
        + y.to_bytes(1, byteorder='little')
        + hold_ticks.to_bytes(2, byteorder='little')
        + release_ticks.to_bytes(2, byteorder='little')
    )


# Map for translating commands used by AutoMaxLair into PABotBase commands.
#
# Note that each value should be called with the seqnum as the first parameter
# and the hold ticks as the second parameter.
# Example: command: bytes = button_map['a'](seqnum: int, hold_ticks: int)
button_map = {
    b'y': lambda x, y: _get_button_command(x, 1, y, GLOBAL_RELEASE_TICKS),
    b'b': lambda x, y: _get_button_command(x, 2, y, GLOBAL_RELEASE_TICKS),
    b'a': lambda x, y: _get_button_command(x, 4, y, GLOBAL_RELEASE_TICKS),
    b'x': lambda x, y: _get_button_command(x, 8, y, GLOBAL_RELEASE_TICKS),
    b'l': lambda x, y: _get_button_command(x, 16, y, GLOBAL_RELEASE_TICKS),
    b'r': lambda x, y: _get_button_command(x, 32, y, GLOBAL_RELEASE_TICKS),
    b'L': lambda x, y: _get_button_command(x, 64, y, GLOBAL_RELEASE_TICKS),
    b'R': lambda x, y: _get_button_command(x, 128, y, GLOBAL_RELEASE_TICKS),
    b'-': lambda x, y: _get_button_command(x, 256, y, GLOBAL_RELEASE_TICKS),
    b'+': lambda x, y: _get_button_command(x, 512, y, GLOBAL_RELEASE_TICKS),
    b'C': lambda x, y: _get_button_command(x, 1024, y, GLOBAL_RELEASE_TICKS),
    b'c': lambda x, y: _get_button_command(x, 2048, y, GLOBAL_RELEASE_TICKS),
    b'h': lambda x, y: _get_button_command(x, 4096, y, GLOBAL_RELEASE_TICKS),
    b'p': lambda x, y: _get_button_command(x, 8192, y, GLOBAL_RELEASE_TICKS),
    b'^': lambda x, y: _get_joystick_command(
        PABB_MSG_COMMAND_PBF_MOVE_JOYSTICK_L, x, 0x80, 0x00, y,
        GLOBAL_RELEASE_TICKS),  # LY stick min
    b'<': lambda x, y: _get_joystick_command(
        PABB_MSG_COMMAND_PBF_MOVE_JOYSTICK_L, x, 0x00, 0x80, y,
        GLOBAL_RELEASE_TICKS),  # LX stick min
    b'v': lambda x, y: _get_joystick_command(
        PABB_MSG_COMMAND_PBF_MOVE_JOYSTICK_L, x, 0x80, 0xFF, y,
        GLOBAL_RELEASE_TICKS),  # LY stick max
    b'>': lambda x, y: _get_joystick_command(
        PABB_MSG_COMMAND_PBF_MOVE_JOYSTICK_L, x, 0xFF, 0x80, y,
        GLOBAL_RELEASE_TICKS),  # LX stick max
    b'8': lambda x, y: _get_joystick_command(
        PABB_MSG_COMMAND_PBF_MOVE_JOYSTICK_R, x, 0x80, 0x00, y,
        GLOBAL_RELEASE_TICKS),  # RY stick min
    b'4': lambda x, y: _get_joystick_command(
        PABB_MSG_COMMAND_PBF_MOVE_JOYSTICK_R, x, 0x00, 0x80, y,
        GLOBAL_RELEASE_TICKS),  # RX stick min
    b'2': lambda x, y: _get_joystick_command(
        PABB_MSG_COMMAND_PBF_MOVE_JOYSTICK_R, x, 0x80, 0xFF, y,
        GLOBAL_RELEASE_TICKS),  # RY stick max
    b'6': lambda x, y: _get_joystick_command(
        PABB_MSG_COMMAND_PBF_MOVE_JOYSTICK_R, x, 0xFF, 0x80, y,
        GLOBAL_RELEASE_TICKS)  # RX stick max
}


class PABotBaseController:
    """Wrapper for a serial port that translates messages to the format used
    by PABotBase.
    """

    def __init__(self, port, __, timeout=0.05, debug_mode=False):
        """Connect to the microcontroller and initialize it."""
        # Initialize attributes.
        self.timeout = timeout
        self.debug_mode = debug_mode or FORCE_DEBUG_MODE
        self.last_command = None
        # Initialize some dummy attributes that are needed because this object
        # pretends to be a serial.Serial object.
        self.port = port
        self.in_waiting = 0
        self.is_open = True

        # Open a serial port
        self.com = serial.Serial(port, 115200)
        # Go through a reset sequence which initializes PABotBase.
        self._reset()

    def __del__(self):
        """Close the com port on deletion."""
        if self.com.is_open:
            self.com.close()

    def _reset(self) -> None:
        """Reset the seqnum for both client and server."""
        # Flush serial buffers and reset the command/request count.
        self.com.flushInput()
        self.com.flushOutput()
        self.seqnum = 0

        # Command PABotBase to stop its current operation.
        echo = self._write(
            PABB_MSG_REQUEST_STOP + self.seqnum.to_bytes(4, 'little')
        )
        # Reset the device seqnum.
        echo = self._write(
            PABB_MSG_SEQNUM_RESET + self.seqnum.to_bytes(4, 'little'))
        assert echo[1] == 0x11, (
            'PABotBase failed to respond to the reset command'
        )
        self.seqnum += 1
        # Get the protocol version and throw an error if it's incompatible.
        echo = self._write(
            PABB_MSG_REQUEST_PROTOCOL_VERSION
            + self.seqnum.to_bytes(4, 'little'))
        controller_program_version = int.from_bytes(
            echo[6:10], byteorder='little')
        assert controller_program_version // 100 == PROTOCOL_VERSION // 100, (
            f'Protocol version {PROTOCOL_VERSION // 100}xx is required but the'
            f' microcontroller is using version {controller_program_version}'
        )

    def _write(self, message) -> bytes:
        """Handler for the PABotBase message send routine which involves
        checking that the message was echoed back successfully.
        """

        # Add the length byte and CRC to the input message.
        length_byte = bytes([(5 + len(message)) ^ 0xFF])
        full_message = self._add_checksum(length_byte + message)
        # Send the message and get the response.
        self.com.write(full_message)
        if self.debug_mode:
            print(f'Sent message: {binascii.hexlify(full_message)}')
        return self._read()

    def _read(self) -> bytes:
        """Method for reading a single message that was sent from PABotBase."""
        # Wait until a message is received, then parse the message.

        # First, read the length of the message.
        while self.com.in_waiting == 0:
            time.sleep(0.01)
        length_byte = self.com.read()
        response_length = length_byte[0] ^ 0xFF
        start_time = time.time()
        message = None

        # Then, read bytes to fill the message length.
        while time.time() - start_time < self.timeout:
            # Wait until a full message has arrived, then read it.
            if self.com.in_waiting >= response_length - 1:
                message = self.com.read(response_length - 1)
                break
        if message is None:
            # In the event of a timeout, read whatever did arrive.
            # Note that this state usually results in an error.
            message = self.com.read(self.com.in_waiting)

        # Finally, assmble and return the complete message.
        full_message = length_byte + message
        if self.debug_mode:
            print(f'Received message: {binascii.hexlify(full_message)}')
        return full_message

    def _read_command_finished(self) -> bool:
        """Confirm that PABotBase finished processing a command, and send an
        acknowledgement for receiving the notification.
        """

        # First, read the expected PABB_MSG_REQUEST_COMMAND_FINISHED message.
        full_message = self._read()

        # Prepare an acknowledgement of the received message to return to the
        # microcontroller.
        ack = None
        code = full_message[1]
        if code == PABB_MSG_REQUEST_COMMAND_FINISHED[0]:
            # Expected response indicating that a previous command succeeded.
            # Prepare the acknowledgement.
            ack = self._add_checksum(
                b'\xf5' + PABB_MSG_ACK_REQUEST + full_message[2:6]
            )
        elif (
            code == PABB_MSG_ERROR_WARNING[0]
            and full_message[2:4] == b'\x01\x00'
        ):
            # Random error that can be ignored, therefore re-call this method.
            return self._read_command_finished()
        else:
            # Unknown error code—print a warning.
            print(
                f'Message code {bytes([full_message[1]])} did not'
                ' match any known response.')

        # Print the messages for debugging purposes.
        if self.debug_mode and ack is not None:
            print(f'Sent ack: {binascii.hexlify(ack)}')

        # Send the acknowledgement.
        if ack is not None:
            self.com.write(ack)
            return True
        else:
            return False

    def _add_checksum(self, message: bytes) -> bytes:
        """Compute the CRC32 checksum and add it to the end of the message."""

        # Compute the CRC using the crccheck module.
        val = crc.Crc32c.calchex(message, byteorder='little')
        # Transform it to the Intel format used by PABotBase.
        inverted_int = int(val, 16) ^ 0xFFFFFFFF

        return message + inverted_int.to_bytes(4, byteorder='big')

    def close(self):
        """Close the com port."""
        self.com.close()

    def write(self, message: bytes):
        """External facing method that the SwitchController will call in the
        same way as serial.Serial.write.

        Takes two bytes, one for the button and one for hold duration, and
        sends the corresponsing PABotBase command.
        """

        # Save the command so it can be "echoed" when the read method is
        # called.
        self.last_command = message

        # Extract the command and hold duration from the input.
        character = message[0].to_bytes(1, 'little')
        hold_ticks = message[1] * 10

        if self.debug_mode:
            print(
                f'Translating command with character {character} and duration '
                f'{hold_ticks}')

        # Increment the seqnum so PABotBase knows this command is new.
        self.seqnum += 1
        # Get the translated command using the preconstructed map.
        # Note that button_map[character] is an anonymous function of either
        # _get_button_command or _get_joystick_command with some parameters
        # filled in already.
        translated_command = button_map[character](self.seqnum, hold_ticks)
        # Finally, send the translated command to the microcontroller.
        self._write(translated_command)

    def read(self, length=2):
        """Wrapper for serial.Serial.read. Always returns two bytes since that
        is the format used by SwitchController.
        """

        assert length == 2, (
            'PABotBaseController.read method always returns 2 bytes.')

        # Handle an incoming PABB_MSG_REQUEST_COMMAND_FINISHED message and
        # "echo" the previous command successfully if everything went as
        # expected.
        if self._read_command_finished():
            return self.last_command
        else:
            return b'er'  # Throws an error


if __name__ == '__main__':
    # Test sequence for running this script in isolation.
    com = PABotBaseController('COM4', 9600, 0.05, True)
    com.write(b'a' + bytes([8]))
    print(com.read(2))
    time.sleep(1)
    com.write(b'b' + bytes([8]))
    print(com.read(2))
    time.sleep(1)
    com.write(b'a' + bytes([8]))
    print(com.read(2))
