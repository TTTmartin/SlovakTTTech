from rplidar import RPLidar
lidar = RPLidar('\\\\.\\com3')
import sys
import numpy as np
import array
import math
import socket

LIMIT_DISTANCE = 1500 #limit distance in front of obstacle (in milimeters)
MAX_DISTANCE = 3000   #maximum distance, which is asigned when meauserement is not successful (in milimeters)
LIMIT_SPACE = 500     #maximum length of space between two end points (in milimeters)

UDP_IP = "192.168.1.200"    #ip address of end device - rasberry
UDP_PORT = 5000             #udp of port of communication with end device - rasberry

#function counts and returns square of number a
def square(a):
    return a*a

#function counts and returns distance of space
#between two end points of angle - cosinus sentence
def count_distance_of_space(range):
    a = range[1]        #begin distance
    b = range[3]        #end distance
    alfa = range[2] - range[0]  #getting angle alfa

    val = math.pi / 180.0   #pre-counting for converting radians to degrees
    ret = math.cos(alfa * val) #countig of cosinus alfa
    return math.sqrt(square(a) + square(b) - 2 * a * b * ret)  #cosinus sentence - known b,c, alfa, return side c

#filtering of short ranges, where space between
#two points is less then limited space
def remove_short_ranges(ranges):
    new_ranges = []     #creating new empty array for passed ranges
    for r in ranges:
        if(r[1] == 0):  #if begin distance is zero, quality bit was zero => suppose it is max distance
            r[1] = MAX_DISTANCE
        if(r[3] == 0):  #if end distance is zero, quality bit was zero => suppose it is max distance
            r[3] = MAX_DISTANCE
        space = count_distance_of_space(r)  #count distance of space between two end points
        if(space > LIMIT_SPACE):
            new_ranges.append(r)    #if space is bigger then limited distance for space, add to new ranges

    return new_ranges

#sending of open ranges as array of bytes
def send_ranges(ranges):
    num_of_ranges = len(ranges)
    if(num_of_ranges != 0):
        packet = bytearray([1,1,2,1,1,0,5,num_of_ranges])   #creating of packet header
        for r in ranges:                                    #loop through all ranges
            b1, b2 = (int (round(r[0])) & 0xFFFF).to_bytes(2, 'big')  #divide begin angle (int) into two bytes
            b3, b4 = (int(round(r[1])) & 0xFFFF).to_bytes(2, 'big')   #divide begin distance (int) into two bytes
            b5, b6 = (int(round(r[2])) & 0xFFFF).to_bytes(2, 'big')   #divide end angle (int) into two bytes
            b7, b8 = (int(round(r[3])) & 0xFFFF).to_bytes(2, 'big')   #divide end distance (int) into two bytes

            packet.append(b1)                                         #creating of packet
            packet.append(b2)
            packet.append(b3)
            packet.append(b4)
            packet.append(b5)
            packet.append(b6)
            packet.append(b7)
            packet.append(b8)
            sock.sendto(packet, (UDP_IP, UDP_PORT))                   #send packet

#processing of measured data into ranges
# with angles and distances
def create_ranges(scan):
    end_angle = 0
    numRanges = 0           #number of all ranges
    previous_bigger = 0
    range = []
    ranges = []
    s_scan = sorted(scan, key=lambda x: x[1])   #sorting of measured data based on angle
    begin_angle = s_scan[0][1]                  #initializing variable with value begin angle in first range
    begin_distance = s_scan[0][2]               #initializing variable with value begin distance in first range
    j = 0
    for meas in s_scan:
        if(meas[0] == 0):           #if quality is zero, suppose distance as maximum measurable
            distance = MAX_DISTANCE
        else:
            distance = meas[2]      #meas[2] represents distance for given measurment; meas[0] - quality, meas[1] - angle

        if(distance < LIMIT_DISTANCE):    #if distance is less then limited distance
            if(previous_bigger == 1):     #if in previous angle was distance bigger then limited, close range
                                          #create range (beg-angle, beg-dist, end-angle, end-dist
                range = [begin_angle, begin_distance, s_scan[j-1][1], s_scan[j-1][2]]
                ranges.append(range)      #append created range to array of ranges
                previous_bigger = 0;      #set control variable to zero
                numRanges = numRanges + 1 #increment number of ranges
            if (j != len(s_scan) - 1):    #treat last field from array to avoid not accessing out of array
                begin_angle = s_scan[j+1][1]     #asign next angle
                begin_distance = s_scan[j+1][2]  #assign next distance
            previous_bigger = 0            #for remembering next meausurement that actual distance was less than limited
        else:
            previous_bigger = 1     #if distance is bigger then limited, just set variable to 1
        #print(j, " - ", round(meas[1], 1), "\t\t", distance, ",\t\t", meas[0]) #print for debugging all measurements
        j = j + 1

    if (len(ranges) > 0):                   #process only if there is at least one range
        if(ranges[-1][2] < begin_angle):    #if end angle is less then begin angle, it means last range wasn't included into ranges
            range = [begin_angle, begin_distance, s_scan[-1][1], s_scan[-1][2]] #create last range
            ranges.append(range)        #append last range
        if(ranges[0][0]>0 and ranges[0][0]<2 and ranges[-1][2]>357 and ranges[-1][2]<360):  #if range exceeds 360 degrees, merge first and last range
            ranges[0][0] = ranges[-1][0]    #edit angle in first range -> change for begin angle from last range
            ranges[0][1] = ranges[-1][1]    #edit distance in first range -> change for begin distance from last range
            del ranges[-1]                  #delete last range
    ranges = remove_short_ranges(ranges)    #filter short ranges
    print(ranges)
    send_ranges(ranges)                     #send ranges

#main
sock = socket.socket(socket.AF_INET,     # Internet
                     socket.SOCK_DGRAM)  # UDP
info = lidar.get_info()     #get info about laser
print(info)
health = lidar.get_health() #get health of laser
print(health)

i = 0
data = []

for scan in lidar.iter_scans():
    create_ranges(scan)     #process measured data
    i = i + 1
    if i > 200:             #process only 200 measurements
        break

lidar.stop()            #stop laser
lidar.stop_motor()
lidar.disconnect()
