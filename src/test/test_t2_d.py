import socket
import sys

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
server_address = ('', 8890)
sock.bind(server_address)

while True:
    print ('\nwaiting to receive message')
    data, address = sock.recvfrom(1024)
    
    print('received %s bytes from %s' % (len(data), address))
    print(data)