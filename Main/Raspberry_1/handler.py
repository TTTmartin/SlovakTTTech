#!/usr/bin/python

import threading
import time
import socket

# Constants for UDP packets
from distlib.compat import raw_input

WHEEL_PORT = 5000

# Constants for data storage
wheelList = []
help_array = []


# Constants for speed control.
MOVE_FORWARD_MAX = 105
MOVE_FORWARD_AVERAGE = 95
SPEED_NEUTRAL = 90
MOVE_BACKWARD_MAX = 0
MOVE_BACKWARD_AVERAGE = 45

# Constants for direction decision
CAMERA_ANGLE_OK = 45

# Helper constants
camera_data = 80


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


def proces_laser(laser_data):
    return 1;


# Function to send UDP packet to devices in network
# @ip, IP address of device
# @port, specific port
# @wheel_number, specific wheel number
def send_packet(ip, port, wheel_number, speed):
    # join is faster '+' is an O(n^2) operation (compared to O(n) for join)
    # 0 - message from central unit
    # 1 - source board is raspberry pi
    # 1 - # of source board is 1
    # 0 - destination board is arduino
    # wheel_number - # of destination board
    # 01 - type of message is instruction
    print('tu')
    data = "".join(["0110", str(wheel_number), "01", str(speed)])
    # calculate bad checksum, seen via Wireshark!!! diskutuj o tom
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(data.encode(), (ip, WHEEL_PORT))


# Function to send speed instruction
def send_speed_instruction():
    print('tu')
    for wheel in wheelList:
        # print(" IP address: ", wheel.ipAddress, "number: ", wheel.wheelNumber)
        send_packet(wheel.ipAddress, WHEEL_PORT, wheel.wheelNumber, MOVE_FORWARD_MAX)

    '''# send faster speed to right wheels and slower to left wheels
    if (proces_laser("10")) and (camera_data > CAMERA_ANGLE_OK):
        # choose wheel from list
        wheel = [x for x in help_array if x.wheelNumber == 1]
        send_packet(wheel[0].ipAddress, WHEEL_PORT, 1, MOVE_FORWARD_MAX)
        wheel = [x for x in help_array if x.wheelNumber == 3]
        send_packet(wheel[0].ipAddress, WHEEL_PORT, 3, MOVE_FORWARD_MAX)
        wheel = [x for x in help_array if x.wheelNumber == 2]
        send_packet(wheel[0].ipAddress, WHEEL_PORT, 2, MOVE_BACKWARD_AVERAGE)
        wheel = [x for x in help_array if x.wheelNumber == 4]
        send_packet(wheel[0].ipAddress, WHEEL_PORT, 4, MOVE_BACKWARD_AVERAGE)

    # send faster speed to left wheels and slower to right wheels
    if (proces_laser("10")) and (camera_data < CAMERA_ANGLE_OK):
        # choose wheel from list
        wheel = [x for x in help_array if x.wheelNumber == 1]
        send_packet(wheel[0].ipAddress, WHEEL_PORT, 1, MOVE_BACKWARD_AVERAGE)
        wheel = [x for x in help_array if x.wheelNumber == 3]
        send_packet(wheel[0].ipAddress, WHEEL_PORT, 3, MOVE_BACKWARD_AVERAGE)
        wheel = [x for x in help_array if x.wheelNumber == 2]
        send_packet(wheel[0].ipAddress, WHEEL_PORT, 2, MOVE_FORWARD_MAX)
        wheel = [x for x in help_array if x.wheelNumber == 4]
        send_packet(wheel[0].ipAddress, WHEEL_PORT, 4, MOVE_FORWARD_MAX)
    '''

    # choose wheel, for example #2
    # pom = [x for x in help_array if x.wheelNumber == 2]
    # print(pom[0].ipAddress)
    # send_packet(pom[0].ipAddress, 8000, pom[0].wheelNumber)


# Function to save received IP address of device.
# @data, data sent in packet
def wait_for_ip_address(data):
    # check for notified IP address
    if data[:2] == '10' and data[3:7] == '1100':
        new_wheel = IpWheel(data[7:], data[2])
        wheelList.append(new_wheel)
        #print("New wheel with ip ", new_wheel.ipAddress)
        #print("And number ", new_wheel.wheelNumber)


# Function to listen on ip and port.
def listen(ip, port):
    global wheelList
    global help_array
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        # bind IP and port
        sock.bind((ip, port))
    except socket.error:
        print("already bind")

        #send_speed_instruction()
    while True:

        data, addr = sock.recvfrom(1024)
        #print("receive message: ", data.decode())

        # if not all IP address received
        if len(wheelList) < 4:
            wait_for_ip_address(data.decode())
            print(len(wheelList))
        if len(wheelList) == 4:
            for wheel in wheelList:
                print(" IP address: ", wheel.ipAddress, "number: ", wheel.wheelNumber)
                if wheel.wheelNumber == '1' or wheel.wheelNumber == '4':
                    send_packet(wheel.ipAddress, WHEEL_PORT, wheel.wheelNumber, 110)
                if wheel.wheelNumber == '2' or wheel.wheelNumber == '3':
                    send_packet(wheel.ipAddress, WHEEL_PORT, wheel.wheelNumber, 50)

            '''userInput = raw_input('WASD: ')
            if userInput == 'w':
                send_speed_instruction(10)
                # send_packet(wheelList[0].ipAddress, WHEEL_PORT, wheelList[0].wheelNumber, MOVE_FORWARD_MAX)
'''

print("Program started")

UDP_IP = "192.168.1.200"
# UDP_IP = "192.168.1.200"
UDP_PORT = 5000

udpListenerThread = UdpListener(UDP_IP, UDP_PORT)
udpListenerThread.start()

print("End of main thread")


