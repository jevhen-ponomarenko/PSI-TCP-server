# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import socket
import sys

# Create a TCP/IP socket
import time

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
server_address = ('0.0.0.0', 3000)
sock.connect(server_address)

try:

    # Send data
    message = b'1'
    sock.sendall(message)

    # Look for the response
    amount_received = 0
    amount_expected = len(message)

    time.sleep(15)

finally:
    print('closing socket')
    sock.close()

