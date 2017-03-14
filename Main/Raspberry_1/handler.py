#!/usr/bin/python

import threading
import time
import socket
import datetime


# Constants for UDP packets
# from distlib.compat import raw_input

# Port on which Arduino is listening.
WHEEL_PORT = 5000

# Constants for data storage
wheelList = []
laserList = []
help_array = []

# file for logging
log_file = ""

# Constants for speed control.
MOVE_FORWARD = 105
SPEED_NEUTRAL = 90
MOVE_BACKWARD = 20

# Constants for laser processing.
MIN_DISTANCE = 50
DIRECTION = 190
ANGLE_CONSTANT = 10

INDEX_OF_PACKET_BYTE = 0

# Model for saving information about wheel IP address and number
class IpWheel:
    def __init__(self, ip, wheelNo):
        self.ipAddress = ip
        self.wheelNumber = wheelNo
        write_log(' New wheel registered: #' + str(wheelNo) + ', ' + ip)


# Model for storage laser data
class LaserData:
    def __init__(self, startAngle, startDistance, endAngle, endDistance):
        self.startAngle = startAngle
        self.startDistance = startDistance
        self.endAngle = endAngle
        self.endDistance = endDistance
        self.startComputedAngle = {True: abs(startAngle - DIRECTION), False: abs(360 - startAngle + DIRECTION)}[self.startAngle <= DIRECTION + 180]
        self.endComputedAngle = {True: abs(endAngle - DIRECTION), False: abs(360 - endAngle + DIRECTION)}[self.endAngle <= DIRECTION + 180]
        self.directionAngle = {True: self.startAngle, False: self.endAngle}[self.startComputedAngle <= self.endComputedAngle]
        write_log(' New laser data: startAngle: ' + str(startAngle) + ' startDistance: ' + str(startDistance) + ' endAngle: ' + str(endAngle) + ' endDistance: ' + str(endDistance))
        print("STARTCOMPUTED: " + str(self.startComputedAngle))
        print("ENDCOMPUTED: " + str(self.endComputedAngle))

# Initializing UDP communication.
class UdpListener(threading.Thread):
    # Constructor
    def __init__(self, ip, port):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port

    # Run function
    def run(self):
        write_log(' start thread')
        listen(self.ip, self.port)


# Function for processing laser packet.
def process_laser(laser_message):
    # laser_message = "010201010100050200C8001E015E005000A005DC00B30037"
    # count of records
    # convert 2 bytes to int representation of their hex value
    number_of_records = int(
        "".join([laser_message[INDEX_OF_PACKET_BYTE + 14], laser_message[INDEX_OF_PACKET_BYTE + 15]]), 16)
    print("count of lase data: ", number_of_records)
    print("laser data: \n")
    laser_list = []
    index = 0
    count = 0
    # iterating over numbers of road side data from camera, message[6] represents count of numbers
    for index in range(0, number_of_records):
        # TODO: save to structure
        # get specific entry
        start_angle = int("".join(
            [laser_message[INDEX_OF_PACKET_BYTE + 16 + count], laser_message[INDEX_OF_PACKET_BYTE + 16 + count + 1],
             laser_message[INDEX_OF_PACKET_BYTE + 16 + count + 2],
             laser_message[INDEX_OF_PACKET_BYTE + 16 + count + 3]]), 16)
        start_distance = int("".join([laser_message[INDEX_OF_PACKET_BYTE + 16 + count + 4],
                                      laser_message[INDEX_OF_PACKET_BYTE + 16 + count + 5],
                                      laser_message[INDEX_OF_PACKET_BYTE + 16 + count + 6],
                                      laser_message[INDEX_OF_PACKET_BYTE + 16 + count + 7]]), 16)
        end_angle = int("".join([laser_message[INDEX_OF_PACKET_BYTE + 16 + count + 8],
                                 laser_message[INDEX_OF_PACKET_BYTE + 16 + count + 9],
                                 laser_message[INDEX_OF_PACKET_BYTE + 16 + count + 10],
                                 laser_message[INDEX_OF_PACKET_BYTE + 16 + count + 11]]), 16)
        end_distance = int("".join([laser_message[INDEX_OF_PACKET_BYTE + 16 + count + 12],
                                    laser_message[INDEX_OF_PACKET_BYTE + 16 + count + 13],
                                    laser_message[INDEX_OF_PACKET_BYTE + 16 + count + 14],
                                    laser_message[INDEX_OF_PACKET_BYTE + 16 + count + 15]]), 16)
        laser_list.append(LaserData(start_angle, start_distance, end_angle, end_distance))
        print(start_angle)
        print(start_distance)
        print(end_angle)
        print(end_distance)
        print("\n")

        count += 16
    return laser_list


