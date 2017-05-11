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
MOVE_FORWARD = 150
SPEED_NEUTRAL = 90
MOVE_BRAKE = 30
MOVE_BACKWARD = 50


# Constants for laser processing.
MIN_DISTANCE = 50
DIRECTION = 5
ANGLE_CONSTANT = 10
# 0-left, 1-right, 2-straight, 3-stop
LASER_RESULT = 1


# Constants for camera processing.
CAMERA_ANGLE = 0


# Constants for handling threads

INDEX_OF_PACKET_BYTE = 0


# Model for saving information about wheel IP address and number
# ipAddress, ip address of wheel
# wheelNumber, number of wheel
# wheelSpeed, current wheel speed
# turnFlag, indicator of turning
class IpWheel:
    def __init__(self, ip, wheelNo):
        self.ipAddress = ip
        self.wheelNumber = wheelNo
        self.wheelSpeed = 90
        self.turnFlag = 0
        write_log(' New wheel registered: #' + str(wheelNo) + ', ' + ip)


# Model for storage laser data
class LaserData:
    def __init__(self, startAngle, startDistance, endAngle, endDistance):
        self.startAngle = startAngle
        self.startDistance = startDistance
        self.endAngle = endAngle
        self.endDistance = endDistance
        # compute distance from direction for start and end angle
        self.startComputedAngle = {True: abs(startAngle - DIRECTION), False: abs(360 - startAngle + DIRECTION)}[self.startAngle <= DIRECTION + 180]
        self.endComputedAngle = {True: abs(endAngle - DIRECTION), False: abs(360 - endAngle + DIRECTION)}[self.endAngle <= DIRECTION + 180]
        self.directionAngle = {True: self.startAngle, False: self.endAngle}[self.startComputedAngle <= self.endComputedAngle]
        write_log(' New laser data: startAngle: ' + str(startAngle) + ' startDistance: ' + str(startDistance) + ' endAngle: ' + str(endAngle) + ' endDistance: ' + str(endDistance))
        print("Start computed: " + str(self.startComputedAngle))
        print("End computed: " + str(self.endComputedAngle))


class _Getch:
    def __init__(self):
        try:
            self.impl = _GetchUnix()
        except ImportError:
            print("error")

    def __call__(self):
        return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


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


# Thread class for WASD control.
class WasdThread(threading.Thread):
    # Constructor
    def __init__(self):
        threading.Thread.__init__(self)

    # Run function
    def run(self):
        print("direction: w - forward, a - turn left, d - turn right, s - backward, q - stop")
        while True:
            getch = _Getch()
            write_log(' wasd start thread')
            # read user input
            # getch = _Getch()
            # FUNGUJE LEN PRE CMD!!!!!
            letter = getch()
            if letter == "x":
                print("break")
                break
            try:
                # letter = input("direction: ")
                direction_types = {
                    "w": go_straight_wasd,
                    "a": go_left_wasd,
                    "s": go_back_wasd,
                    "d": go_right_wasd,
                    "q": stop
                }
                direction_types[letter.decode()]()
            # bad input
            except:
                write_log(' Bad input: ' + letter)
                continue
            '''if(len(wheelList) == 4):
                # decode, because standard input put 'b' befor char
                direction_types[letter.decode()]();
            else:
                print("waiting for wheels")'''


