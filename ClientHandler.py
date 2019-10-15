from _socket import socket
import threading
from functools import reduce
from typing import List

from Buffer import Buffer


class ClientHandler(threading.Thread):
    FIRST_MESSAGE = '201 PASSWORD\r\n'
    SECOND_MESSAGE = '202 OK\r\n'

    LOGIN_FAILED = '500 LOGIN FAILED\r\n'
    SYNTAX_ERROR = '501 SYNTAX ERROR\r\n'
    TIMEOUT = '502 TIMEOUT\r\n'

    BAD_CHECKSUM = '300 BAD CHECKSUM\r\n'

    def __init__(self, connection: socket):
        super().__init__()
        self.connection = connection
        self.buffer = Buffer()
        self.step = 0
        self.username = None
        self.stop_event = threading.Event()
        self.bad_checksum = threading.Event()
        self.syntax = threading.Event()

    def end_with_message(self, message):
        self.connection.sendall(message.encode())
        self.connection.close()


    def run(self,):
        while not self.stop_event.is_set():
            data = self.connection.recvmsg(1)
            if not self.buffer.add_byte(data):
                res = self.handle_message(self.buffer.get_last_message())
                if not res:
                    self.stop_event.set()
                    break
                self.connection.sendall(res.encode())
        if self.bad_checksum.is_set():
            self.end_with_message(self.BAD_CHECKSUM)
        return
    def join(self, **kwargs):
        if not self.stop_event.is_set():
            self.connection.sendall(self.TIMEOUT.encode())
            self.stop_event.set()
        super().join(**kwargs)
        
    def handle_message(self, message: str):
        message_word_list = message.decode().split(' ')
        return self.create_response(message_word_list)

    def create_response(self, words: list)->str:
        if self.step == 0:
            self.step += 1
            self.handle_first_step(words)
            return self.FIRST_MESSAGE
        elif self.step == 1:
            self.step += 1
            if self.handle_second_step(words):
                return self.SECOND_MESSAGE
            else:
                self.stop_event.set()
                self.bad_checksum.set()
                return None
        elif self.step == 2:
            return self.handle_third_step(words)

    def handle_first_step(self, words: List):
        self.username = words[0]
        return True

    def handle_second_step(self, words: List):
        password = reduce(lambda x, y: x+y, list(map(ord, [x for x in self.username])))
        try:
            entered_pass = int(words[0])
        except Exception:
            return False
        return password == entered_pass