# Finds closest clear degrees to direction degree
# returns 2 fields with degree, first is the closer one
# @direction, main degree
# @range_list, list of degrees 0-359 d-distance 0-blocked
def find_closest_degree(direction, laser_data_list):
    left = 0
    right = 0

    laser_data_list.sort(key=lambda x: x.startComputedAngle)
    startAngle = laser_data_list[0]
    laser_data_list.sort(key=lambda x: x.endComputedAngle)
    endAngle = laser_data_list[0]

    move_forward_right_flag = 0
    move_forward_left_flag = 0
    move_forward_flag = 0
    for data in laser_data_list:
        if (data.startAngle < DIRECTION < data.endAngle):
            move_forward_flag = 1
        if (data.startAngle < (DIRECTION + ANGLE_CONSTANT) % 360 < data.endAngle):
            move_forward_right_flag = 1
        if (data.startAngle < (DIRECTION - ANGLE_CONSTANT) % 360 < data.endAngle):
            move_forward_left_flag = 1

    # direction clean and also with angle constants
    if(move_forward_flag and move_forward_left_flag and move_forward_left_flag):
        move_vehicle(MOVE_FORWARD)
    # direction clean, right stop
    elif(move_forward_flag and move_forward_right_flag == 0):
        turn_vehicle(1, MOVE_FORWARD)
    # direction clean, left stop
    elif(move_forward_flag and move_forward_left_flag == 0):
        turn_vehicle(0, MOVE_FORWARD)
    # find closest angle
    else:
        closestAngle = {True: startAngle, False: endAngle}[startAngle.startComputedAngle <= endAngle.endComputedAngle]
        print("Win: " + str(closestAngle.directionAngle))
        if(closestAngle.directionAngle >=180):
            turn_vehicle(1, MOVE_FORWARD)
        else:
            turn_vehicle(0, MOVE_FORWARD)
    '''
    x = direction
    while range_list[x] != 1:
        right += 1
        x = (x + 1) % 360

    x = direction
    while range_list[x] != 1:
        left += 1
        x = (x - 1) % 360

    if (right < left):
        return [(direction + right) % 360, (direction - left) % 360]
    elif (left < right):
        return [(direction - left) % 360, (direction + right) % 360]
    else:
        return [(direction + right) % 360, (direction - left) % 360]
    '''

# Process laser data.
# @laser_data, free angles.
def proces_laser_data(laser_data):
    free_angle = find_closest_degree(0, laser_data)[0]

    # stop vehicle befor turning
    move_vehicle(SPEED_NEUTRAL)

    # move left
    if free_angle >= 180:
        turn_vehicle(1, MOVE_FORWARD)
    # move straight ahead
    elif free_angle == 0:
        move_vehicle(MOVE_FORWARD)
    # move right
    else:
        turn_vehicle(0, MOVE_FORWARD)
    return 1;


# Function for logging.
# @message, string to write to file.
def write_log(message):
    log_file = open('control_unit_log', 'a')
    log_file.write(str(datetime.datetime.now()) + message + '\n')
    log_file.close()


# Function to send UDP packet to devices in network specifying speed.
# @ip, IP address of device
# @port, specific port
# @wheel_number, specific wheel number
def send_speed_instruction(ip, port, wheel_number, speed):
    # join is faster '+' is an O(n^2) operation (compared to O(n) for join)
    # 0 - message from central unit
    # 1 - source board is raspberry pi
    # 1 - # of source board is 1
    # 0 - destination board is arduino
    # wheel_number - # of destination board
    # 01 - type of message is instruction
    data = "".join(["0110", str(wheel_number), "01", str(speed)])
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(data.encode(), (ip, WHEEL_PORT))


# Function to save received IP address of device.
# @data, data sent in packet
def wait_for_ip_address(data):
    # check for notified IP address
    print("zacinam arduino")
    if data[10:14] == '0000':
        wheel_number = int("".join([data[4],data[5]]), 16)
        wheel_ip = ''
        for i in range(4):
            number =  str(int("".join([data[14+2*i], data[15+2*i]]), 16))
            if(i!=3):
                wheel_ip = wheel_ip + number + '.';
            else:
                wheel_ip = wheel_ip + number;
        new_wheel = IpWheel(wheel_ip, wheel_number)
        wheelList.append(new_wheel)


