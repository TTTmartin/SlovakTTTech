#!/usr/bin/python

import threading
import time
import socket

wheelList = []
help_array = []

# Constants for speed control.
MOVE_FORWARD = 190
BRAKE = 90
MOVE_BACKWARD = 50


# Model for saving information about wheel IP address and number
class IpWheel:
    def __init__(self, ip, wheelNo):
        self.ipAddress = ip
        self.wheelNumber = wheelNo


class UdpListener(threading.Thread):
    def __init__(self, ip, port):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port

    def run(self):
        print("Starting thread")
        listen(self.ip, self.port)


def send_packet(ip, port, wheel_number):
    # join is faster '+' is an O(n^2) operation (compared to O(n) for join)
    # 0 - message from central unit
    # 1 - source board is raspberry pi
    # 1 - # of source board is 1
    # 0 - destination board is arduino
    # wheel_number - # of destination board
    # 1 - type of message is instruction
    data = "".join(["0110", str(wheel_number), "1", str(MOVE_FORWARD)])
    print(data)
    # calculate bad checksum, seen via Wireshark!!! diskutuj o tom
    sock = socket.socket(socket.AF_INET,  # Internet
                            socket.SOCK_DGRAM)  # UDP
    sock.sendto(data.encode(), (ip, 8000))


# Function to send speed instruction
def send_speed_instruction():
    for i in range(len(help_array)):
        print("IP address: ", help_array[i].ipAddress, "number: ", help_array[i].wheelNumber)

    # choose wheel, for example #2
    pom = [x for x in help_array if x.wheelNumber == 2]
    print(pom[0].ipAddress)
    send_packet(pom[0].ipAddress, 8000, pom[0].wheelNumber)


# Function to save received IP address of device.
# @data, data sent in packet
def wait_for_ip_address(data):
    # check for notified IP address
    if data[:2] == "10" and data[3:7] == "1100":
        wheelList.append(IpWheel(data[7:], data[2]))
        print("New wheel with ip ", wheelList[1].ipAddress)
        print("And number ", wheelList[1].wheelNumber)


# Function to listen on ip and port.
def listen(ip, port):
    global wheelList
    global help_array
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # variable for testing
    help_array.append(IpWheel("192.168.1.1", 1))
    help_array.append(IpWheel("192.168.1.2", 2))
    help_array.append(IpWheel("192.168.1.3", 3))
    help_array.append(IpWheel("192.168.1.4", 4))

    try:
        # bind IP and port
        sock.bind((ip, port))
    except socket.error:
        print("already bind")

    send_speed_instruction()
    while True:
        '''
        data, addr = sock.recvfrom(1024)
        print("receive message: ", data)

        # if not all IP address received
        if len(wheelList) != 4:
           wait_for_ip_address(data)
        send_speed_instruction()
        '''


        '''
        if data[:2] == "10" and data[3:7] == "1100":
            wheelList.append(IpWheel(data[7:], data[2]))
            print("New wheel with ip ", wheelList[1].ipAddress)
            print("And number ", wheelList[1].wheelNumber)
        '''



print("Program started")
wheelList.append(IpWheel("10.10", "6"))

UDP_IP = "147.175.182.7"
# UDP_IP = "192.168.1.200"
UDP_PORT = 5000

udpListenerThread = UdpListener(UDP_IP, UDP_PORT)
udpListenerThread.start()

print("End of main thread")


