import random


class Point:
    def __init__(self, reachable, visited=False, timecost=0, changeProb=0.2):
        self.init_reachable = reachable
        self.reachable = self.init_reachable
        self.visited = visited
        self.visited_times = 0
        self.timecost = timecost
        self.changeProb = changeProb
        self.timespent = 0
        self.ischargingp = False
        pass

    def update(self):
        e = random.random()
        if e < self.changeProb:
            self.reachable = not self.reachable
        pass


class ChargingPoint(Point):
    def __init__(self, timecost=30, cap=8):
        super(ChargingPoint, self).__init__(reachable=True, visited=False, timecost=timecost, changeProb=0)
        self.cap = cap
        self.init_stop_num = random.randint(0, self.cap)
        self.stop_num = self.init_stop_num
        self.chargingList = []
        self.ischargingp = True

    def update(self):
        super(ChargingPoint, self).update()
        if self.ischargingp:
            self.stop_num = len(self.chargingList) + random.randint(0, self.cap - len(self.chargingList))


class Edge:
    def __init__(self, from_p, to_p, traveltime=1):
        self.from_p = from_p
        self.to_p = to_p
        self.traveltime = traveltime