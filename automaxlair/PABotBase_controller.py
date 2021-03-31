"""Interface for bridging the command format intended for RemoteControl.hex
with the command format required by PABotBase.
"""

import binascii
import time

from sys import stdout

import serial

from crccheck import crc


# Constants used by PABotBase
PROTOCOL_VERSION = 2021030200  # Match to hex file required
PABB_MSG_SEQNUM_RESET = b'\x40'
PABB_MSG_REQUEST_PROTOCOL_VERSION = b'\x41'
PABB_MSG_CONTROLLER_STATE = b'\x9f'

# Overrides for the parameters used by the regular serial port.
BAUD_RATE = 115200
TIMEOUT = 0.05


class PABotBaseController:
    """Wrapper for a serial port that translates messages to the format used
    by PABotBase.
    """

    def __init__(self, port, __, __, debug_mode=False):
        """Initialize a serial port connection."""
        self.debug_mode = debug_mode
        self.com = serial.Serial(port, 115200)

        self._reset()

    def __del__(self):
        """Close the com port on deletion."""
        if self.com.is_open:
            self.com.close()

    def _reset(self) -> None:
        """Reset the seqnum for both client and server."""

        self.seqnum = 0

        echo = self._write(PABB_MSG_SEQNUM_RESET, b'')
        assert echo[1] == 0x11, (
            'PABotBase failed to respond to the reset command'
        )

        echo = self._write(PABB_MSG_REQUEST_PROTOCOL_VERSION, b'')
        controller_program_version = self._decode_bytestring(echo[6:10])
        assert controller_program_version == PROTOCOL_VERSION, (
            f'Protocol version {PROTOCOL_VERSION} is required but the '
            f'microcontroller is using version {controller_program_version}'
        )

    def _write(self, message_type_byte, message) -> None:
        """Handler for the PABotBase message send routine which involves
        checking that the message was echoed back successfully.
        """

        length_byte = bytes([(10 + len(message)) ^ 0xFF])

        full_message = self._add_checksum(
            length_byte + message_type_byte
            + self._encode_bytestring(self.seqnum) + message
        )

        self.com.flushInput()
        self.com.flushOutput()
        self.com.write(full_message)
        time.sleep(0.05)
        echo = self.com.read(self.com.inWaiting())
        if self.debug_mode:
            print(f'Sent message: {binascii.hexlify(full_message)}')
            print(f'Received message: {binascii.hexlify(echo)}')
        return echo

    def _read(self) -> bytes:
        """Handler for the PABotBase message receive routine which involves
        reading an expected message and echoing it back.
        """

        self.com.flushInput()
        while self.com.inWaiting() == 0:
            time.sleep(0.01)
        length_byte = self.com.read()
        response_length = int.from_bytes([length_byte], 'little') ^ 0xFF

        start_time = time.time()
        while time.time() - start_time < 0.05:
            if self.com.inWaiting() >= response_length - 1:
                message = self.com.read(response_length)
                break

        full_message = length_byte + message

        if self.debug_mode:
            print(f'Received message: {full_message}')

        self.com.write(full_message)

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

    def _encode_bytestring(self, integer: int) -> bytes:
        """Encode an integer as a 4 byte little-endian bytestring."""
        return integer.to_bytes(4, byteorder='little')

    def close(self):
        """Close the com port."""
        self.com.close()

    def write(self, message: bytes):
        """Wrapper for serial.Serial.write. Takes two bytes, one for the button
        and one for hold duration, and sends the corresponsing PABotBase
        command.
        """

        self.seqnum += 1

        translated_message = b'PLACEHOLDER'

        self._write(translated_message)

    def read(self, length=2):
        """Wrapper for serial.Serial.read. Always returns two bytes since that
        is the format used by SwitchController.
        """

        if length != 2:
            raise serial.SerialException(
                'PABotBaseController.read method always returns 2 bytes.')

        message = self._read()

        translated_message = message  # PLACEHOLDER

        return translated_message


if __name__ == '__main__':

    com = PABotBaseController('COM4', 9600, 0.05, True)
