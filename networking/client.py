import os
import sys
import time
import socket
import struct

socket.IPPROTO_MPTCP

if __name__ == '__main__':

    data_request_size = int(sys.argv[1])

    start_time = time.time()

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 262)
        print("Using mptcp...")
    except:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Using tcp...")

    client_socket.settimeout(None)

    buffer_size = 65536  # Adjust this value as needed
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, buffer_size)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_size)

    client_socket.connect(("10.0.2.2", 12345))

    packed = struct.pack("<Q", data_request_size)

    client_socket.sendall(packed)

    amount_received = 0

    while amount_received < data_request_size:
        data = client_socket.recv(15 * 1024)
        amount_received += len(data)

    print("\tTotal time:", time.time() - start_time, "seconds")
    print("\tAmount bytes received:", amount_received)

    client_socket.close()
