import sys
import json
import os
import random
import time
import psycopg2

sys.path.append('../')
from scripts.DataGenerator import *
from framework.CustomExceptions import *
from framework.QueryTool import *



class ConcreteEnv:
    def __init__(self, charge_list, drone_locs, datasrc=None, metadata='../data/metadata.json'):
        """
        Description:
            Init the concrete map of the environment according to real data or default setting.
        Parameters:
            datasrc: File path or database connection info to the real environment data.
            metadata: If datasrc exist, metadata will include the basic description info for the concrete environment,
            and these data is generated when processing the source data. Otherwise, the metadata will include the default
            or user setting of the initial environment.
        Returns:
            None
        """
        self.charge_list = charge_list
        # random.seed(time.time())
        if metadata and os.path.isfile(metadata):
            with open(file=metadata, mode='r') as fr:
                metadata = json.loads("".join(fr.readlines()))['metadata']
                # print(metadata)
                self.width = metadata['width']
                self.height = metadata['height']
                self.node_num = metadata['node_num']
                self.edge_num = metadata['edge_num']
                self.charge_num = metadata['charge_num']
                self.obstacle_num = metadata['obstacle_num']
                self.danger_num = metadata['danger_num']
                self.env_change_prob = metadata['env_change_prob']
                # 环境变化概率,list[3],分别表示bolcked,victims_num,need_rescue的变化概率
                self.stat_change_prob = metadata['stat_change_prob']
                # station状态变化概率,list[2],分别表示station是否处于可用状态,以及处于station中无人机数量随机变化的概率
            if datasrc and os.path.isfile(datasrc):
                # define datasrc structure and process the real data into specific structure
                # create Points & Edges objects according to datasrc
                with open(file=datasrc, mode='r') as fr:
                    default = json.loads("".join(fr.readlines()))
                    def_nodes = default['nodes']
                    def_edges = default['edges']
                    self.Nodes = []
                    self.Edges = []
                    drone_ids = [[],[],[]]
                    danger_dis = []
                    block_dis = []
                    safe_dis = []
                    for i in range(self.width):
                        self.Nodes.append([])
                        for j in range(self.height):
                            node = def_nodes[i][j]
                            if node['node_type'] != 2:
                                new_p = Point(nid=node['node_id'],
                                              pos_x=node['pos_x'],
                                              pos_y=node['pos_y'],
                                              node_type=node['node_type'],
                                              victims_num=node['victims_num'],
                                              need_rescue=node['need_rescue'],
                                              visited=node['visited'],
                                              visit_count=node['visit_count'],
                                              t_request=node['t_request'])
                                if node['node_type'] == 1:
                                    block_dis.append(node['node_id'])
                                else:
                                    danger_dis.append(node['node_id'])
                                if node['node_type'] == 1 or node['node_type'] == 3:
                                    if node['node_id'] in drone_locs.values():
                                        d_id_0 = list(drone_locs[0].keys())[list(drone_locs[0].values()).index(node['node_id'])]
                                        d_id_1 = list(drone_locs[1].keys())[list(drone_locs[1].values()).index(node['node_id'])]
                                        d_id_2 = list(drone_locs[2].keys())[list(drone_locs[2].values()).index(node['node_id'])]
                                        drone_ids[0].append(d_id_0)
                                        drone_ids[1].append(d_id_1)
                                        drone_ids[2].append(d_id_2)
                                else:
                                    safe_dis.append(node['node_id'])
                            else:
                                safe_dis.append(node['node_id'])
                                new_p = ChargingPoint(sid=node['station_id'],
                                                      nid=node['node_id'],
                                                      pos_x=node['pos_x'],
                                                      pos_y=node['pos_y'],
                                                      t_request=node['t_request'],
                                                      charging_cap=node['charging_cap'],
                                                      queue_cap=node['queue_cap'],
                                                      dock_cap=node['dock_cap'],
                                                      is_inservice=node['is_inservice'],
                                                      cur_utilization=node['cur_utilization'],
                                                      queue_length=node['queue_length'],
                                                      dock_num=node['dock_num']
                                                      )
                            self.Nodes[i].append(new_p)
                    for i in range(self.edge_num):
                        edge = def_edges[i]
                        new_e = Edge(eid=edge['edge_id'],
                                     from_p=edge['from_id'],
                                     to_p=edge['to_id'],
                                     distance=edge['distance']
                                     )
                        new_e.travel_time = edge['travel_time']
                        self.Edges.append(new_e)

                    qt = QueryTool()
                    list_0 = list(set(safe_dis).difference(set(drone_locs[0].values).union(set(drone_locs[1].values)).union(set(drone_locs[2].values))))
                    new_locs_0 = list(np.random.choice(a=list_0,size=len(drone_ids[0]),replace=False,p=None))
                    new_locs_2 = list(np.random.choice(a=list(set(list_0).difference(set(new_locs_0))),size=len(drone_ids[2]),replace=False,p=None))
                    list_1 = set(list_0).difference(set(new_locs_0)).difference(set(new_locs_2)).union(set(danger_dis).difference(set(drone_locs[1])))
                    new_locs_1 = list(np.random.choice(a=list_1,size = len(drone_ids[1], replace=False,p=None)))

                    new_locs = [new_locs_0,new_locs_1,new_locs_2]
                    # a_list = list(set(range(self.width * self.height)).difference(set(not_allow_locs)))
                    # new_locs = list(np.random.choice(a=a_list, size=len(drone_ids), replace=False, p=None))

                    qt.update_drones_location(
                        drone_ids=drone_ids,
                        new_locs=new_locs,
                    )
                    qt.clear_db_connection()
            else:
                with open(file='../data/default_env.json', mode='w') as fw:
                    dg = GlobalDataInitializer(agent_num=None, map_width=self.width,
                                               map_height=self.height, charge_num=self.charge_num,
                                               obstacle_num=self.obstacle_num, danger_num=self.danger_num,
                                               charge_pos_list=None, db_used=False)
                    self.Nodes, self.Edges = dg.initDefaultEnv(charge_list=self.charge_list, drone_locs=drone_locs)
                    nodes_json = []
                    for i in range(self.width):
                        nodes_json.append([])
                        for j in range(self.height):
                            node = {}
                            node['node_id'] = self.Nodes[i][j].NID
                            node['pos_x'] = self.Nodes[i][j].pos_x
                            node['pos_y'] = self.Nodes[i][j].pos_y
                            if self.Nodes[i][j].blocked:
                                node['node_type'] = 1
                            elif self.Nodes[i][j].is_charge_p:
                                node['node_type'] = 2
                            elif self.Nodes[i][j].danger_level == 1:
                                node['node_type'] = 3
                            else:
                                node['node_type'] = 0
                            node['visited'] = self.Nodes[i][j].visited
                            node['visit_count'] = self.Nodes[i][j].visit_count
                            node['victims_num'] = self.Nodes[i][j].victims_num
                            node['need_rescue'] = self.Nodes[i][j].need_rescue
                            node['t_request'] = self.Nodes[i][j].t_request
                            if node['node_type'] == 2:
                                node['station_id'] = self.Nodes[i][j].sid
                                node['charging_cap'] = self.Nodes[i][j].charging_cap
                                node['queue_cap'] = self.Nodes[i][j].queue_cap
                                node['dock_cap'] = self.Nodes[i][j].dock_cap
                                node['is_inservice'] = self.Nodes[i][j].is_inservice
                                node['cur_utilization'] = self.Nodes[i][j].cur_utilization
                                node['queue_length'] = self.Nodes[i][j].queue_length
                                node['dock_num'] = self.Nodes[i][j].dock_num
                            nodes_json[i].append(node)
                    edges_json = []
                    for i in range(self.edge_num):
                        edge = {}
                        edge['edge_id'] = self.Edges[i].EID
                        edge['from_id'] = self.Edges[i].from_p
                        edge['to_id'] = self.Edges[i].to_p
                        edge['distance'] = self.Edges[i].distance
                        edge['travel_time'] = self.Edges[i].travel_time
                        edges_json.append(edge)
                    map_json = {'nodes': nodes_json, 'edges': edges_json}
                    fw.write(json.dumps(map_json))
                    fw.flush()
        else:
            raise CustomError("Lacking of metadata when initializing the environment!")

    def update(self):
        for i in range(self.width):
            for j in self.height:
                self.Nodes[i][j].update()
        for i in range(self.edge_num):
            self.Edges[i].update()


