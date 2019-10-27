import socket
import struct


class PhotoLengthNotNumber(BaseException):
    pass


class Buffer:
    def __init__(self, connection: socket):
        self.connection = connection
        self.buffer = bytearray()
        # self.photo_length_buffer = bytearray()
        # self.state = 0  # only 0 and 1 is allowed
        # self.photo = None
        # self.info = None
        # self.checksum = 0
        # self.sent_checksum = bytearray()
        # self.read_photo_bytes = 0
        # self.password = 0
        # self.last_byte = None
        # self.counting_pass = False
        # self.counting_checksum = False
        # self.data = bytearray()
        # self.file = open(f"guru99.{self.__hash__()[0:5]}", "w+")

    def __eq__(self, other: bytearray):
        return self.buffer == other

    def __len__(self,):
        return len(self.buffer)

    def read_line(self,):
        self.buffer = bytearray()
        last_byte, curr_byte = b'', b''

        while curr_byte != b'\n' or last_byte != b'\r':
            try:
                last_byte = curr_byte
                curr_byte = self.connection.recv(1)
                self.buffer.extend(curr_byte)
            except Exception as e:
                raise e
        # skip the esc sequence
        buff = self.buffer[:-2]
        self.buffer = bytearray()
        return buff

    def read_byte(self,):
        data = self.connection.recv(1)
        self.buffer.extend(data)
        return data

    def read_photo_length(self,):
        self.buffer = bytearray()
        byte = b''
        while byte != b' ':
            byte = self.read_byte()

        buff = self.buffer[:-1]  # remove extra space at the end
        try:
            num = int(buff)
            return num
        except ValueError:
            raise PhotoLengthNotNumber()


    def possible_start_info(self):
        info = b'INFO '
        length = min(len(self.buffer), 5)
        return info[:length] == self.buffer[:length]

    def possible_start_photo(self):
        photo = b'FOTO '
        length = min(len(self.buffer), 5)
        return photo[:length] == self.buffer[:length]



    # def process_byte(self, byte: bytes) -> bool or int:
    #     pass
    #     # """
    #     # Adds byte to a buffer, takes care of handling escape characters
    #     # :param byte:
    #     # :return: True on success, bytesarray() on escape seq
    #     # """
    #     if self.state == 0:
    #         if self.counting_pass and byte == b'\n' and self.last_byte == b'\r':  # escape sequence
    #             self.password -= ord(b'\r')  # bc \r is end seq, we dont want to count that
    #             self.state = 1
    #             self.counting_pass = False
    #             self.buffer = bytearray()
    #             return self.password
    #
    #         if not self.counting_pass:
    #             if byte == b'\n' and self.last_byte == b'\r':
    #                 self.state = 1
    #                 return self.password
    #             self.last_byte = byte
    #             self.buffer.extend(byte)
    #             self.password += ord(byte)
    #             if len(self.buffer) == 5:
    #                 if not self.buffer == bytearray(b'Robot'):
    #                     self.counting_pass = True
    #                     raise RobotNotInUsername()
    #                 else:
    #                     self.counting_pass = True
    #                     return None
    #         else:
    #             self.last_byte = byte
    #             try:
    #                 self.password += ord(byte)
    #             except TypeError:
    #                 pass
    #             return None
    #
    #     elif self.state == 1:
    #         if byte == b'\n' and self.last_byte == b'\r':  # escape sequence
    #             self.state = 2
    #             ret = self.buffer[:-1]
    #             self.buffer = bytearray()  # flush it
    #             return ret
    #         else:
    #             self.buffer.extend(byte)
    #             self.last_byte =byte
    #             return None
    #
    #     elif self.state == 2:
    #         if not self.counting_checksum:
    #
    #             if len(self.buffer) < 5:
    #                 if self.last_byte and self.last_byte == b'\r' and byte == b'\n':
    #                     raise InfoOrFoto()
    #                 self.last_byte = byte
    #                 self.buffer.extend(byte)
    #             elif len(self.buffer) == 5:
    #                 if self.buffer != bytearray(b'INFO ') and self.buffer != bytearray(b'FOTO '):
    #                     raise InfoOrFoto()
    #                 elif self.buffer == bytearray(b'FOTO '):
    #                     self.info = False
    #                     self.photo = True
    #                     self.photo_length_buffer.extend(byte)  # one byte of length is loaded in memory now
    #                     self.buffer.extend(byte)  # too keep this bullshit working
    #                 elif self.buffer == bytearray(b'INFO '):
    #                     self.info = True
    #                     self.photo = False
    #                     self.buffer.extend(byte)
    #                     self.last_byte = byte
    #             elif byte == b' ' and self.photo:
    #                 self.counting_checksum = True
    #             elif byte != b' ' and self.photo:
    #                 if self.last_byte and self.last_byte == b'\r' and byte == b'\n':
    #                     raise FotoException()
    #                 self.last_byte = byte
    #                 self.photo_length_buffer.extend(byte)
    #             elif self.last_byte == b'\r' and byte == b'\n':
    #                 self.buffer = bytearray()  # i think its INFO case
    #                 return True
    #             elif not self.photo:
    #                 self.last_byte = byte
    #             else:
    #                 raise InfoOrFoto()
    #         elif self.counting_checksum and self.photo:
    #             self.data.extend(byte)  # just for testing
    #             if self.last_byte and self.last_byte == b'\r' and byte == b'\n' and self.read_photo_bytes <= int(self.photo_length_buffer) + 4:
    #                 self.delete_photo_params()
    #                 raise BadCheckSum()
    #             self.last_byte = byte
    #             if self.read_photo_bytes < int(self.photo_length_buffer):  # reading photo data
    #                 self.checksum += ord(byte)
    #                 self.read_photo_bytes += 1
    #             elif self.read_photo_bytes < int(self.photo_length_buffer) + 4:  # reading last 4 bytes
    #
    #                 self.sent_checksum.extend(byte)
    #                 self.read_photo_bytes += 1
    #                 self.buffer = bytearray()  # flush the buffer
    #             elif self.read_photo_bytes < int(self.photo_length_buffer) + 6:
    #                 self.buffer.extend(byte)
    #                 self.read_photo_bytes += 1
    #                 if self.read_photo_bytes == int(self.photo_length_buffer) + 6:
    #                     if self.buffer == b'\r\n':
    #                         check = struct.unpack('>HH', self.sent_checksum)
    #                         check = str(check[0]) + str(check[1])
    #                         check = int(check)
    #                         if self.checksum == check:
    #                             print(str(self.data) + f'----{self.password}----')
    #                             self.delete_photo_params()
    #                             return True
    #                         else:
    #                             print(str(self.data) + f'----{self.password}----')
    #                             self.delete_photo_params()
    #                             raise BadCheckSum()
    #                     else:
    #                         if self.last_byte and self.last_byte == b'\r' and byte == b'\n':
    #                             print(str(self.data) + f'----{self.password}----')
    #                             self.delete_photo_params()
    #                             raise BadCheckSum()
    #                         self.last_byte = byte
    #
    #             else:
    #                 raise FotoException()
    #         elif not self.photo:  # reading INFO
    #             self.data.extend(byte)
    #             if byte == b'\n' and self.last_byte == b'\r':  # escape sequence
    #                 print(f'--------'*5)
    #                 print(f'----{self.password}----')
    #                 print(self.data)
    #                 print(f'--------' * 5)
    #                 self.delete_photo_params()
    #                 return True
    #             else:
    #                 self.last_byte = byte
    #                 self.buffer.extend(byte)
    #         else:
    #             self.delete_photo_params()
    #             raise InfoOrFoto()

    def delete_photo_params(self):
        """ gets called after reading FOTO msg, in all cases"""
        # self.buffer = bytearray()
        # self.photo_length_buffer = bytearray()
        # self.photo = None
        # self.info = None
        # self.checksum = 0
        # self.sent_checksum = bytearray()
        # self.read_photo_bytes = 0
        # self.last_byte = None
        # self.counting_pass = False
        # self.counting_checksum = False
        # self.data = bytearray()
        pass