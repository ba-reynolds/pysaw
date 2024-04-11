from .exceptions import LoginRequired
from .constants import STEAM_FACTOR


def formatted_to_float(price_formatted: str) -> float:
    # "$389,20" -> 389,20"
    numbers = "".join(filter(str.isdigit, price_formatted))
    return int(numbers) / STEAM_FACTOR


def n_elements_per_call(iterable, n):
    buffer = []
    for i in iterable:
        buffer.append(i)
        if len(buffer) < n:
            continue
        yield buffer
        buffer.clear()
    if buffer:
        yield buffer


def encode_varint(value: int) -> bytes:
    # Varint encoding used by protobuf
    # https://carlmastrangelo.com/blog/lets-make-a-varint
    encoded_bytes = bytearray()

    while value > 127:
        # Take the least significant 7 bits of the value and set the continuation bit
        byte = (value & 0x7F) | 0x80
        # Append the byte to the encoded bytes array
        encoded_bytes.append(byte)
        # Shift the value to the right by 7 bits to discard the 7 bits that were just encoded
        value >>= 7

    # For the last byte, set the continuation bit to 0
    encoded_bytes.append(value & 0x7F)

    return bytes(encoded_bytes)


def login_required(func):
    def func_wrapper(self, *args, **kwargs):
        try:
            was_login_executed = self._was_login_executed
        except AttributeError:
            was_login_executed = self._steam._was_login_executed

        if not was_login_executed:
            raise LoginRequired("You must be logged in to perform that action")

        return func(self, *args, **kwargs)

    return func_wrapper
