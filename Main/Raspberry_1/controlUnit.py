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
        print(gps1.degree)
        time.sleep(1)

laser1 = laser.Laser()
gps1 = gps.Gps()
compas1 = compass.Compass()

t1= Thread(target = listen_on_interface)
t2= Thread(target = steering_control)
t1.start()
t2.start()
t1.join()
t2.start()

while 1:
  pass

