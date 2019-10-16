import queue
from _errors import MsgTooLong

class RobotNotInUsername(Exception):
    pass
class InfoOrFoto(Exception):
    pass

class Buffer:
    def __init__(self):
        self.buffer = bytearray()
        self.photo_length_buffer = bytearray()
        self.state = 0  # only 0 and 1 is allowed
        self.password = None
        self.last_byte = None
        self.second_last_byte = None
        self.counting_pass = False
        self.counting_checksum = False

    def process_byte(self, byte: bytes) -> bool or int:
        # """
        # Adds byte to a buffer, takes care of handling escape characters
        # :param byte:
        # :return: True on success, bytesarray() on escape seq
        # """
        if self.state == 0:
            if self.counting_pass and byte == b'\n' and self.last_byte == b'\r':  # escape sequence
                self.state = 1
                self.counting_pass = False
                return self.password

            if not self.counting_pass:
                self.buffer.extend(byte)
                if len(self.buffer) == 5:
                    if not self.buffer == bytearray(b'Robot'):
                        raise RobotNotInUsername()
                    else:
                        self.counting_pass = True
                        return None
            else:
                self.last_byte = byte
                self.password += ord(byte)
                return None

        elif self.state == 1:
            if byte == b'\n' and self.last_byte == b'\r':  # escape sequence
                self.state = 2
                return self.buffer[:-1]
            else:
                self.buffer.extend(byte)
                return None

        elif self.state == 2:
            # if self.counting_checksum and byte == b'\n' and self.last_byte == b'\r':  # escape sequence
            #     self.state = 1
            #     self.counting_pass = False
            #     return self.password

            if not self.counting_checksum:
                self.buffer.extend(byte)
                if len(self.buffer) == 5:
                    if not self.buffer == bytearray(b'INFO ') or not self.buffer == bytearray(b'FOTO '):
                        raise InfoOrFoto()
                elif len(self.buffer) > 5 and byte != b' ':
                    self.photo_length_buffer.extend(byte)
                elif byte == b' ':
                    self.counting_checksum = True
                # TODO case of INFO, compute the checksum on the go, ...
