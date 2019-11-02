import struct
import threading
import time
from _socket import socket, MSG_DONTWAIT

import settings
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
        t = threading.Timer(45, self.after_done)
        t.start()
        super().__init__()

    def after_done(self):
        if self.stop_event.is_set():
            return
        self.end_with_message(self.TIMEOUT)

    def end_with_message(self, message):
        self.stop_event.set()
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
            if time.time() - self.start_time >= (45 if settings.AWS else 1000000):
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
        username = self.buffer.read_username()
        print(str(username) + '+++++' + str(self.ident))
        self.send_message(self.PASSWORD_MESSAGE)
        password = self.buffer.read_password(aprox_length=len(str(username)))
        print(str(password) + '!!!!!!' + str(self.ident))
        try:
            if password == username:
                self.send_message(self.SECOND_MESSAGE)
                return True
            else:
                return False
        except WrongPassword:
            return False

    def handle_command(self):
        while True:
            curr_byte = self.buffer.read_byte()
            if curr_byte == '':
                raise WrongSyntax()
            if not self.buffer.possible_start_info() and not self.buffer.possible_start_photo():
                raise WrongSyntax()
            elif self.buffer == b'INFO ':
                try:
                    self.handle_info()
                except BlockingIOError:
                    self.end_with_message(self.SYNTAX_ERROR)
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
        with open(f'out{self.ident}', 'wb') as f:
            bytes_to_read = self.buffer.read_photo_length()
            read_bytes = 0
            checksum = 0
            while read_bytes < bytes_to_read:
                try:
                    byte = self.buffer.read_byte(MSG_DONTWAIT, fake=True)
                except BlockingIOError:
                    self.end_with_message(self.SYNTAX_ERROR)

                f.write(byte)
                checksum += ord(byte)
                read_bytes += 1

        sent_checksum = bytearray()
        
        for i in range(4):
            try:
                byte = self.buffer.read_byte(fake=True)
            except BlockingIOError:
                raise BadCheckSum()
            sent_checksum.extend(byte)
        parsed_checksum = struct.unpack('>HH', sent_checksum)
        parsed_checksum = str(parsed_checksum[0]) + str(parsed_checksum[1])
        parsed_checksum = int(parsed_checksum)

        # if not settings.AWS:  # this thingy is in settings module, telnet sends \r\n at the end of every message
        #     for i in range(2):
        #         self.buffer.read_byte(fake=True)

        if parsed_checksum == checksum:
            self.send_message(self.SECOND_MESSAGE)
        else:
            raise BadCheckSum()

    def handle_info(self):
        try:
            self.buffer.read_line(fake=True)
            self.send_message(self.SECOND_MESSAGE)
        except PhotoLengthNotNumber:
            self.end_with_message(self.SYNTAX_ERROR)