# Move vehicle forward, backwards or stop vehicle.
# @speed, vehicle speed
def move_vehicle(speed):
    write_log(' vehicle move: ' + str(speed))
    for i in range(len(wheelList)):
        send_speed_instruction(wheelList[i].ipAddress, WHEEL_PORT, wheelList[i].wheelNumber, speed)


# Move to side.
# @direction, 1 - left, 0 - right.
def turn_vehicle(direction, speed):
    write_log(' vehicle turn : ' + str(direction) + ' speed: ' + str(speed))
    if direction == 1:
        send_speed_instruction(wheelList[0].ipAddress, WHEEL_PORT, wheelList[0].wheelNumber, speed)
        send_speed_instruction(wheelList[2].ipAddress, WHEEL_PORT, wheelList[2].wheelNumber, speed)
        send_speed_instruction(wheelList[1].ipAddress, WHEEL_PORT, wheelList[1].wheelNumber, 180 - speed)
        send_speed_instruction(wheelList[3].ipAddress, WHEEL_PORT, wheelList[3].wheelNumber, 180 - speed)
    else:
        send_speed_instruction(wheelList[1].ipAddress, WHEEL_PORT, wheelList[1].wheelNumber, speed)
        send_speed_instruction(wheelList[3].ipAddress, WHEEL_PORT, wheelList[3].wheelNumber, speed)
        send_speed_instruction(wheelList[0].ipAddress, WHEEL_PORT, wheelList[0].wheelNumber, 180 - speed)
        send_speed_instruction(wheelList[2].ipAddress, WHEEL_PORT, wheelList[2].wheelNumber, 180 - speed)


def process_infrared_camera(data):
    print(data)


def process_message(data):
    message_type = data[10:14]
    message_types = {
        "0005": process_laser,
        "0003": process_infrared_camera
    }
    message_types[message_type](data)

# Function to listen on ip and port.
def listen(ip, port):
    global wheelList
    global help_array

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    wheelList.append(IpWheel('192.168.1.10', 3))
    wheelList.append(IpWheel('192.168.1.9', 4))
    wheelList.append(IpWheel('192.168.1.8', 2))
    wheelList.append(IpWheel('192.168.1.22', 1))
    wheelList.sort(key=lambda x: x.wheelNumber)
    move_vehicle(MOVE_FORWARD)
    laser_message = "010201010100050200C8001E015E005000A005DC00B30037"
    camera_message = "010000000003A5"
    arduino_message = "01000101010000C0A80116"
    #laser_message = "01020100000502 00CB 001E 015E 0050 00A0 05DC 00B3 0037"
    # 2 30 350 80 20 1500 192 55
    process_message(laser_message)
    #laserList = process_laser(laser_message)
    #find_closest_degree(0, laserList)
    try:
        # bind IP and port
        sock.bind((ip, port))
    except socket.error:
        log_file.write(str(datetime.datetime.now()) + ' port already bind \n')

    while True:
        data, addr = sock.recvfrom(1024)
        write_log('receive message: ' + str(data.decode()))

        # choose wheel, for example #2
        # pom = [x for x in help_array if x.wheelNumber == 2]
        # print(pom[0].ipAddress)
        # send_packet(pom[0].ipAddress, 8000, pom[0].wheelNumber)

        # if not all IP address received
        if len(wheelList) < 4:
            wait_for_ip_address(str(data.decode()))
            if len(wheelList) == 4:
                # sort list according to wheelNumber
                wheelList.sort(key=lambda x: x.wheelNumber)
        if len(wheelList) == 4:
            for wheel in wheelList:
                move_vehicle(MOVE_FORWARD)
                turn_vehicle(1, MOVE_FORWARD)
#   TODO: posielanie rychlosti arduinu

log_file = open('control_unit_log', 'w+')
#UDP_IP = "192.168.1.200"
UDP_IP = "147.175.152.40"
UDP_PORT = 5000

write_log(' control unit start')

udpListenerThread = UdpListener(UDP_IP, UDP_PORT)
udpListenerThread.start()

write_log(' End of main thread')