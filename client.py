import os
import sys
import time
import socket
import struct

data_to_receive = 100 * 1000 ** 2

start_time = time.time()

print("Creating socket...")
try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 262)
    print("Using mptcp...")
except:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Using tcp...")

print("Connecting to server...")
client_socket.connect(("10.0.2.2", 12345))

print("Receiving data...")
amount_received = 0
while amount_received < data_to_receive:
    data = client_socket.recv(15 * 1024)
    amount_received += len(data)

transfer_time = time.time() - start_time
print("Total time:", transfer_time, "seconds")
print("Amount bytes received:", amount_received, "bytes")
actual_throughput = round(((amount_received / 1000000) * 8) / transfer_time, 2)
print("Actual throughput:", actual_throughput, "Mbps")

client_socket.close()
