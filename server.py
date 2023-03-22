import os
import sys
import socket
import struct

data_to_send = 100 * 1000 ** 2

print("Creating socket...")
try:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 262)
    print("Using mptcp...")
except:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Using tcp...")

print("Binding port...")
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("10.0.2.2", 12345))

print("Listening...")
server_socket.listen()

client_socket, client_address = server_socket.accept()
print("Accepted connection...")

print("Sending data...")
random_bytes = os.urandom(data_to_send)
client_socket.sendall(random_bytes)

client_socket.close()
server_socket.close()