# Function for processing laser packet.
def parse_laser_data(laser_message):
    number_of_records = int(
        "".join([laser_message[INDEX_OF_PACKET_BYTE + 14], laser_message[INDEX_OF_PACKET_BYTE + 15]]), 16)
    #print("count of lase data: ", number_of_records)
    #print("laser data: \n")
    laser_list = []
    index = 0
    count = 0
    # iterating over numbers of road side data from camera, message[6] represents count of numbers
    for index in range(0, number_of_records):
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
# @laser_data_list, list of laser data
def find_closest_degree(laser_data_list):
    laser_data_list.sort(key=lambda x: x.startComputedAngle)
    startAngle = laser_data_list[0]
    laser_data_list.sort(key=lambda x: x.endComputedAngle)
    endAngle = laser_data_list[0]
    global DIRECTION
    global LASER_RESULT
    is_direction_set = False
    # 0-left, 1-right, 2-straight, 3-stop
    # if direction is between <350,10>
    if 350 < DIRECTION or DIRECTION < 10:
        for data in laser_data_list:
            # if we can go straight in range cca <350,10>
            if (data.startAngle > data.endAngle) and (data.startAngle >= 0) and (0 <= data.endAngle):
                print("1**************")
                LASER_RESULT = 2
                is_direction_set = True
                break
        if is_direction_set == False:
                closestAngle = {True: startAngle, False: endAngle}[startAngle.startComputedAngle <= endAngle.endComputedAngle]
                # if closest angle is higher or equal than 180 - means left is closer
                if closestAngle.directionAngle >= 180:
                    print("2********************")
                    LASER_RESULT = 0
                    is_direction_set = True
                # if closest angle is lower than 180 - means right is closer
                else:
                    print("3*******************")
                    LASER_RESULT = 1
                    is_direction_set = True

    if is_direction_set:
        write_log(' LASER_RESULT SET IN FIRST DECISION: ' + LASER_RESULT)
        return

    for data in laser_data_list:
        # if DIRECTION not straight, direction is free, turn to direction
        if ((data.startAngle > data.endAngle) and ((data.startAngle >= DIRECTION) and (DIRECTION <= data.endAngle))) or ((data.startAngle < data.endAngle) and ((data.startAngle <= DIRECTION) and (DIRECTION <= data.endAngle))):
            # if DIRECTION is higher or equal than 180 - means left is closer
            if DIRECTION >= 180:
                LASER_RESULT = 0
                is_direction_set = True
                break
            # if DIRECTION is lower than 180 - means right is closer
            else:
                LASER_RESULT = 1
                is_direction_set = True
                break

    if is_direction_set:
        write_log(' LASER_RESULT SET IN SECOND DECISION: ' + LASER_RESULT)
        return

    closestAngle = {True: startAngle, False: endAngle}[startAngle.startComputedAngle <= endAngle.endComputedAngle]
    # if closest angle is higher or equal than 180 - means left is closer
    if closestAngle.directionAngle >= 180:
        LASER_RESULT = 0
        is_direction_set = True
        write_log(' LASER_RESULT SET IN THIRD DECISION: ' + LASER_RESULT)
    # if closest angle is lower than 180 - means right is closer
    else:
        LASER_RESULT = 1
        write_log(' LASER_RESULT SET IN FOURTH DECISION: ' + LASER_RESULT)
        is_direction_set = True


# Process laser data.
# @laser_data, free angles.
def process_laser_data(laser_data):
    # get list of angles
    list_of_angles = parse_laser_data(laser_data)
    # get best free angle

    global LASER_RESULT
    if len(list_of_angles) == 0:
        # stop
        LASER_RESULT = 3
    else:
        find_closest_degree(list_of_angles)
    print("laser: ", LASER_RESULT)
    # stop vehicle before turning
    stop()


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
    # 00 - message from central unit
    # 01 - source board is raspberry pi
    # 01 - # of source board is 1
    # 00 - destination board is arduino
    # wheel_number - # of destination board
    # 0001 - type of message is instruction
    data = bytearray([0, 1, 1, 0, wheel_number, 0, 1, speed])
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(data, (ip, WHEEL_PORT))


# Function to save received IP address of device.
# @data, data sent in packet
def wait_for_ip_address(data):
    print("data: ", data)
    # check for notified IP address
    if data[10:14] == '0000':
        wheel_number = int("".join([data[4],data[5]]), 16)
        wheel_ip = ''
        for i in range(4):
            number = str(int("".join([data[14+2*i], data[15+2*i]]), 16))
            if i != 3:
                wheel_ip = wheel_ip + number + '.'
            else:
                wheel_ip = wheel_ip + number
        new_wheel = IpWheel(wheel_ip, wheel_number)
        wheelList.append(new_wheel)


# Move vehicle forward, backwards or stop vehicle.
# @speed, vehicle speed
def move_vehicle(speed):
    write_log(' vehicle move: ' + str(speed))
    for i in range(len(wheelList)):
        current_speed = wheelList[i].wheelSpeed + 1
        # if current speed is less than minimal forward speed
        # OR current speed is set to higher value than allowed
        # OR vehicle was turning
        # set minimal forward speed
        if current_speed >= 150:
            current_speed = wheelList[i].wheelSpeed
        elif wheelList[i].turnFlag == 1:
            current_speed = 91
        send_speed_instruction(wheelList[i].ipAddress, WHEEL_PORT, wheelList[i].wheelNumber, current_speed)
        # reset turn flag
        wheelList[i].turnFlag = 0
        # speed cannot be higher that 150
        if current_speed < 150:
            wheelList[i].wheelSpeed = current_speed


