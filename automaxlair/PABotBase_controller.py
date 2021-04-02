"""Interface for bridging the command format intended for RemoteControl.hex
with the command format required by PABotBase.
"""

import binascii
import time

from sys import stdout

import serial

from crccheck import crc


# Constants used by PABotBase
PROTOCOL_VERSION = 2021030200  # Match of all but last 2 digits required
PABB_MSG_ACK_REQUEST_I32  = b'\x14'
PABB_MSG_SEQNUM_RESET = b'\x40'
PABB_MSG_REQUEST_PROTOCOL_VERSION = b'\x41'
PABB_MSG_REQUEST_COMMAND_FINISHED = b'\x45'
PABB_MSG_CONTROLLER_STATE = b'\x9f'
PABB_MSG_COMMAND_PBF_PRESS_BUTTON = b'\x91'

TICKS_PER_SECOND = 125
GLOBAL_RELEASE_TICKS = 10

# Overrides for the parameters used by the regular serial port.
BAUD_RATE = 115200
TIMEOUT = 0.05


# Functions to convert series of parameters into commands.
def _get_button_command(
    seqnum: int,
    button: int,
    hold_ticks: int,
    release_ticks: int
):
    """Get a bytestring corresponding to the desired button press."""
    return (
        b'\x91'
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
        b'\x93', x, 0x80, 0x00, y, GLOBAL_RELEASE_TICKS),  # LY stick min
    b'<': lambda x, y: _get_joystick_command(
        b'\x93', x, 0x00, 0x80, y, GLOBAL_RELEASE_TICKS),  # LX stick min
    b'v': lambda x, y: _get_joystick_command(
        b'\x93', x, 0x80, 0xFF, y, GLOBAL_RELEASE_TICKS),  # LY stick max
    b'>': lambda x, y: _get_joystick_command(
        b'\x93', x, 0xFF, 0x80, y, GLOBAL_RELEASE_TICKS),  # LX stick max
    b'8': lambda x, y: _get_joystick_command(
        b'\x94', x, 0x80, 0x00, y, GLOBAL_RELEASE_TICKS),  # RY stick min
    b'4': lambda x, y: _get_joystick_command(
        b'\x94', x, 0x00, 0x80, y, GLOBAL_RELEASE_TICKS),  # RX stick min
    b'2': lambda x, y: _get_joystick_command(
        b'\x94', x, 0x80, 0xFF, y, GLOBAL_RELEASE_TICKS),  # RY stick max
    b'6': lambda x, y: _get_joystick_command(
        b'\x94', x, 0xFF, 0x80, y, GLOBAL_RELEASE_TICKS)  # RX stick max
}


class PABotBaseController:
    """Wrapper for a serial port that translates messages to the format used
    by PABotBase.
    """

    def __init__(self, port, __, ___, debug_mode=False):
        """Initialize a serial port connection."""
        self.debug_mode = debug_mode
        self.com = serial.Serial(port, 115200)
        self.timeout = 0.05

        self.last_command = None

        self._reset()

    def __del__(self):
        """Close the com port on deletion."""
        if self.com.is_open:
            self.com.close()

    def _reset(self) -> None:
        """Reset the seqnum for both client and server."""

        self.seqnum = 0

        echo = self._write(
            PABB_MSG_SEQNUM_RESET + self.seqnum.to_bytes(4, 'little'))
        assert echo[1] == 0x11, (
            'PABotBase failed to respond to the reset command'
        )

        echo = self._write(
            PABB_MSG_REQUEST_PROTOCOL_VERSION
            + self.seqnum.to_bytes(4, 'little'))
        controller_program_version = int.from_bytes(
            echo[6:10], byteorder='little')
        assert controller_program_version//100 == PROTOCOL_VERSION//100, (
            f'Protocol version {PROTOCOL_VERSION//100}xx is required but the '
            f'microcontroller is using version {controller_program_version}'
        )

    def _write(self, message) -> bytes:
        """Handler for the PABotBase message send routine which involves
        checking that the message was echoed back successfully.
        """

        length_byte = bytes([(5 + len(message)) ^ 0xFF])

        full_message = self._add_checksum(length_byte + message)

        #self.com.flushInput()
        #self.com.flushOutput()
        self.com.write(full_message)
        if self.debug_mode:
            print(f'Sent message: {binascii.hexlify(full_message)}')
        time.sleep(0.005)
        echo = self._read()
        
        return echo

    def _read(self) -> bytes:
        """Handler for the PABotBase message receive routine which involves
        reading an expected message and echoing it back.
        """

        while self.com.inWaiting() == 0:
            time.sleep(0.01)
        length_byte = self.com.read()
        response_length = length_byte[0] ^ 0xFF

        start_time = time.time()
        while time.time() - start_time < self.timeout:
            if self.com.inWaiting() >= response_length - 1:
                message = self.com.read(response_length - 1)
                break

        full_message = length_byte + message

        if self.debug_mode:
            print(f'Received message: {binascii.hexlify(full_message)}')

        return full_message

    def _read_command_finished(self) -> bool:
        """Confirm that PABotBase finished processing a command."""

        full_message = self._read()

        # Prepare an acknowledgement of the received message to return to the
        # microcontroller.
        ack = None
        if full_message[1] == PABB_MSG_REQUEST_COMMAND_FINISHED:
            ack = self._add_checksum(
                b'\x0a' + PABB_MSG_ACK_REQUEST_I32 + full_message[6:10]
            )
        else:
            print(
                f'Message code {full_message[1]} did not'
                ' match any known response.')
        # Send the acknowledgement.
        if ack is not None:
            self.com.write(ack)
            # self.com.flushInput()
            return True
        else:
            return False

        # Print the messages for debugging purposes.
        if self.debug_mode:
            print(f'Received message: {binascii.hexlify(full_message)}')
            if ack is not None:
                print(f'Sent ack: {binascii.hexlify(ack)}')

        return full_message

    def _add_checksum(self, message: bytes) -> bytes:
        """Compute the CRC32 checksum and add it to the end of the message."""

        val = crc.Crc32c.calchex(message, byteorder='little')
        inverted_int = int(val, 16) ^ 0xFFFFFFFF

        return message + inverted_int.to_bytes(4, byteorder='big')

    def _decode_bytestring(self, int_as_bytes: bytes) -> int:
        """Decode the little-endian ints encoded within PABotBase messages."""
        return int.from_bytes(
            binascii.unhexlify(int_as_bytes), byteorder='little')

    def close(self):
        """Close the com port."""
        self.com.close()

    def write(self, message: bytes):
        """Wrapper for serial.Serial.write. Takes two bytes, one for the button
        and one for hold duration, and sends the corresponsing PABotBase
        command.
        """

        self.last_command = message

        character = message[0].to_bytes(1, 'little')
        hold_ticks = message[1] * 10

        if self.debug_mode:
            print(
                f'Translating command with character {character} and duration '
                f'{hold_ticks}')

        translated_command = button_map[character](self.seqnum, hold_ticks)
        self._write(translated_command)
        self.seqnum += 1

    def read(self, length=2):
        """Wrapper for serial.Serial.read. Always returns two bytes since that
        is the format used by SwitchController.
        """

        if length != 2:
            raise serial.SerialException(
                'PABotBaseController.read method always returns 2 bytes.')

        if self._read_command_finished():
            return self.last_command
        else:
            return b'\xff\xff'  # Throws an error


if __name__ == '__main__':

    com = PABotBaseController('COM4', 9600, 0.05, True)
    com.write(b'x' + bytes([8]))
    print(com.read(2))
    com.write(b'x' + bytes([8]))
    print(com.read(2))