class LocalViewMap:

    def __init__(self, data=None):
        self.exp_config = ExperimentConfig()
        self.Edges = {}
        self.Nodes = {}
        self.Neighbors = {}
        if data:
            n_col_names = data[0][0]
            n_records = data[0][1]  # list of list(record)
            e_col_names = data[1][0]
            e_records = data[1][1]  # list of list(record)
            u_col_names = data[2][0]
            u_records = data[2][1]
            for i in range(len(n_records)):
                node = {}
                for col in range(len(n_col_names)):
                    node[n_col_names[col]] = n_records[i][col]
                new_p = Point(nid=node['node_id'],
                              pos_x=node['pos_x'],
                              pos_y=node['pos_y'],
                              node_type=node['node_type'],
                              victims_num=node['victims_num'],
                              need_rescue=node['need_rescue'],
                              visited=node['visited'],
                              visit_count=node['visit_count'],
                              t_request=node['visit_cap']
                              )
                self.Nodes[node['node_id']] = new_p
            for j in range(len(e_records)):
                edge = {}
                for col in range(len(e_col_names)):
                    edge[e_col_names[col]] = e_records[j][col]
                new_e = Edge(eid=edge['edge_id'],
                             from_p=edge['from_id'],
                             to_p=edge['to_id'],
                             distance=edge['distance'])
                self.Edges[edge['from_id'] + '_' + edge['to_id']] = new_e
            for k in range(len(u_records)):
                neighbor = {}
                # u_record: uav_id, loc_node_id
                for col in range(len(u_col_names)):
                    neighbor[u_col_names[col]] = u_records[k][col]
                self.Neighbors[neighbor['loc_node_id']] = neighbor['neighbor_id']

        self.update_state = [{}, {}, [], [], []]
        for key in self.Nodes.keys():
            self.update_state[0][key] = (False, None)
        for key in self.Edges.keys():
            self.update_state[1][key] = (False, None)

        self.charge_targets = []
        self.rescue_targets = {}
        self.delivery_targets = {}

        for i in range(len(self.charge_targets)):
            self.update_state[2].append((False, None))
        for i in range(len(self.rescue_targets)):
            self.update_state[3].append((False, None))
        for i in range(len(self.rescue_targets)):
            self.update_state[4].append((False, None))

    def update_map(self, data, sense_time=None):
        try:
            if sense_time:
                # 利用感知到的数据更新地图
                # 在新数据记录上标记True,不更新的记录上标记False,并且标记感知时间
                # 在sense的时候一定是事先有了非空的self.Nodes与self.Edges且sense到的内容应该是与其对应的
                new_nodes_data = data[0]
                new_edges_data = data[1]
                # 需要根据Drones.UAV的sense_within_range函数决定这里怎么写
                # 看传入的data是要更新的点还是所有点需要再判断是不是更新了
                # 应该是只传入要更新的点,查找更新时根据nid与eid对应
                for key, value in new_nodes_data.items():
                    self.Nodes[key] = value
                    self.update_state[0][key] = (True, sense_time)
                for key, value in new_edges_data.items():
                    self.Edges[key] = value
                    self.update_state[1][key] = (True, sense_time)
                return True
            else:
                # 利用从center获取的view数据更新地图
                # 所有数据记录都把更新标记标为False
                self.Edges.clear()
                self.Nodes.clear()
                self.Neighbors.clear()
                self.update_state[0].clear()
                self.update_state[1].clear()

                n_col_names = data[0][0]
                n_records = data[0][1]  # list of list(record)
                e_col_names = data[1][0]
                e_records = data[1][1]  # list of list(record)
                u_col_names = data[2][0]
                u_records = data[2][1]

                for i in range(len(n_records)):
                    node = {}
                    for col in range(len(n_col_names)):
                        node[n_col_names[col]] = n_records[i][col]
                    new_p = Point(nid=node['node_id'],
                                  pos_x=node['pos_x'],
                                  pos_y=node['pos_y'],
                                  node_type=node['node_type'],
                                  victims_num=node['victims_num'],
                                  need_rescue=node['need_rescue'],
                                  visited=node['visited'],
                                  visit_count=node['visit_count'],
                                  t_request=node['visit_cap']
                                  )
                    self.Nodes[node['node_id']] = new_p
                    self.update_state[0][node['node_id']] = (False, None)
                for j in range(len(e_records)):
                    edge = {}
                    for col in range(len(e_col_names)):
                        edge[e_col_names[col]] = e_records[j][col]
                    new_e = Edge(eid=edge['edge_id'],
                                 from_p=edge['from_id'],
                                 to_p=edge['to_id'],
                                 distance=edge['distance'])
                    self.Edges[(edge['from_id'], edge['to_id'])] = new_e
                    self.update_state[1][(edge['from_id'], edge['to_id'])] = (False, None)
                for k in range(len(u_records)):
                    neighbor = {}
                    # u_record: uav_id, loc_node_id
                    for col in range(len(u_col_names)):
                        neighbor[u_col_names[col]] = u_records[k][col]
                    self.Neighbors[neighbor['loc_node_id']] = neighbor['neighbor_id']

                return True
        except Exception as e:
            print(e)
            return False

    def update_charge_stations(self, data, sense_time=None):
        # TODO: if get from view, set (FALSE,NONE); else update and set (TRUE,TIME)
        return True

    def update_rescue_targets(self, data, sense_time=None):
        # TODO: if get from view, set (FALSE,NONE); else update and set (TRUE,TIME)
        try:
            if sense_time is not None:
                #从环境中观察到的目标信息
                for key, value in data.items():
                    self.rescue_targets[key] = (value, True)
                    self.update_state[3][key] = (True, sense_time)
                return True
            else:
                #从中心获取的信息
                self.update_state[3].clear()
                self.rescue_targets.clear()
                t_col_names = data[0][0]
                t_records = data[0][1]
                for i in range(len(t_records)):
                    target = {}
                    for col in range(len(t_col_names)):
                        target[t_col_names[col]] = t_records[i][col]

                    new_p = Point(nid=target['target_id'],
                                  pos_x=target['pos_x'],
                                  pos_y=target['pos_y'],
                                  node_type=3,
                                  victims_num=target['victims_num'],
                                  need_rescue=True,
                                  visited=False
                                  )
                    if target['is_allocated'] and not target['is_completed']:
                        self.rescue_targets[target['target_id']] = (new_p, False)
                    # else:
                    #     self.rescue_targets[target['target_id']] = (new_p, True)
                    self.update_state[3][target['target_id']] = (False, None)
                return True
        except Exception as e:
            print(e)
            return False

    def update_delivery_targets(self, data, sense_time=None):
        # TODO: if get from view, set (FALSE,NONE); else update and set (TRUE,TIME)
        try:
            if sense_time is not None:
                for key, value in data.items():
                    self.delivery_targets[key] = (value, True)
                    self.update_state[4][key] = (True, sense_time)
                return True
            else:
                # 从中心获取的信息
                self.update_state[4].clear()
                self.delivery_targets.clear()
                t_col_names = data[0][0]
                t_records = data[0][1]
                for i in range(len(t_records)):
                    target = {}
                    for col in range(len(t_col_names)):
                        target[t_col_names[col]] = t_records[i][col]
                    new_p = Point(nid=target['target_id'],
                                  pos_x=target['pos_x'],
                                  pos_y=target['pos_y'],
                                  node_type=0,
                                  victims_num=self.exp_config.S_max+1,
                                  load_demand_num=target['load_demand_num'],
                                  need_rescue=False,
                                  visited=False
                                  )
                    if target['is_allocated'] and not target['is_completed']:
                        self.delivery_targets[target['target_id']] = (new_p,False)

                    self.update_state[4][target['target_id']] = (False, None)
                return True
        except Exception as e:
            print(e)
            return False
