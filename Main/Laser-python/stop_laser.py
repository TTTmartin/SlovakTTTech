from rplidar import RPLidar
lidar = RPLidar('\\\\.\\com3')
import sys
import numpy as np
import array
import math
from tkinter import *


lidar.stop()            #stop laser
lidar.stop_motor()
lidar.disconnect()
