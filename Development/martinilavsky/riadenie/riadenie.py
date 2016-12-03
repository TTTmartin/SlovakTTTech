class GPS:
    
 def __init__(self):
   self.degree = 0.0
 
 def setDegree(self, degree):
   self.degree = degree
   
class Compass:

 def __init__(self):
   self.degree = 0.0
 
 def setDegree(self,degree):
   self.degree = degree

class Laser:

 def __init__(self):
  self.range_list=[]
  for x in range (0, 360):
    self.range_list.append(1)

 def setRange(self,range_list):
  for x in range (0, 360):
    if range_list[x] == 1:
      self.range_list.append(1)
    else:
      self.range_list.append(0)

laser1 = Laser()
print (laser1.range_list)

