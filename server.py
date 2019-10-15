# #!/usr/bin/env python3
import socket

import sys
import threading

from ClientHandler import ClientHandler

HOST = '0.0.0.0' # all availabe interfaces
PORT = 3000 # arbitrary non privileged port

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
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

# The code below is what you're looking for ############


while True:
    # blocking call, waits to accept a connection
    conn, addr = s.accept()

    print("[-] Connected to " + addr[0] + ":" + str(addr[1]))
    conn.send(b"200 LOGIN\r\n")
    event = threading.Event()
    client = ClientHandler(conn)
    client.start()
    client.join(timeout=15.0)
    # if client.is_alive():
    #     client.join()

s.close()