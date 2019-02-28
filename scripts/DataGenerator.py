# -*- coding:utf-8 -*-
import sys
import os

sys.path.append('../')
from framework.EnvComponents import *
from framework.StaticConsensus import *
import psycopg2
import random
import time
import numpy as np


class GlobalDataInitializer:

    def __init__(self, agent_num, map_width, map_height, charge_num, danger_num, charge_pos_list, obstacle_num=0,
                 db_used=True):
        if agent_num:
            self.agent_num = agent_num[0] + agent_num[1]
            self.agent_g_num = agent_num
        self.map_width = map_width
        self.map_height = map_height
        self.charge_num = charge_num
        self.danger_num = danger_num
        self.charge_pos_list = charge_pos_list
        self.static_info = StaticInfo()
        self.expconfig = ExperimentConfig()
        if db_used:
            self.conn = psycopg2.connect(database='multiAgents', user='chuwenjie', password='2399321cwj',
                                         host='127.0.0.1', port='5432')
            self.cur = self.conn.cursor()
        else:
            self.obstacle_num = obstacle_num

    def initNewMapViews(self):
        self.cur.execute("TRUNCATE TABLE areas")
        self.cur.execute("TRUNCATE TABLE nodes_config")
        self.cur.execute("TRUNCATE TABLE grid_edges")
        self.cur.execute("TRUNCATE TABLE grid_nodes")
        self.cur.execute("TRUNCATE TABLE charging_stations_config")
        self.cur.execute("TRUNCATE TABLE charging_stations_cur_state")
        area_id = 0
        area_lefttop = self.map_height - 1
        area_leftdown = 0
        area_righttop = self.map_height * self.map_width - 1
        area_rightdown = (self.map_width - 1) * self.map_height
        area_size = self.map_width * self.map_height
        self.cur.execute("INSERT INTO areas VALUES({},{},{},{},{},{})"
                         .format(area_id, area_lefttop, area_leftdown,
                                 area_righttop, area_rightdown,
                                 area_size))
        for i in range(self.map_width):
            for j in range(self.map_height):
                node_id = i * self.map_height + j
                pos_x = i
                pos_y = j
                visited = False
                visit_cap = 1
                visit_count = 0
                victims_num = 0
                need_rescue = False
                if node_id in self.charge_pos_list:
                    node_type = 2  # charging stations
                    visited = True
                else:
                    node_type = 0  # normal points
                self.cur.execute("INSERT INTO nodes_config VALUES({},{},{},{})"
                                 .format(node_id, pos_x, pos_y, visit_cap))
                self.cur.execute(
                    "INSERT INTO grid_nodes VALUES({},{},{},{},{},{})".format(node_id, visit_count,
                                                                              visited, victims_num,
                                                                              need_rescue, node_type))
        edge_id = -1
        for i in range(self.map_width * self.map_height):
            from_id = i
            if i - self.map_width >= 0:
                to_id = i - self.map_width
                edge_id += 1
                self.cur.execute("INSERT INTO grid_edges VALUES({},{},{},{})".format(from_id, to_id, edge_id, 1.0))
            if i + self.map_width < self.map_height * self.map_height:
                to_id = i + self.map_width
                edge_id += 1
                self.cur.execute("INSERT INTO grid_edges VALUES({},{},{},{})".format(from_id, to_id, edge_id, 1.0))
            if i - 1 >= i - i % self.map_width:
                to_id = i - 1
                edge_id += 1
                self.cur.execute("INSERT INTO grid_edges VALUES({},{},{},{})".format(from_id, to_id, edge_id, 1.0))
            if i + 1 < (i + self.map_width) - (i + self.map_width) % self.map_width:
                to_id = i + 1
                edge_id += 1
                self.cur.execute("INSERT INTO grid_edges VALUES({},{},{},{})".format(from_id, to_id, edge_id, 1.0))

        for i in range(self.charge_num):
            node_id = self.charge_pos_list[i]
            station_id = i
            is_inservice = True
            charging_cap = self.agent_num / self.charge_num
            cur_utilization = 0
            queue_cap = self.agent_num / self.charge_num
            queue_length = 0
            dock_cap = self.agent_num
            dock_num = 0
            cur_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            self.cur.execute("INSERT INTO charging_stations_config VALUES({},{},{},{},{})".format(
                station_id, node_id, charging_cap, queue_cap, dock_cap
            ))
            self.cur.execute("INSERT INTO charging_stations_cur_state VALUES({},{},{},{},{},'{}')".format(
                station_id, is_inservice, cur_utilization, queue_length,
                dock_num, cur_timestamp
            ))

        self.cur.execute("SELECT * FROM areas")
        rows = self.cur.fetchall()
        print(rows)
        self.cur.execute("SELECT * FROM nodes_config")
        rows = self.cur.fetchall()
        print(rows)
        self.cur.execute("SELECT * FROM grid_nodes")
        rows = self.cur.fetchall()
        print(rows)
        self.cur.execute("SELECT * FROM grid_edges")
        rows = self.cur.fetchall()
        print(rows)
        self.cur.execute("SELECT * FROM charging_stations_config")
        rows = self.cur.fetchall()
        print(rows)
        self.cur.execute("SELECT * FROM charging_stations_cur_state")
        rows = self.cur.fetchall()
        print(rows)

    def initNewAgentViews(self):
        self.cur.execute("TRUNCATE TABLE drones_config")
        self.cur.execute("TRUNCATE TABLE drones_cur_state")
        uav_count = 0
        for j in range(len(self.agent_g_num)):
            fleet_id = j
            for i in range(self.agent_g_num[j]):
                uav_id = uav_count
                uav_count += 1
                if j != 2:
                    loc_node_id = random.randint(0, self.map_height * self.map_width)
                else:
                    loc_node_id = random.choice(self.charge_pos_list)
                sense_range = 2.0
                view_range = 4.0
                load_cap = 0
                load_num = 0
                max_electricity = self.expconfig.MAX_E
                cur_electricity = self.expconfig.MAX_E
                charge_efficiency = 1
                flying_state = 1
                cur_path_length = 0
                cur_resource_cost = 0
                workload = 0
                completed_workload = 0
                cur_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                self.cur.execute(
                    "INSERT INTO drones_cur_state VALUES({},{},{},{},{},{},{},{},'{}')".format(
                        uav_id, loc_node_id, view_range,
                        load_num, cur_electricity, flying_state,
                        cur_path_length, cur_resource_cost, cur_timestamp
                    ))
                self.cur.execute("INSERT INTO drones_config VALUES({},{},{},{},{},{})"
                                 .format(uav_id, fleet_id, sense_range, load_cap, max_electricity,
                                         charge_efficiency))

        self.cur.execute("SELECT * FROM drones_config")
        rows = self.cur.fetchall()
        print(rows)
        self.cur.execute("SELECT * FROM drones_cur_state")
        rows = self.cur.fetchall()
        print(rows)

    def initNewTaskViews(self):
        cur_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        self.cur.execute("TRUNCATE TABLE delivery_task_targets")
        self.cur.execute("TRUNCATE TABLE delivery_cur_state")
        self.cur.execute("TRUNCATE TABLE rescue_support_task_targets")
        self.cur.execute("TRUNCATE TABLE rescue_support_cur_state")
        self.cur.execute("TRUNCATE TABLE search_coverage_history_states")
        self.cur.execute("TRUNCATE TABLE search_coverage_task")
        self.cur.execute("TRUNCATE TABLE rescue_support_task")
        self.cur.execute("TRUNCATE TABLE delivery_task")

        self.cur.execute("INSERT INTO search_coverage_task VALUES(0,null,0,'{}',null)".format(cur_timestamp))
        self.cur.execute("INSERT INTO rescue_support_task VALUES(0,'{}',null,0,null,1)".format(cur_timestamp))
        self.cur.execute("INSERT INTO delivery_task VALUES(0,'{}',null,0,null,2)".format(cur_timestamp))

    def initDefaultEnv(self, charge_list=None, drone_locs=None):
        if drone_locs is not None and charge_list is not None:

            d_list = list(
                set(range(self.map_height * self.map_width)).difference(set(drone_locs[0].values())).difference(
                    set(drone_locs[2].values())).difference(set(charge_list)))
            danger_list = np.random.choice(a=d_list, size=self.danger_num, replace=False, p=None)

            a_list = list(set(range(self.map_height * self.map_width)).difference(
                set(drone_locs[0].values()).union(set(drone_locs[1].values())).union(
                    set(drone_locs[2].values()))).difference(set(charge_list)).difference(set(danger_list)))
            blocked_list = list(np.random.choice(a=a_list, size=self.obstacle_num, replace=False, p=None))
        elif charge_list is None and drone_locs is None:
            num = self.obstacle_num + self.charge_num
            s_list = list(np.random.choice(a=self.map_width * self.map_height, size=num, replace=False, p=None))
            blocked_list = list(np.random.choice(a=s_list, size=self.obstacle_num, replace=False, p=None))
            charge_list = list(set(s_list).difference(set(blocked_list)))
            d_list = list(
                set(range(self.map_width * self.map_height)).difference(set(blocked_list)).difference(set(charge_list)))
            danger_list = list(np.random.choice(a=d_list, size=self.danger_num, replace=False, p=None))
        else:
            print("Waring: Valid operation when initializing Concrete Env, It may cause unexpected event later.")
        rand_vic_point = list(np.random.choice(a=danger_list,size=1,replace=False,p=None))
        Nodes = []
        for i in range(self.map_width):
            Nodes.append([])
            for j in range(self.map_height):
                nid = i * self.map_height + j
                if nid in blocked_list:
                    node_type = 1
                    victims_num = 0
                    need_rescue = False
                    load_demand_num = 0
                elif nid in charge_list:
                    node_type = 2
                    victims_num = 0
                    need_rescue = False
                    load_demand_num = 0
                elif nid in danger_list:
                    node_type = 3
                    if nid in rand_vic_point:
                        victims_num = random.randint(1, self.expconfig.MAX_LOAD)
                        need_rescue = True
                    else:
                        victims_num = 0
                        need_rescue = False
                    load_demand_num = 0
                else:
                    node_type = 0
                    e = random.uniform(0, 1)
                    # there are refuge_prob possibility that this safe grid is a refuge
                    if e <= self.expconfig.refuge_prob:
                        victims_num = self.expconfig.S_max + 1
                        load_demand_num = 1
                    else:
                        victims_num = random.randint(0, self.expconfig.S_max)
                        load_demand_num = 0
                    need_rescue = False
                # victims_num = random.randint(0, 10)
                # need_rescue = bool(random.randint(0, 1))
                visited = False
                visit_count = 0
                t_request = 0
                if node_type != 2:
                    p_ = Point(nid=i * self.map_height + j, pos_x=i, pos_y=j, node_type=node_type,
                               victims_num=victims_num, need_rescue=need_rescue,
                               visited=visited, visit_count=visit_count,
                               t_request=t_request, load_demand_num=load_demand_num)
                else:
                    p_ = ChargingPoint(sid=charge_list.index(nid), nid=i * self.map_height + j, pos_x=i, pos_y=j,
                                       cur_utilization=0, queue_length=0)
                Nodes[i].append(p_)

        Edges = []
        edge_id = -1
        for i in range(self.map_width * self.map_height):
            from_id = i
            if Nodes[int(i / self.map_height)][int(i % self.map_height)].blocked:
                dis = self.static_info.EDGE_INX
            else:
                dis = 1
            if i - self.map_width >= 0:
                to_id = i - self.map_width
                if dis > 1:
                    tmp_dis = dis
                else:
                    if Nodes[int(to_id / self.map_height)][int(to_id % self.map_height)].blocked:
                        tmp_dis = self.static_info.EDGE_INX
                    else:
                        tmp_dis = 1
                edge_id += 1
                Edges.append(Edge(eid=edge_id, from_p=from_id, to_p=to_id, distance=tmp_dis))
            if i + self.map_width < self.map_height * self.map_height:
                to_id = i + self.map_width
                if dis > 1:
                    tmp_dis = dis
                else:
                    if Nodes[int(to_id / self.map_height)][int(to_id % self.map_height)].blocked:
                        tmp_dis = self.static_info.EDGE_INX
                    else:
                        tmp_dis = 1
                edge_id += 1
                Edges.append(Edge(eid=edge_id, from_p=from_id, to_p=to_id, distance=tmp_dis))
            if i - 1 >= i - i % self.map_width:
                to_id = i - 1
                if dis > 1:
                    tmp_dis = dis
                else:
                    if Nodes[int(to_id / self.map_height)][int(to_id % self.map_height)].blocked:
                        tmp_dis = self.static_info.EDGE_INX
                    else:
                        tmp_dis = 1
                edge_id += 1
                Edges.append(Edge(eid=edge_id, from_p=from_id, to_p=to_id, distance=tmp_dis))
            if i + 1 < (i + self.map_width) - (i + self.map_width) % self.map_width:
                to_id = i + 1
                if dis > 1:
                    tmp_dis = dis
                else:
                    if Nodes[int(to_id / self.map_height)][int(to_id % self.map_height)].blocked:
                        tmp_dis = self.static_info.EDGE_INX
                    else:
                        tmp_dis = 1
                edge_id += 1
                Edges.append(Edge(eid=edge_id, from_p=from_id, to_p=to_id, distance=tmp_dis))

        return Nodes, Edges

    def ClearDBInitializer(self):
        self.conn.commit()
        self.cur.close()
        self.conn.close()


if __name__ == '__main__':
    initializer = GlobalDataInitializer(agent_num=[2, 0], map_width=3, map_height=3, charge_num=1, charge_pos_list=[5])
    initializer.initNewMapViews()
    initializer.initNewAgentViews()
    # initializer.initGlobalAgentViews()
    initializer.ClearDBInitializer()
