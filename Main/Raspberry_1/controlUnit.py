import compass
import gps
import laser
import threading
from threading import Thread
import time

# Listening for messages on ethernet interface
def listen_on_interface():
    while True:
        gps1.setDegree(1)
        gps1.setDegree(2)

# Controling steering based on data from interface
def steering_control():
    while True:
        closest_free_degrees = find_closest_degree(return_relative_degree(compas1.degree,gps1.degree),laser1.range_list)
        print(closest_free_degrees)
        time.sleep(1)


# Finds closest clear degrees to direction degree
# returns 2 fields with degree, first is the closer one
#@direction, main degree
#@range_list, list of degrees 0-359 1-clear 0-blocked
def find_closest_degree(direction, range_list):
    left = 0
    right = 0

    x = direction
    while range_list[x] != 1:
        right += 1
        x = (x+1) % 360

    x=direction
    while range_list[x] != 1:
        left += 1
        x = (x-1) % 360

    if(right<left):
        return [(direction+right) % 360, (direction-left) % 360]
    elif (left<right):
        return [(direction-left) % 360, (direction+right) % 360]
    else:
        return [(direction+right) % 360, (direction-left) % 360]


# Returns relative degree of next GPS point
# @compass_degree, geographical degree return by compass
# @gps_degree, geographical degree of next destination
def return_relative_degree(compass_degree, gps_degree):
    return gps_degree - compass_degree if gps_degree - compass_degree > 0 else gps_degree - compass_degree + 360

#testing
laser1 = laser.Laser()
gps1 = gps.Gps()
compas1 = compass.Compass()

range_list = []
for x in range(0, 360):
    range_list.append(1)
for x in range(10, 31):
    range_list[x]=0

print(range_list)
print(find_closest_degree(20,range_list))

t1= Thread(target = listen_on_interface)
t2= Thread(target = steering_control)
t1.start()
t2.start()
t1.join()
t2.start()

while 1:
  pass

