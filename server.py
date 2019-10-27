# #!/usr/bin/env python3
import socket

import sys
import threading
import time

from ClientHandler import ClientHandler

HOST = '0.0.0.0' # all availabe interfaces
PORT = 3000 # arbitrary non privileged port

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
except socket.error as msg:
    print("Could not create socket. Error Code: ", str(msg[0]), "Error: ", msg[1])
    sys.exit(0)

print("[-] Socket Created")

# bind socket
try:
    s.bind((HOST, PORT))
    print("[-] Socket Bound to port " + str(PORT))
except socket.error as msg:
    print("Bind Failed. Error Code: {} Error: {}".format(str(msg[0]), msg[1]))
    sys.exit()

s.listen(10)
print("Listening...")

while True:
    # blocking call, waits to accept a connection
    conn, addr = s.accept()

    print("[-] Connected to " + addr[0] + ":" + str(addr[1]))

    client = ClientHandler(conn)
    client.start()

s.close()