# Model for storage laser data
class LaserData:
    def __init__(self, startAngle, startDistance, endAngle, endDistance):
        self.startAngle = startAngle
        self.startDistance = startDistance
        self.endAngle = endAngle
        self.endDistance = endDistance
        self.startComputedAngle = {True: 360 - startAngle, False: startAngle}[startAngle >= 180]
        self.endComputedAngle = {True: 360 - endComputedAngle, False: endComputedAngle}[endComputedAngle >= 180]
        log_file = open('control_unit_log', 'a')
        log_file.write(str(datetime.datetime.now()) + message + '\n')
        log_file.close(' New laser data: startAngle: ' + str(startAngle) + ' startDistance: ' + str(startDistance) + ' endAngle: ' + endAngle + ' endDistance: ' + endDistance)