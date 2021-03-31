import binascii
from crccheck import crc

original = crc.Crc32c.calchex(bytearray.fromhex('f900'), byteorder='little')
print(f'Python calculated CRC (little endian): {original}')

as_int = int(original, 16)
print(f'Integer format: {as_int}')
inverted = as_int ^ 0xffffffff
print(f'Inverted integer: {inverted}')
as_hex = hex(inverted)
print(f'Final hex value: {as_hex}')
print(inverted.to_bytes(4, byteorder='big'))


