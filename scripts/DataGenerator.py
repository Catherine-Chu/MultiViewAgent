# -*- coding:utf-8 -*-
import psycopg2
import random
import time

class GlobalDataInitializer:

    def __init__(self,agent_num,map_width,map_height,charge_num,charge_pos_list):
        self.agent_num = agent_num[0]+agent_num[1]
        self.agent_g_num = agent_num
        self.map_width = map_width
        self.map_height = map_height
        self.charge_num = charge_num
        self.charge_pos_list = charge_pos_list
        self.conn = psycopg2.connect(database='multiAgents', user='chuwenjie', password='2399321cwj', host='127.0.0.1', port='5432')
        self.cur = self.conn.cursor()

    def initGlobalMapViews(self):
        self.cur.execute("TRUNCATE TABLE grid_edges")
        self.cur.execute("TRUNCATE TABLE charging_stations")
        self.cur.execute("TRUNCATE TABLE grid_nodes")
        for i in range(self.map_height):
            for j in range(self.map_width):
                node_id = i * self.map_width + j
                pos_x = i
                pos_y = j
                is_blocked = False
                visited = False
                visit_cap = 1
                visit_count = 0
                victims_num = 0
                need_rescue = False
                if node_id in self.charge_pos_list:
                    node_type = 2 # charging stations
                else:
                    node_type = 1 # normal points
                self.cur.execute("INSERT INTO grid_nodes VALUES({},{},{},{},{},{},{},{},{},{})".format(node_id,pos_x,pos_y,is_blocked,visited,visit_cap,visit_count,victims_num,need_rescue,node_type))
        edge_id = -1
        for i in range(self.map_width * self.map_height):
            from_id = i
            if i-self.map_width >= 0:
                to_id = i-self.map_width
                edge_id += 1
                self.cur.execute("INSERT INTO grid_edges VALUES({},{},{},{})".format(from_id,to_id,edge_id,1.0))
            if i+self.map_width < self.map_height*self.map_height:
                to_id = i+self.map_width
                edge_id += 1
                self.cur.execute("INSERT INTO grid_edges VALUES({},{},{},{})".format(from_id,to_id,edge_id,1.0))
            if i-1 >= i-i%self.map_width:
                to_id = i-1
                edge_id += 1
                self.cur.execute("INSERT INTO grid_edges VALUES({},{},{},{})".format(from_id,to_id,edge_id,1.0))
            if i+1 < (i+self.map_width)-(i+self.map_width)%self.map_width:
                to_id = i+1
                edge_id += 1
                self.cur.execute("INSERT INTO grid_edges VALUES({},{},{},{})".format(from_id,to_id,edge_id,1.0))

        for i in range(self.charge_num):
            node_id = self.charge_pos_list[i]
            station_id = i
            self.cur.execute("SELECT pos_x,pos_y FROM grid_nodes WHERE grid_nodes.node_id = {}".format(node_id))
            pos_ = self.cur.fetchone()
            pos_x = pos_[0]
            pos_y = pos_[1]
            print(pos_x, pos_y)
            is_inservice = True
            charging_cap = self.agent_num/self.charge_num
            cur_utilization = 0
            queue_cap = self.agent_num/self.charge_num
            queue_length = 0
            dock_cap = self.agent_num
            dock_num = 0
            self.cur.execute("INSERT INTO charging_stations VALUES({},{},{},{},{},{},{},{},{},{},{})".format(
                node_id,station_id,pos_x,pos_y,is_inservice,charging_cap,cur_utilization,queue_cap,queue_length,dock_cap,dock_num
            ))

        self.cur.execute("SELECT * FROM grid_nodes")
        rows = self.cur.fetchall()
        print(rows)
        self.cur.execute("SELECT * FROM grid_edges")
        rows = self.cur.fetchall()
        print(rows)
        self.cur.execute("SELECT * FROM charging_stations")
        rows = self.cur.fetchall()
        print(rows)

    def initGlobalAgentViews(self):
        uav_count = 0
        for j in range(len(self.agent_g_num)):
            fleet_id = j+1
            for i in range(self.agent_g_num[j]):
                uav_id = uav_count
                uav_count += 1
                loc_node_id = random.randint(0,self.map_height *self.map_width)
                self.cur.execute("SELECT pos_x,pos_y FROM grid_nodes WHERE grid_nodes.node_id = {}".format(loc_node_id))
                pos_ = self.cur.fetchone()
                pos_x = pos_[0]
                pos_y = pos_[1]
                sense_range = 2.0
                view_range = 4.0
                load_cap = 0
                load_num = 0
                max_electricity = 30
                cur_electricity = 30
                charge_efficiency = 1
                flying_state = 1
                cur_path_length = 0
                cur_resource_cost = 0
                workload = 0
                completed_workload = 0
                self.cur.execute("INSERT INTO drones_cur_state VALUES({},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{})".format(
                    uav_id,loc_node_id,pos_x,pos_y,fleet_id,sense_range,view_range,load_cap,
                    load_num,max_electricity,cur_electricity,charge_efficiency,flying_state,
                    cur_path_length,cur_resource_cost,workload,completed_workload
                ))
        self.cur.execute("SELECT * FROM drones_cur_state")
        rows = self.cur.fetchall()
        print(rows)

    def initNewMapViews(self):
        self.cur.execute("TRUNCATE TABLE areas")
        self.cur.execute("TRUNCATE TABLE nodes_config")
        self.cur.execute("TRUNCATE TABLE grid_edges")
        self.cur.execute("TRUNCATE TABLE grid_nodes")
        self.cur.execute("TRUNCATE TABLE charging_stations_config")
        self.cur.execute("TRUNCATE TABLE charging_stations_cur_state")
        area_id = 0
        area_lefttop = (self.map_height-1)*self.map_width
        area_leftdown = 0
        area_righttop = self.map_height*self.map_width-1
        area_rightdown = self.map_width-1
        area_size = self.map_width*self.map_height
        self.cur.execute("INSERT INTO areas VALUES({},{},{},{},{},{})"
                         .format(area_id,area_lefttop,area_leftdown,
                                 area_righttop,area_rightdown,
                                 area_size))
        for i in range(self.map_height):
            for j in range(self.map_width):
                node_id = i * self.map_width + j
                pos_x = i
                pos_y = j
                visited = False
                visit_cap = 1
                visit_count = 0
                victims_num = 0
                need_rescue = False
                if node_id in self.charge_pos_list:
                    node_type = 2  # charging stations
                else:
                    node_type = 0  # normal points
                self.cur.execute("INSERT INTO nodes_config VALUES({},{},{},{})"
                                 .format(node_id,pos_x,pos_y,visit_cap))
                self.cur.execute(
                    "INSERT INTO grid_nodes VALUES({},{},{},{},{},{})".format(node_id,visit_count,
                                                                              visited,victims_num,
                                                                              need_rescue,node_type))
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
            cur_timestamp = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
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
            fleet_id = j + 1
            for i in range(self.agent_g_num[j]):
                uav_id = uav_count
                uav_count += 1
                loc_node_id = random.randint(0, self.map_height * self.map_width)
                sense_range = 2.0
                view_range = 4.0
                load_cap = 0
                load_num = 0
                max_electricity = 30
                cur_electricity = 30
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
                        cur_path_length, cur_resource_cost,cur_timestamp
                    ))
                self.cur.execute("INSERT INTO drones_config VALUES({},{},{},{},{},{})"
                                 .format(uav_id,fleet_id,sense_range,load_cap,max_electricity,
                                         charge_efficiency))

        self.cur.execute("SELECT * FROM drones_config")
        rows = self.cur.fetchall()
        print(rows)
        self.cur.execute("SELECT * FROM drones_cur_state")
        rows = self.cur.fetchall()
        print(rows)

    def initNewTaskViews(self):
        a = 0

    def ClearInitializer(self):
        self.conn.commit()
        self.cur.close()
        self.conn.close()


if __name__ == '__main__':
    initializer = GlobalDataInitializer(agent_num=[2,0],map_width=3,map_height=3,charge_num=1,charge_pos_list=[5])
    initializer.initNewMapViews()
    initializer.initNewAgentViews()
    #initializer.initGlobalAgentViews()
    initializer.ClearInitializer()