# Move vehicle backward
def move_backward():
    write_log(' vehicle move backward: ')
    list_length = len(wheelList)
    wheel_speed = wheelList[0].wheelSpeed
    # if speed is higher than 90, we can decrease it by 1 and send speed to wheels.
    if wheel_speed - 1 > 90:
        for i in range(list_length):
            #current_speed = {True: 80, False: wheelList[i].wheelSpeed - 1}[
            #    (wheelList[i].wheelSpeed - 1 == 90) or (wheelList[i].turnFlag == 1)]
            current_speed = {True: 85, False: wheelList[i].wheelSpeed - 1}[(wheelList[i].turnFlag == 1)]
            send_speed_instruction(wheelList[i].ipAddress, WHEEL_PORT, wheelList[i].wheelNumber, current_speed)
            wheelList[i].turnFlag = 0
            wheelList[i].wheelSpeed = current_speed
        return
    # if speed is lower than 90, we can decrease it by 1 and send speed to wheels.
    elif wheel_speed - 1 < 90:
        for i in range(list_length):
            current_speed = {True: 32, False: wheelList[i].wheelSpeed - 1}[
                (wheelList[i].wheelSpeed - 1 == 31) or (wheelList[i].turnFlag == 1)]
            send_speed_instruction(wheelList[i].ipAddress, WHEEL_PORT, wheelList[i].wheelNumber, current_speed)
            wheelList[i].turnFlag = 0
            wheelList[i].wheelSpeed = current_speed
        return
    # this is case with neutral and break speeds
    else:
        for i in range(list_length):
            current_speed = 89
            for k in range(2):
                if k == 0:
                    send_speed_instruction(wheelList[i].ipAddress, WHEEL_PORT, wheelList[i].wheelNumber, MOVE_BRAKE)
                # send 90 as neutral speed
                if k == 1:
                    send_speed_instruction(wheelList[i].ipAddress, WHEEL_PORT, wheelList[i].wheelNumber, SPEED_NEUTRAL)
            send_speed_instruction(wheelList[i].ipAddress, WHEEL_PORT, wheelList[i].wheelNumber, current_speed)
            wheelList[i].wheelSpeed = current_speed


# Move to side.
# @direction, 1 - left, 0 - right.
def turn_vehicle(direction, speed):
    write_log(' vehicle turn : ' + str(direction) + ' speed: ' + str(speed))

    # turning left
    if direction == 1:
        faster_wheels = [x for x in wheelList if x.wheelNumber == 1 or x.wheelNumber == 4]
        slower_wheels = [x for x in wheelList if x.wheelNumber == 2 or x.wheelNumber == 3]
    # turning right
    else:
        slower_wheels = [x for x in wheelList if x.wheelNumber == 1 or x.wheelNumber == 4]
        faster_wheels = [x for x in wheelList if x.wheelNumber == 2 or x.wheelNumber == 3]

    # set speed on faster wheels
    for i in range(len(faster_wheels)):
        current_speed = faster_wheels[i].wheelSpeed + 2
        # if current speed is less than minimal forward speed allowed
        # set minimal forward speed + 5
        if current_speed <= 100:
            current_speed = 140
        # else if current speed is set to higher value than allowed
        # set original forward speed
        elif current_speed >= 150:
            current_speed -= 2
        send_speed_instruction(faster_wheels[i].ipAddress, WHEEL_PORT, faster_wheels[i].wheelNumber, 150)
    # set speed on slower wheel
    # for j in range(3):
    for i in range(len(slower_wheels)):
        current_speed = {True: faster_wheels[0].wheelSpeed - 2, False: slower_wheels[i].wheelSpeed - 2}[
            faster_wheels[0].wheelSpeed <= slower_wheels[i].wheelSpeed - 2]
        # current_speed = slower_wheels[i].wheelSpeed - 10
        # if current slower wheel speed is len than minimal forward speed, set to minimal forward speed
        if current_speed < 100:
            current_speed = 100
        send_speed_instruction(slower_wheels[i].ipAddress, WHEEL_PORT, slower_wheels[i].wheelNumber, 92)

    # set turn flag for wheels
    for i in range(len(wheelList)):
        wheelList[i].turnFlag = 1


