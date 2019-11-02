import socket


class PhotoLengthNotNumber(BaseException):
    pass


class Buffer:
    def __init__(self, connection: socket):
        self.connection = connection
        self.buffer = bytearray()

    def __eq__(self, other: bytearray):
        return self.buffer == other

    def __len__(self,):
        return len(self.buffer)

    def read_password(self,*args, aprox_length):
        last_byte, curr_byte = b'', b''
        password = bytearray()
        read_bytes = 0

        while curr_byte != b'\n' or last_byte != b'\r':
            try:
                last_byte = curr_byte
                curr_byte = self.connection.recv(1, *args)
                read_bytes += 1
                if curr_byte == '':
                    return

                if read_bytes <= aprox_length:
                    password.extend(curr_byte)
                else:
                    pass
            except BlockingIOError as e:
                raise e
        try:
            return int(password)
        except ValueError:
            return

    def read_username(self, *args):
        last_byte,curr_byte = b'', b''
        username_processed = 0

        while curr_byte != b'\n' or last_byte != b'\r':
            try:
                last_byte = curr_byte
                curr_byte = self.connection.recv(1, *args)
                if curr_byte == '':
                    return
                username_processed += ord(curr_byte)
            except BlockingIOError as e:
                raise e

        return username_processed - ord(b'\r') - ord(b'\n')

    def read_line(self, *args, fake=False):
        self.buffer = bytearray()
        last_byte, curr_byte = b'', b''

        while curr_byte != b'\n' or last_byte != b'\r':
            try:
                last_byte = curr_byte
                if fake:
                    curr_byte = self.read_byte(fake=True)
                else:
                    curr_byte = self.connection.recv(1, *args)
                    self.buffer.extend(curr_byte)
                if curr_byte == '':
                    raise PhotoLengthNotNumber()

            except BlockingIOError as e:
                raise e
        return True

    def read_byte(self, *args, fake=False):
        data = self.connection.recv(1, *args)
        if not fake:
            self.buffer.extend(data)
        return data

    def read_photo_length(self,):
        self.buffer = bytearray()
        byte = b''
        while byte != b' ':
            byte = self.read_byte()

        buff = self.buffer[:-1]  # remove extra space at the end
        self.buffer = bytearray()
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