import struct

class RobotNotInUsername(Exception):
    pass
class InfoOrFoto(Exception):
    pass
class FotoException(Exception):
    pass

class Buffer:
    def __init__(self):
        self.buffer = bytearray()
        self.photo_length_buffer = bytearray()
        self.state = 0  # only 0 and 1 is allowed
        self.info = None
        self.photo = None
        self.checksum = 0
        self.sent_checksum = bytearray()
        self.read_photo_bytes = 0
        self.password = 0
        self.last_byte = None
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
                self.password -= ord(b'\r')  # bc \r is end seq, we dont want to count that
                self.state = 1
                self.counting_pass = False
                self.buffer = bytearray()
                return self.password

            if not self.counting_pass:
                self.buffer.extend(byte)
                self.password += ord(byte)
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
                ret = self.buffer[:-1]
                self.buffer = bytearray()  # flush it
                return ret
            else:
                self.buffer.extend(byte)
                return None

        elif self.state == 2:
            if not self.counting_checksum:
                self.buffer.extend(byte)
                if len(self.buffer) == 5:
                    if not self.buffer == bytearray(b'INFO ') or not self.buffer == bytearray(b'FOTO '):
                        raise InfoOrFoto()
                    elif self.buffer == bytearray(b'FOTO '):
                        self.info = False
                        self.photo = True
                    elif self.buffer == bytearray(b'INFO '):
                        self.info = True
                        self.photo = False
                elif len(self.buffer) > 5 and byte != b' ':
                    self.photo_length_buffer.extend(byte)
                elif byte == b' ':
                    self.counting_checksum = True
            elif self.photo:
                if self.read_photo_bytes <= int(self.photo_length_buffer): # reading photo data
                    self.checksum += ord(byte)
                    self.read_photo_bytes += 1
                elif self.read_photo_bytes <= int(self.photo_length_buffer) + 4: # reading last 4 bytes
                    self.counting_checksum = False
                    self.sent_checksum.extend(byte)
                    self.read_photo_bytes += 1
                    self.buffer = bytearray() # flush the buffer
                elif self.read_photo_bytes <= int(self.photo_length_buffer) + 6:
                    self.buffer.extend(byte)
                else:
                    if self.buffer == b'\r\n':
                        check = struct.unpack('>HH', self.sent_checksum)
                        check = str(check[0]) + str(check[1])
                        check = int(check)

                        return self.checksum == check
                    else:
                        raise FotoException()
                   