# Move vehicle forward, backwards.
# @speed, vehicle speed
def auto_move_vehicle(speed):
    write_log(' vehicle move: ' + str(speed))
    for i in range(len(wheelList)):
        send_speed_instruction(wheelList[i].ipAddress, WHEEL_PORT, wheelList[i].wheelNumber, 105)


# Turn vehicle automatically.
# @direction, 1 - left, 0 - right.
def auto_turn_vehicle(direction, speed):
    direct = ""
    if direction == 1:
        direct = "left"
    else:
        direct = "right"
    write_log(' vehicle turn : ' + direct + ' speed: ' + str(speed))
    # turn left
    if direction == 1:
        send_speed_instruction(wheelList[0].ipAddress, WHEEL_PORT, wheelList[0].wheelNumber, 150)
        send_speed_instruction(wheelList[3].ipAddress, WHEEL_PORT, wheelList[3].wheelNumber, 150)
        send_speed_instruction(wheelList[1].ipAddress, WHEEL_PORT, wheelList[1].wheelNumber, MOVE_BRAKE)
        send_speed_instruction(wheelList[2].ipAddress, WHEEL_PORT, wheelList[2].wheelNumber, MOVE_BRAKE)
        send_speed_instruction(wheelList[1].ipAddress, WHEEL_PORT, wheelList[1].wheelNumber, SPEED_NEUTRAL)
        send_speed_instruction(wheelList[2].ipAddress, WHEEL_PORT, wheelList[2].wheelNumber, SPEED_NEUTRAL)
        send_speed_instruction(wheelList[1].ipAddress, WHEEL_PORT, wheelList[1].wheelNumber, 95)
        send_speed_instruction(wheelList[2].ipAddress, WHEEL_PORT, wheelList[2].wheelNumber, 95)
    # turn right
    else:
        send_speed_instruction(wheelList[1].ipAddress, WHEEL_PORT, wheelList[1].wheelNumber, 150)
        send_speed_instruction(wheelList[2].ipAddress, WHEEL_PORT, wheelList[2].wheelNumber, 150)
        send_speed_instruction(wheelList[0].ipAddress, WHEEL_PORT, wheelList[0].wheelNumber, MOVE_BRAKE)
        send_speed_instruction(wheelList[3].ipAddress, WHEEL_PORT, wheelList[3].wheelNumber, MOVE_BRAKE)
        send_speed_instruction(wheelList[0].ipAddress, WHEEL_PORT, wheelList[0].wheelNumber, SPEED_NEUTRAL)
        send_speed_instruction(wheelList[3].ipAddress, WHEEL_PORT, wheelList[3].wheelNumber, SPEED_NEUTRAL)
        send_speed_instruction(wheelList[0].ipAddress, WHEEL_PORT, wheelList[0].wheelNumber, 95)
        send_speed_instruction(wheelList[3].ipAddress, WHEEL_PORT, wheelList[3].wheelNumber, 95)


# Function to process data from infrared camera.
# @data, data from camera
def process_infrared_camera(data):
    # TODO: skontrolovat index
    global CAMERA_ANGLE
    CAMERA_ANGLE = data[7]
    if CAMERA_ANGLE > 127:
        CAMERA_ANGLE = 128 - CAMERA_ANGLE


# Process data from GPS.
# @data, data from GPS
def process_gps(data):
    global DIRECTION
    # DIRECTION = int("".join([data[14], data[15], data[16], data[17]]), 16)
    log_file.write(str(datetime.datetime.now()) + ' Direction updated to: ' + str(DIRECTION) + '\n')
    # gps_decision_maker()


def gps_decision_maker():
    dire = DIRECTION
    print(dire)
    if dire >= 350 or (dire <= 10 and dire >= 0):
        print('straight')
        write_log(' GO STRAIGHT IN GPS_DECISION_MAKER ')
        auto_move_vehicle(MOVE_FORWARD)
    elif dire > 10 and dire <= 180:
        print('right')
        write_log(' TURN RIGHT VEHICLE IN GPS_DECISION_MAKER ')
        auto_turn_vehicle(0, MOVE_FORWARD)
    else:
        print('left')
        write_log(' TURN LEFT VEHICLE IN GPS_DECISION_MAKER ')
        auto_turn_vehicle(1, MOVE_FORWARD)


