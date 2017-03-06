INDEX_OF_PACKET_BYTE = 0
class LaserData:
    def __init__(self, startAngle, startDistance, endAngle, endDistance):
        self.startAngle = startAngle
        self.startDistance = startDistance
        self.endAngle = endAngle
        self.endDistance = endDistance
        self.startComputedAngle = {True: 360 - startAngle, False: startAngle}[startAngle >= 180]
        self.endComputedAngle = {True: 360 - endAngle, False: endAngle}[endAngle >= 180]
