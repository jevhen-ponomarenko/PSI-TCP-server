import queue

class Buffer:
    def __init__(self):
        self.buffer = bytearray()
        self.msg_queue = queue.Queue(0)

    def is_full(self):
        return len(self.buffer) >= 1024

    def add_byte(self, byte: bytes):
        # """
        # Adds byte to a buffer, takes care of handling escape characters
        # :param byte:
        # :return: True on success, bytesarray() on escape seq
        # """
        # if self.is_full():
        #     self.msg_queue.put((self.flush(), None))
        #     return True
        if byte == b'\n' and self.buffer[-1:] == b'\r':  # escape sequence
            self.msg_queue.put(self.flush())
            return False
        else:
            self.buffer.extend(byte)
            return True

    def flush(self):
        ret = self.buffer[:-1]
        self.buffer = bytearray()
        return ret

    def get_last_message(self):
        try:
            return self.msg_queue.get()
        except Exception as e:
            print(e)
