#Class for laser data
class Laser:

    #Constructor
    def __init__(self):
        self.range_list = []
        for x in range(0, 360):
            self.range_list.append(1)

    def setRange(self, range_list):
        for x in range(0, 360):
            if range_list[x] == 1:
                self.range_list.append(1)
            else:
                self.range_list.append(0)
