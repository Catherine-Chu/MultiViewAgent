import random
import sys
sys.path.append('../')
from framework.StaticConsensus import *



class Point:
    def __init__(self, nid, pos_x, pos_y, node_type=0, victims_num=None, need_rescue=False, visited=False,
                 visit_count=0, t_request=0, load_demand_num=None):
        self.expcfg = ExperimentConfig()
        self.NID = nid
        self.pos_x = pos_x
        self.pos_y = pos_y
        if node_type == 0:
            self.danger_level = 0
            self.blocked = False
            self.is_charge_p = False
        elif node_type == 1:
            self.blocked = True
            self.is_charge_p = False
            self.danger_level = 2
        elif node_type == 2:
            self.blocked = False
            self.is_charge_p = True
            self.danger_level = 0
        else:
            self.danger_level = 1
            self.blocked = False
            self.is_charge_p = False
        self.visited = visited
        self.visit_count = visit_count
        if victims_num is not None:
            self.victims_num = victims_num
        else:
            self.victims_num = random.randint(0, self.expcfg.S_max)  # TODO: 范围内的人员分布是否要完全没有规律,随机生成,随机变动？
        self.need_rescue = need_rescue

        self.t_request = t_request
        if load_demand_num is not None:
            self.load_demand_num = load_demand_num
        else:
            if self.need_rescue or self.victims_num <= self.expcfg.S_max:
                self.load_demand_num = 0
            elif self.danger_level == 1 or self.blocked or self.is_charge_p:
                self.load_demand_num = 0
            else:
                self.load_demand_num = 1

        self.t_cost = 0
        pass

    def __eq__(self, other):
        if isinstance(other, Point) and self.NID == other.NID:
            result = (self.danger_level == other.danger_level) and (self.blocked == other.blocked) and (self.is_charge_p == other.is_charge_p) and (
                    self.visited == other.visited) and (self.visit_count == other.visit_count) and (
                             self.victims_num == other.victims_num) and (
                             self.need_rescue == other.need_rescue) and (self.t_request == other.t_request) and (
                             self.t_cost == other.t_cost)
            return result
        else:
            return False

    def update(self, change_prob):
        e = random.random()
        if e < change_prob[0]:
            self.blocked = not self.blocked
        if not self.blocked:
            if self.danger_level == 2:
                self.danger_level = 1
            else:
                e = random.random()
                if e < change_prob[0]:
                    self.danger_level = 1-self.danger_level
            e = random.random()
            if e < change_prob[1]:
                self.victims_num = random.randint(0, 10)
            e = random.random()
            if e < change_prob[2]:
                self.need_rescue = not self.need_rescue
        if self.blocked:
            self.danger_level = 2
            self.visited = False
            self.is_charge_p = False
        pass


class ChargingPoint(Point):

    def __init__(self, sid, nid, pos_x, pos_y, t_request=30, charging_cap=4, queue_cap=4, dock_cap=4, is_inservice=True,
                 cur_utilization=None, queue_length=None, dock_num=None):
        super(ChargingPoint, self).__init__(nid=nid, pos_x=pos_x, pos_y=pos_y, node_type=2, t_request=t_request,visited=True)
        self.sid = sid
        self.charging_cap = charging_cap
        self.queue_cap = queue_cap
        self.dock_cap = dock_cap
        self.is_inservice = is_inservice
        if cur_utilization:
            self.cur_utilization = cur_utilization
        else:
            self.cur_utilization = random.randint(0, self.charging_cap)
        if self.cur_utilization >= self.charging_cap:
            if queue_length:
                self.queue_length = queue_length
            else:
                self.queue_length = random.randint(0, self.queue_cap)
        else:
            self.queue_length = 0
        if dock_num:
            self.dock_num = dock_num
        else:
            self.dock_num = random.randint(0, self.dock_cap)

    def __eq__(self, other):
        if isinstance(other, ChargingPoint) and self.NID == other.NID:
            result = (self.danger_level == other.danger_level) and (self.blocked == other.blocked) and (self.is_charge_p == other.is_charge_p) and (
                    self.visited == other.visited) and (self.visit_count == other.visit_count) and (
                             self.victims_num == other.victims_num) and (
                             self.need_rescue == other.need_rescue) and (self.t_request == other.t_request) and (
                             self.t_cost == other.t_cost)
            result = result and (self.is_inservice == other.is_inservice) and (
                    self.cur_utilization == other.cur_utilization) and (
                             self.queue_length == other.queue_length) and (self.dock_num == other.dock_num)
            return result
        else:
            return False

    def update(self, change_prob):
        super(ChargingPoint, self).update(change_prob)
        if self.is_charge_p:
            e = random.random()
            if e < change_prob[3]:
                self.is_inservice = not self.is_inservice
            if self.is_inservice:
                e = random.random()
                if e < change_prob[4]:
                    self.cur_utilization = random.randint(0, self.charging_cap)
                if self.cur_utilization >= self.charging_cap:
                    e = random.random()
                    if e < change_prob[4]:
                        self.queue_length = random.randint(0, self.queue_cap)
                else:
                    self.queue_length = 0
                e = random.random()
                if e < change_prob[4]:
                    self.dock_num = random.randint(0, self.dock_cap)

class Edge:

    def __init__(self, eid, from_p, to_p, distance=1):
        self.EID = eid
        self.from_p = from_p
        self.to_p = to_p
        self.distance = distance
        self.travel_time = distance

    def __eq__(self, other):
        if isinstance(other, Edge) and self.EID == other.EID:
            result = (self.distance == other.distance) and (self.travel_time == other.travel_time)
            return result
        else:
            return False

    def update(self, change_prob):
        e = random.random()
        if e < change_prob:
            self.travel_time = random.uniform(0, 2 * self.travel_time)
