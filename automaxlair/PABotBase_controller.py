"""Interface for bridging the command format intended for RemoteControl.hex
with the command format required by PABotBase.
"""

import time

import serial

from crccheck import crc


# Constants used by PABotBase
PABB_MSG_SEQNUM_RESET = b'\x40'
PABB_MSG_CONTROLLER_STATE = b'\x9f'

# Overrides for the parameters used by the regular serial port.
BAUD_RATE = 115200
TIMEOUT = 0.05


class PABotBaseController:
    """Wrapper for a serial port that translates messages to the format used
    by PABotBase.
    """

    def __init__(self, port, __, timeout_=0.05):
        """Initialize a serial port connection."""
        self.com = serial.Serial(port, 115200)
        #self.com.open()
        self.timeout = timeout_

        self._reset()

    def __del__(self):
        """Close the com port on deletion."""
        self.com.close()

    def _reset(self) -> None:
        """Reset the seqnum for both client and server."""

        self.seqnum = 0
        length_byte = bytes([10 ^ 0xFF])  # 10 bytes in length
        message = self._add_checksum(length_byte + PABB_MSG_SEQNUM_RESET)

        self.com.write(b'\x00'*15)

        self._write(message)

    def _write(self, message) -> None:
        """Handler for the PABotBase message send routine which involves
        checking that the message was echoed back successfully.
        """

        self.com.flushInput()
        self.com.write(message)
        echo = self.com.read(len(message))
        print(f'Sent message: {message}')
        print(f'Echoed message: {echo}')
        return echo

    def _read(self) -> bytes:
        """Handler for the PABotBase message receive routine which involves
        reading an expected message and echoing it back.
        """

        self.com.flushInput()
        while self.com.inWaiting() == 0:
            time.sleep(0.01)
        length_byte = self.com.read()
        response_length = ~length_byte[0]

        start_time = time.time()
        while time.time() - start_time < self.timeout:
            if self.com.inWaiting() >= response_length:
                message = self.com.read(response_length)
                break

        full_message = length_byte + message

        print(f'Received message: {full_message}')

        self.com.write(full_message)

        return full_message

    def _add_checksum(self, message: bytes) -> bytes:
        """Compute the CRC32 checksum and add it to the end of the message."""

        crc32_string = crc.Crc32.calchex(message)
        return message + bytes.fromhex(crc32_string)

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

    com = PABotBaseController('COM4', 9600, 0.05)