# Main vehicle control
def decision_maker():
    # 0-left, 1-right, 2-straight
    # LASER_RESULT - from laser, HIGHEST PRIORITY
    # DIRECTION - from gps and compas
    # CAMERA_ANGLE - from camera LOWEST PRIORITY
    print("tu")
    global LASER_RESULT
    if LASER_RESULT == 3:
        write_log(' STOP VEHICLE IN DECISION_MAKER ')
        stop()
    # if laser result is left, turn left.
    elif LASER_RESULT == 0:
        write_log(' TURN VEHICLE LEFT IN DECISION_MAKER ')
        auto_turn_vehicle(1, MOVE_FORWARD)
    # if laser result is right, turn right.
    elif LASER_RESULT == 1:
        write_log(' TURN VEHICLE RIGHT IN DECISION_MAKER ')
        auto_turn_vehicle(0, MOVE_FORWARD)
    # if camera angle > 10, turn right.
    elif CAMERA_ANGLE > 10:
        write_log(' TURN VEHICLE RIGHT(CAMERA) IN DECISION_MAKER ')
        auto_turn_vehicle(0, MOVE_FORWARD)
    # if camera angle < -10, turn left.
    elif CAMERA_ANGLE < -10:
        write_log(' TURN VEHICLE LEFT(CAMERA) IN DECISION_MAKER ')
        auto_turn_vehicle(1, MOVE_FORWARD)
    # go straight.
    else:
        write_log(' GO STRAIGHT VEHICLE IN DECISION_MAKER ')
        auto_move_vehicle(MOVE_FORWARD)


# Process message type function.
# @data, data from message
def process_message(data):
    message_type = data[10:14]
    try:
        message_types = {
            "0006": process_gps,
            "0005": process_laser_data,
            "0003": process_infrared_camera
        }
        write_log(' IN PROCESS MESSAGE RECEIVED MESSAGE: ' + message_type)
        message_types[message_type](data)
        decision_maker()
    except:
        write_log(' RECEIVED DATA: ' + data)

# WASD go straight function.
def go_straight_wasd():
    print("going straight forward")
    move_vehicle(MOVE_FORWARD)


# WASD go left function.
def go_left_wasd():
    print("turning left")
    turn_vehicle(1, MOVE_FORWARD)


# WASD go backward function.
def go_back_wasd():
    print("going backward")
    move_backward()


# WASD go right function.
def go_right_wasd():
    print("going right")
    turn_vehicle(0, MOVE_FORWARD)


# Stop vehicle function.
def stop():
    print("stopping")
    for j in range(2):
        for i in range(len(wheelList)):
            # first send speed 30 as brake
            if j == 0:
                send_speed_instruction(wheelList[i].ipAddress, WHEEL_PORT, wheelList[i].wheelNumber, MOVE_BRAKE)
            # send 90 as neutral speed
            if j == 1:
                send_speed_instruction(wheelList[i].ipAddress, WHEEL_PORT, wheelList[i].wheelNumber, SPEED_NEUTRAL)

            wheelList[i].wheelSpeed = 90


# Function to listen on ip and port.
def listen(ip, port):
    global wheelList
    global help_array
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        if len(wheelList) != 4:
            # bind IP and port
            print("IP: ", ip)
            print("port: ", port)

        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((ip, port))
    except socket.error:
        log_file.write(str(datetime.datetime.now()) + ' port already bind \n')

    while True:
        data, addr = sock.recvfrom(1024)
        # if not all IP address received
        if len(wheelList) < 4:
            wait_for_ip_address(str(data.encode('hex')))
            if len(wheelList) == 4:
                # sort list according to wheelNumber
                wheelList.sort(key=lambda x: x.wheelNumber)
                wasdThread1.start()

        if len(wheelList) == 4:
           process_message(str(data.encode('hex')))

log_file = open('control_unit_log', 'w+')
UDP_IP = "192.168.1.200"
UDP_PORT = 5000

write_log(' control unit start')

wasdThread1 = WasdThread();
udpListenerThread = UdpListener(UDP_IP, UDP_PORT)
udpListenerThread.start()


write_log(' End of main thread')
