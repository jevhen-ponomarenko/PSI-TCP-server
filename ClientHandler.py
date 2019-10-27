import struct
import time
from _socket import socket
import threading
from functools import reduce
from typing import List

from Buffer import Buffer, PhotoLengthNotNumber


class RobotNotInUsername(Exception):
    pass


class InfoOrFoto(Exception):
    pass


class FotoException(Exception):
    pass


class BadCheckSum(Exception):
    pass


class WrongSyntax(Exception):
    pass

class WrongPassword(Exception):
    pass


# noinspection PyMethodMayBeStatic
class ClientHandler(threading.Thread):
    FIRT_MESSAGE = '200 LOGIN\r\n'
    PASSWORD_MESSAGE = '201 PASSWORD\r\n'
    SECOND_MESSAGE = '202 OK\r\n'

    LOGIN_FAILED = '500 LOGIN FAILED\r\n'
    SYNTAX_ERROR = '501 SYNTAX ERROR\r\n'
    TIMEOUT = '502 TIMEOUT\r\n'

    BAD_CHECKSUM = '300 BAD CHECKSUM\r\n'

    def __init__(self, connection: socket):
        self.time_start = time.time()
        self.connection = connection
        self.buffer = Buffer(connection)
        self.step = 0
        self.username = None
        self.stop_event = threading.Event()
        self.username_wrong = None
        self.start_time = time.time()
        super().__init__()

    def end_with_message(self, message):
        self.connection.sendall(message.encode())
        self.connection.close()
        self.stop_event.set()

    def send_message(self, message: str):
        self.connection.sendall(message.encode())

    def run(self,):
        if not self.handle_login():
            self.end_with_message(self.LOGIN_FAILED)
            return

        while not self.stop_event.is_set():
            if time.time() - self.start_time >= 45:
                self.end_with_message(self.TIMEOUT)
                break
            try:
                self.handle_command()
            except FotoException:
                self.end_with_message(self.SYNTAX_ERROR)
                break
            except PhotoLengthNotNumber:
                self.end_with_message(self.SYNTAX_ERROR)
                break
            except BadCheckSum:
                self.send_message(self.BAD_CHECKSUM)
            except WrongSyntax:
                self.end_with_message(self.SYNTAX_ERROR)
                break
        return

    def join(self, **kwargs):
        if not self.stop_event.is_set():
            self.stop_event.set()
        super().join(**kwargs)

    def handle_login(self):
        self.send_message(self.FIRT_MESSAGE)
        username = self.buffer.read_line()
        self.send_message(self.PASSWORD_MESSAGE)
        password = self.buffer.read_line()
        try:
            if self.validate_password(password, username):
                self.send_message(self.SECOND_MESSAGE)
                return True
            else:
                return False
        except WrongPassword:
            return False

    def handle_command(self):
        while True:
            self.buffer.read_byte()
            if not self.buffer.possible_start_info() and not self.buffer.possible_start_photo():
                raise WrongSyntax()
            elif self.buffer == b'INFO ':
                self.handle_info()
                break
            elif self.buffer == b'FOTO ':
                self.handle_photo()
                break
            elif len(self.buffer) > 5:
                raise WrongSyntax()

    def validate_password(self, password: bytearray, username: bytearray) -> bool:
        computed_password = 0
        for byte in username:
            computed_password += byte

        if len(username) < 5:
            return False
        elif len(username) > 5 and username[:5] != b'Robot':
            return False
        else:
            try:
                password = int(password)
                return computed_password == password
            except ValueError:
                raise WrongPassword()

    def handle_photo(self):
        with open(f'photo{self.ident}', 'wb') as f:
            bytes_to_read = self.buffer.read_photo_length()
            read_bytes = 0
            checksum = 0
            while read_bytes < bytes_to_read:
                byte = self.buffer.read_byte()
                f.write(byte)
                checksum += ord(byte)
                read_bytes += 1

        sent_checksum = bytearray()
        
        for i in range(4):
            byte = self.buffer.read_byte()
            sent_checksum.extend(byte)

        parsed_checksum = struct.unpack('>HH', sent_checksum)
        parsed_checksum = str(parsed_checksum[0]) + str(parsed_checksum[1])
        parsed_checksum = int(parsed_checksum)
        
        if parsed_checksum == checksum:
            return True
        else:
            raise BadCheckSum()

    def handle_info(self):
        msg = self.buffer.read_line()
        # print(msg.decode() + '-------' + str(self.ident) + '-------')
        self.send_message(self.SECOND_MESSAGE)



