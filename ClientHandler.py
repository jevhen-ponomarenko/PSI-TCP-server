import time
from _socket import socket
import threading
from functools import reduce
from typing import List

from Buffer import Buffer

from Buffer import RobotNotInUsername, InfoOrFoto, FotoException, BadCheckSum


class ClientHandler(threading.Thread):
    FIRST_MESSAGE = '201 PASSWORD\r\n'
    SECOND_MESSAGE = '202 OK\r\n'

    LOGIN_FAILED = '500 LOGIN FAILED\r\n'
    SYNTAX_ERROR = '501 SYNTAX ERROR\r\n'
    TIMEOUT = '502 TIMEOUT\r\n'

    BAD_CHECKSUM = '300 BAD CHECKSUM\r\n'

    def __init__(self, connection: socket):
        self.connection = connection
        self.buffer = Buffer()
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

    def run(self,):
        while not self.stop_event.is_set():
            if time.time() - self.start_time >= 45:
                self.end_with_message(self.TIMEOUT)
                print(f'stopped {self.ident} thread: TIMEOUT')
                return
            data = self.connection.recv(1)
            if self.buffer.state == 0:
                # TODO> fix case of ROBOT NOT in username
                try:
                    username_sum = self.buffer.process_byte(data)
                    if username_sum:
                        self.username = username_sum
                        self.connection.sendall(self.FIRST_MESSAGE.encode())
                except RobotNotInUsername:
                    self.username_wrong = True
            elif self.buffer.state == 1:
                password = self.buffer.process_byte(data)
                if password:
                    try:
                        int_from_password = int(password)
                    except ValueError:
                        self.end_with_message(self.LOGIN_FAILED)
                        print('------------' * 5)
                        print(vars(self.buffer))
                        print('------------' * 5)
                        print(f'stopped {self.ident} thread: LOGIN_FAILED')
                        return
                    if self.username_wrong:
                        self.end_with_message(self.LOGIN_FAILED)
                        print('------------' * 5)
                        print(vars(self.buffer))
                        print('------------' * 5)
                        print(f'stopped {self.ident} thread: LOGIN_FAILED')
                        return
                    if int_from_password == self.username:
                        self.connection.sendall(self.SECOND_MESSAGE.encode())
                    else:
                        self.end_with_message(self.LOGIN_FAILED)
                        print('------------' * 5)
                        print(vars(self.buffer))
                        print('------------' * 5)
                        print(f'stopped {self.ident} thread: LOGIN_FAILED')
                        return
            elif self.buffer.state == 2:
                try:
                    reading_succ = self.buffer.process_byte(data)
                    if reading_succ:
                        self.connection.sendall(self.SECOND_MESSAGE.encode())
                except BadCheckSum:
                    self.connection.sendall(self.BAD_CHECKSUM.encode())
                except FotoException:
                    print(f'stopped {self.ident} thread: SYNTAX_ERROR')
                    self.end_with_message(self.SYNTAX_ERROR)
                    return
                except InfoOrFoto:
                    print('------------' * 5)
                    print(vars(self.buffer))
                    print('------------' * 5)
                    print(f'stopped {self.ident} thread: SYNTAX_ERROR')
                    self.end_with_message(self.SYNTAX_ERROR)
                    return
        print('------------' * 5)
        print(vars(self.buffer))
        print('------------' * 5)
        print(f'stopped {self.ident} thread: END')
        return

    def join(self, **kwargs):
        if not self.stop_event.is_set():
            self.stop_event.set()
        super().join(**kwargs)






