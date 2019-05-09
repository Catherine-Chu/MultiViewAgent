# -*- coding:utf-8 -*-
import sys
import math
import random
import time
from socket import *
from threading import Thread
from threading import Lock
import json
import heapq
import tkinter as tk
import copy
import numpy as np
import argparse
import matplotlib.pyplot as plt

sys.path.append('../')
from framework.CustomExceptions import *
from framework.StaticConsensus import *
from framework.QueryTool import *
from framework.EnvMap import *
from baseline.BoB import *
from framework.MyThread import *

# import os
# import psutil
import yappi

global global_map
global agents_path
global agents_pos
global g_visited
# global next_pos

global map_lock
global paths_lock
global pos_lock
# global next_lock


class UAV:

    def __init__(self, ID, experiment_config=ExperimentConfig(), X=None, Y=None, NID=None):
        if X is None and Y is None and NID is None:
            self._running = True  # used to control the termination of agent process and its child threads.
            self.STATIC_INFO = StaticInfo()  # static consensus info between agents and center
            self.experiment_config = experiment_config
            self.alpha = self.experiment_config.HYBRID_ALPHA

            # arguments related to socket connections with center
            self.HOST = '127.0.0.1'
            self.PORT = 8080
            # self.socket = None
            self.UID = ID

            self.Local_View_Map = LocalViewMap()  # 空局部地图View
            self.cur_charge_tar = None
            self.cur_rescue_tar = []
            self.cur_delivery_tar = None

            self.action_space = [(0, 1, 1), (0, -1, 1), (-1, 0, 1), (1, 0, 1), (0, 0, 1), (0, 0, 0)]
            self.path_buffer = []
            self.start = True
            self.TID = None

            self.his_step = []
            self.cloud_cpu_clock = 0
            self.broadcast_cpu_clock = 0
            self.connect_cost = 0
            self.connect_count = 0
            self.hybrid_rd = 0
            self.broadcast_rd = 0

            #     self.state_init()
            #
            # def state_init(self):
            try:
                get_data = self.connect_with_center(RoW='R', View_List=[2], GoL='L')  # list
                colnames = get_data[0][0]  # list
                rows = get_data[0][1]  # list[tuple,tuple,...]
                while rows is None:
                    print("Error in initializing configuration for the drone. Try again!")
                    get_data = self.connect_with_center(RoW='R', View_List=[2], GoL='L')  # list
                    colnames = get_data[0][0]  # list
                    rows = get_data[0][1]  # list[tuple,tuple,...]
                self.FID = rows[0][colnames.index('fleet_id')]
                self.cur_NID = rows[0][colnames.index('loc_node_id')]
                self.cur_PX = rows[0][colnames.index('pos_x')]
                self.cur_PY = rows[0][colnames.index('pos_y')]
                self.VR = rows[0][colnames.index('view_range')]
                self.SR = rows[0][colnames.index('sense_range')]
                self.E = rows[0][colnames.index('max_electricity')]
                self.CE = rows[0][colnames.index('charge_efficiency')]
                self.L_CAP = rows[0][colnames.index('load_cap')]
                self.cur_State = rows[0][colnames.index('flying_state')]
                self.cur_PLen = rows[0][colnames.index('cur_path_length')]
                self.cur_E = rows[0][colnames.index('cur_electricity')]
                self.cur_RCost = rows[0][colnames.index('cur_resource_cost')]  # 0:无损坏 1:轻微损坏,可选维修 2:严重损坏,必须尽快维修
                self.cur_LN = rows[0][colnames.index('load_num')]
            except Exception as e:
                print(e)
            # 在init情况下,所有uav的flying_state只有可能是0或1
            # 在reset情况下,首先reset的是数据库中drones,map等相关的数据,然后再重新从数据中init
            # 即无人机reset函数的调用必须在环境reset及中心全局数据reset之后
            # 1)环境状态reset 2)全局数据reset 3)中心属性reset 4)agents属性reset
            # 如果环境和关于环境的全局数据保持最新状态，仅想要reset所有的无人机则
            # 1)全局数据中关于drones state的数据reset 2)中心中有关drones的属性reset 3)agents属性reset

        else:
            self._running = True  # used to control the termination of agent process and its child threads.
            self.STATIC_INFO = StaticInfo()  # static consensus info between agents and center
            self.experiment_config = experiment_config
            self.alpha = self.experiment_config.HYBRID_ALPHA
            self.UID = ID
            self.action_space = [(0, 1, 1), (0, -1, 1), (-1, 0, 1), (1, 0, 1), (0, 0, 1), (0, 0, 0)]
            self.path_buffer = []
            self.start = True

            self.FID = 0
            self.cur_NID = NID
            self.cur_PX = X
            self.cur_PY = Y
            self.VR = 4
            self.SR = 2
            self.E = 100
            self.CE = 1
            self.cur_State = 1
            self.cur_PLen = 0
            self.cur_E = 100
            self.cur_RCost = 0  # 0:无损坏 1:轻微损坏,可选维修 2:严重损坏,必须尽快维修
            self.cur_LN = 0
            self.TID = 0

            self.his_step = []
            self.cloud_cpu_clock = 0
            self.broadcast_cpu_clock = 0
            self.connect_cost = 0
            self.connect_count = 0

            self.hybrid_rd = 0
            self.broadcast_rd = 0
        # self.cloud_cpu_clock = 0
        # self.broadcast_cpu_clock = 0
        # self.connect_cost = 0

    def reset(self):
        # if self.socket is not None:
        #     self.socket.close()
        # self.socket = None
        self._running = True
        # self.state_init()

    def terminate(self):
        self._running = False
        # if self.socket is not None:
        #     self.socket.close()

    def connect_with_center(self, RoW='R', View_List=None, GoL='L', Datas=None, SQLs=None, Compute=False, Func=None,
                            args=None, in_thread=False):
        connect_start = time.clock()
        cur_socket = socket(AF_INET, SOCK_STREAM)
        cur_socket.connect((self.HOST, self.PORT))
        if not Compute:
            send_data = self.before_send_request(RoW, View_List, GoL, Datas, SQLs)
        else:
            if RoW == 'R':
                send_data = {'RoW': 'R',
                             'GoL': 'G',
                             'Compute': True,
                             'uav_id': self.UID,
                             'task_id': self.TID,
                             'loc_node_id': self.cur_NID,
                             'func': Func,
                             'args': args,
                             'request_time': time.time()}
            else:
                send_data = {'RoW': 'W',
                             'GoL': 'G',
                             'Compute': True,
                             'uav_id': self.UID,
                             'task_id': self.TID,
                             'loc_node_id': self.cur_NID,
                             'func': Func,
                             'args': args,
                             'request_time': time.time(),
                             'sense_time': args['sense_time']}
        send_data = json.dumps(send_data)
        cur_socket.send(send_data.encode())
        cur_socket.send("*".encode())
        get_data = None
        total_data = []
        data = None


        try:
            while True:

                # self.socket.setblocking(0)

                data = cur_socket.recv(4096)
                if not data:
                    # print("Without receiving data.")
                    break
                data = data.decode()
                # print("1.",data)

                if self.STATIC_INFO.END in data:
                    data = data[:data.find(self.STATIC_INFO.END)]
                    if data != "Put is done." and not (
                            data == "Request is received." or data == "Request is in queue." or data == 'Data Ready.'):
                        # print("2.",data)
                        total_data.append(data)
                    break

                if data == "Request is received." or data == "Request is in queue." or data == 'Data Ready.':
                    # print(data)
                    continue
                elif data == "Put is done.":
                    # print("Put is done.")
                    break
                else:
                    total_data.append(data)
            temp_data = ''.join(total_data)
            if len(temp_data) > 0:
                # print("Receiving meaningful data.")
                # print("3.",temp_data)
                data = json.loads(temp_data)
                # print("4.",data)
                if isinstance(data, list) or isinstance(data, dict):
                    # print('1 done')
                    cur_socket.send('Data is received.*'.encode())
                    # print('2 done')
                    # self.socket.send("*".encode())
                    # print('3 donne')
                    get_data = data
                    # print('3 done')
                    # print(get_data)
                else:
                    raise CustomError('Returned wrong data!')

        except Exception as e:
            print("Exception when receiving data from center. May be for bad json.")
            print(get_data)
            print(e)
            cur_socket.close()

        # time.sleep(4)
        cur_socket.close()
        connect_end = time.clock()
        if not in_thread:
            self.connect_cost += (connect_end - connect_start)
            self.connect_count += 1
        return get_data

    def before_send_request(self, RoW, View_List, GoL, Datas, SQLs):
        send_data = {}
        uav_id = self.UID
        send_data['uav_id'] = uav_id
        try:
            if GoL == 'L':
                send_data['GoL'] = 'L'
                if View_List:
                    view_index_list = View_List
                    send_data['view_index_list'] = view_index_list
                else:
                    raise CustomError('None view list in the local request!')
                request_time = time.time()
                send_data['request_time'] = request_time
                try:
                    if RoW == 'R':
                        send_data['RoW'] = 'R'
                        return send_data
                    elif RoW == 'W':
                        if Datas:
                            sense_time = Datas['sense_time']
                            view_data_list = Datas['new_data']
                            send_data['view_data_list'] = view_data_list
                            send_data['sense_time'] = sense_time
                        else:
                            raise CustomError('None data in the local writing request!')
                        send_data['RoW'] = 'W'
                        return send_data
                    else:
                        raise CustomError('RoW Type Error!')
                except CustomError as e:
                    print(e)
                    send_data.clear()
            elif GoL == 'G':
                send_data['GoL'] = 'G'
                if SQLs:
                    sql_list = SQLs
                    send_data['sql_list'] = sql_list
                else:
                    raise CustomError('None sql list in the global request!')
                request_time = time.time()
                send_data['request_time'] = request_time
                try:
                    if RoW == 'R':
                        send_data['RoW'] = 'R'
                        return send_data
                    elif RoW == 'W':
                        if Datas:
                            send_data['sense_time'] = Datas['sense_time']
                        else:
                            raise CustomError('None data in the global writing request!')
                        send_data['RoW'] = 'W'
                        return send_data
                    else:
                        raise CustomError('RoW Type Error!')
                except CustomError as e:
                    print(e)
                    send_data.clear()
            else:
                raise CustomError('GoL Type Error!')
        except CustomError as e:
            print(e)
            send_data.clear()
        return send_data

    def test(self):
        while self._running:
            # read request test
            get_data = self.connect_with_center(RoW='R', View_List=[3], GoL='L')
            get_data = self.connect_with_center(RoW='R', View_List=[4], GoL='L')
            break

    def broadcast_run_search(self, env):
        self.broadcast_rd = 0

        drone_start_clock = time.clock()

        self.TID = 0
        self.cur_State = 1

        def update_shared_map():
            g_visited[self.cur_NID] = True
            for pl in range(len(pos_lock)):
                with pos_lock[pl]:
                    agents_pos[pl][self.UID] = self.cur_NID

            within_nodes = []
            for lock_i, map_lock_i in enumerate(map_lock):
                with map_lock_i:
                    within_nodes.clear()
                    for i in range(self.cur_PX - self.SR, self.cur_PX + self.SR + 1, 1):
                        for j in range(self.cur_PY - self.SR, self.cur_PY + self.SR + 1, 1):
                            if 0 <= i < env.width and 0 <= j < env.height:
                                if math.pow(i - self.cur_PX, 2) + math.pow(j - self.cur_PY, 2) <= math.pow(
                                        self.SR,
                                        2):
                                    env_node = env.Nodes[i][j]
                                    within_nodes.append(env_node.NID)
                                    n_key = i * env.height + j
                                    tmp_visited_state = global_map[lock_i].Nodes[n_key].visited
                                    global_map[lock_i].Nodes[n_key] = env_node
                                    global_map[lock_i].Nodes[n_key].visited = tmp_visited_state
                    global_map[lock_i].Nodes[self.cur_NID].visited = True

                    for from_p in within_nodes:
                        for to_p in within_nodes:
                            e_key = str(from_p) + '_' + str(to_p)
                            if e_key in list(global_map[lock_i].Edges.keys()):
                                env_edge = env.Edges[global_map[lock_i].Edges[e_key].EID]
                                global_map[lock_i].Edges[e_key] = env_edge

            return True, within_nodes

        def map_random_lose(maxr, within_nodes):
            maxn = int((2*maxr+1)*(2*maxr+1))
            n_list=list(range(len(global_map[self.UID].Nodes)))
            left_list = list(set(n_list).difference(set(within_nodes)))
            if maxn>=len(within_nodes):
                if maxn-len(within_nodes)<= len(left_list):
                    final_list = random.sample(left_list, maxn - len(within_nodes))
                else:
                    final_list = left_list
                final_list.extend(within_nodes)
            else:
                final_list = within_nodes
            for i in range(len(global_map[self.UID].Nodes)):
                if i not in final_list:
                    if global_map[self.UID].Nodes[i].blocked:
                        global_map[self.UID].Nodes[i].blocked = False
                        x = int(i / env.height)
                        y = int(i % env.height)
                        direct = [(0,1),(0,-1),(1,0),(-1,0)]
                        for dir in direct:
                            to_x = x+dir[0]
                            to_y = y+dir[1]
                            if 0<=to_x<env.width and 0<=to_y<env.height:
                                to_p = to_x*env.height + to_y
                                if not global_map[self.UID].Nodes[to_p].blocked:
                                    e_key = str(i)+'_'+str(to_p)
                                    global_map[self.UID].Edges[e_key].distance = 1
                                    e_key = str(to_p)+'_'+str(i)
                                    global_map[self.UID].Edges[e_key].distance = 1
                    else:
                        global_map[self.UID].Nodes[i].visited = False

            return True

        def BoB_movement(scale, within_nodes=None):
            if len(self.path_buffer) == 0:
                with map_lock[self.UID]:
                    map_random_lose(self.experiment_config.MAX_MEMORY, within_nodes)
                    not_end_point, next_x, next_y, self.his_step = boustrophedon_step(global_map[self.UID], scale,
                                                                                      self.action_space,
                                                                                      self.cur_PX, self.cur_PY,
                                                                                      self.UID, self.FID,
                                                                                      self.his_step)
                if not_end_point:
                    # with next_lock[self.UID]:
                    #     next_pos_id = next_x * scale[1]+next_y
                    #     if next_pos_id in list(next_pos[self.UID].values()):
                    #         print("sleep here and recalculation")
                    #         time.sleep(0.2)
                    #         with map_lock[self.UID]:
                    #             not_end_point, next_x, next_y, self.his_step = boustrophedon_step(global_map[self.UID], scale,
                    #                                                                               self.action_space,
                    #                                                                               self.cur_PX, self.cur_PY,
                    #                                                                               self.UID, self.FID,
                    #                                                                               self.his_step)
                    #             next_pos_id = next_x * scale[1]+next_y
                    #     else:
                    #         next_pos[self.UID][self.UID]= next_pos_id
                    #
                    # for np in range(len(next_lock)):
                    #     if np != self.UID:
                    #         with next_lock[np]:
                    #             next_pos[np][self.UID] = next_pos_id
                    #
                    next_nid = next_x * scale[1] + next_y
                    pass
                else:
                    with pos_lock[self.UID]:
                        pos_list = {v: k for k, v in agents_pos[self.UID].items()}
                    # local planning
                    with map_lock[self.UID]:
                        with paths_lock[self.UID]:
                            back_points = find_backtracking_points(global_map[self.UID], scale, pos_list,
                                                                   agents_path[self.UID])
                            # print("get_points: ", back_points)

                            if len(back_points) > 0:
                                tar_x, tar_y, agents_path[self.UID][self.UID] = find_shortest_backtracking_path(scale,
                                                                                                                global_map[
                                                                                                                    self.UID],
                                                                                                                self.cur_PX,
                                                                                                                self.cur_PY,
                                                                                                                back_points)
                                if not agents_path[self.UID][self.UID]:
                                    agents_path[self.UID][self.UID] = []
                            else:
                                agents_path[self.UID][self.UID] = []

                            self.path_buffer = copy.deepcopy(agents_path[self.UID][self.UID])
                            # print("get_paths:", self.path_buffer)

                    for ap in range(len(agents_path)):
                        if ap != self.UID:
                            with paths_lock[ap]:
                                agents_path[ap][self.UID] = copy.deepcopy(self.path_buffer)

                    if self.path_buffer and len(self.path_buffer) > 0:
                        start_p = self.path_buffer.pop(-1)
                        self.path_buffer.reverse()
                        next_nid = self.path_buffer[0]
                        next_x = int(next_nid / scale[1])
                        next_y = int(next_nid % scale[1])
                    else:
                        next_nid = None
                        next_x = None
                        next_y = None
                    # with next_lock[self.UID]:
                    #     if next_nid in list(next_pos[self.UID].values()):
                    #         time.sleep(0.2)
                return next_nid, next_x, next_y
            else:
                # if path_buffer is not empty, then there exist a path through covered area (known area
                # within visited or blocked nodes)
                next_nid = self.path_buffer[0]
                next_x = int(next_nid / scale[1])
                next_y = int(next_nid % scale[1])
                return next_nid, next_x, next_y

        def is_done():
            result = True
            for key, nodes in global_map[self.UID].Nodes.items():
                if nodes.visited or nodes.blocked or nodes.danger_level > 0:
                    continue
                else:
                    result = False
                    break
            return result

        max_step = 2*(env.width * env.height) # 400%的冗余度
        while self._running:
            time.sleep(0.5)
            if self.cur_State == 0:
                self.cur_State = 1
                self.TID = 0
            elif self.cur_State == 1:
                if self.TID == 0:
                    # working in search_coverage_task
                    if max_step>0 and not is_done():
                        _, within_nodes = update_shared_map()
                        next_nid, next_x, next_y = BoB_movement((env.width, env.height),within_nodes)
                        if next_nid is not None:
                            sense_time = self.bob_move(next_nid, next_x, next_y)
                            max_step -= 1
                        else:
                            self.cur_State = 5
                            break
                    else:
                        self.cur_State = 5
                        break

            elif self.cur_State == 2:
                # TODO: GO FOR CHARGING
                self.cur_State = 5
                break
            elif self.cur_State == 3:
                # TODO: WAITING FOR CHARGING
                self.cur_State = 4
                continue
            elif self.cur_State == 4:
                # TODO: IN CHARGING
                self.cur_State = 0
                continue
            else:
                self.cur_State = 5
                self._running = False
        # 主进程要求终止后，需要处理的收尾工作
        update_shared_map()
        if self.cur_State == 5 and self._running:
            self._running = False
        drone_end_clock = time.clock()
        self.broadcast_cpu_clock = drone_end_clock - drone_start_clock
        return None

    def run(self, env):
        self.hybrid_rd = 0
        try:
            # State Machine
            drone_start_clock = time.clock()
            self.connect_cost = 0
            self.connect_count = 0
            while self._running:
                # 无人机正常飞行过程中的主要逻辑，包括什么时候调用self.connect_with_center函数/创建线程
                if self.cur_State == 0:
                    # WW: Waiting For Work State
                    if self.is_allocated_task():
                        self.cur_State = 1
                        sense_time = time.time()
                        new_data = [
                            [{'UID': self.UID, 'NID': self.cur_NID, 'VR': self.VR, 'LN': self.cur_LN, 'CE': self.cur_E,
                              'FS': 1, 'CL': self.cur_PLen, 'RC': self.cur_RCost}]]
                        self.connect_with_center(RoW='W', View_List=[2], GoL='L',
                                                 Datas={'sense_time': sense_time, 'new_data': new_data}, SQLs=None)
                        # daemon=false相当于在主线程最后调用thread.join方法,子线程为后台线程，主线程完成后会等待子线程结束然后再结束
                        # daemon=true则主线程结束,子线程自动结束
                    else:
                        if self.TID is None:
                            time.sleep(5)
                            continue
                        else:
                            self.cur_State = 5  # 标识任务结束
                            # 不需要同步到中心,中心中drones_state表里的flying_state=5应该在中心添加end_time的时候同步更新了,
                            # 现在agent能够进入到这里说明中心已经更新过数据,这是agent主动获取到的关于任务的新数据,因为在WW状态下agent只能通过对
                            # 任务数据的查询判断自己应不应该进行状态变迁
                            # 当然也可以对每个agent也建立监听socket,用于接收来自center主动发出的控制数据
                            # (当前的通信连接都是agent主动发起的,center不能更新数据后立刻让agent知道,这能是agent需要数据或者决定查询的时候将
                            # 新数据同步到agent,这样是为了避免agent时刻维持监听耗费资源,被动接受自己不需要的数据)
                            break
                elif self.cur_State == 1:
                    # IW: In Working State:
                    if self.TID is None:
                        self.is_allocated_task()
                        if self.TID is None:
                            self.cur_State = 0
                            sense_time = time.time()
                            new_data = [
                                [{'UID': self.UID, 'NID': self.cur_NID, 'VR': self.VR, 'LN': self.cur_LN, 'CE': self.cur_E,
                                  'FS': 0, 'CL': self.cur_PLen, 'RC': self.cur_RCost}]]
                            self.connect_with_center(RoW='W', View_List=[2], GoL='L', Datas={'sense_time': sense_time,
                                                                                             'new_data': new_data},
                                                     SQLs=None)
                            continue
                    if self.TID == 0:
                        # working in search_coverage_task
                        # if not self.is_work_done(0):
                        get_data = self.connect_with_center(RoW='R', View_List=[0, 1, 6], GoL='L')
                        # 以下两句会将Local_View_Map中的数据更新到最新,第一句得到的数据均标记为未更新(因为是从center拿到的)
                        # 第二句中sense到的并且和Local_View_Map中数据不一致的要更新,并把所有更新过的标记为已更新
                        self.Local_View_Map.update_map(get_data)
                        sense_time = self.sense_within_range(env)
                        healthy = self.self_check()
                        if healthy:
                            new_data = self.gen_new_data(View_List=[0, 1, 2])
                            self.connect_with_center(RoW='W', View_List=[0, 1, 2], GoL='L',
                                                     Datas={'sense_time': sense_time,
                                                            'new_data': new_data},
                                                     SQLs=None)

                            next_nid, next_x, next_y = self.make_move_decision(tid=0, scale=(env.width, env.height))
                            if next_nid is not None:
                                sense_time = self.move(next_nid, next_x, next_y)
                                new_data = [[{'UID': self.UID, 'NID': self.cur_NID, 'VR': self.VR, 'LN': self.cur_LN,
                                              'CE': self.cur_E,
                                              'FS': 1, 'CL': self.cur_PLen, 'RC': self.cur_RCost}]]
                                self.connect_with_center(RoW='W', View_List=[2], GoL='L',
                                                         Datas={'sense_time': sense_time,
                                                                'new_data': new_data},
                                                         SQLs=None)
                            else:
                                # when drone can't find next start point within local view data, it need to increase
                                # the view range parameters

                                # if self.VR < math.sqrt(env.width * env.width + env.height * env.height):
                                #     self.VR = math.ceil(math.sqrt(env.width * env.width + env.height * env.height))
                                #     sense_time = time.time()
                                #     new_data = [
                                #         [{'UID': self.UID, 'NID': self.cur_NID, 'VR': self.VR, 'LN': self.cur_LN,
                                #           'CE': self.cur_E,
                                #           'FS': 1, 'CL': self.cur_PLen, 'RC': self.cur_RCost}]]
                                #     self.connect_with_center(RoW='W', View_List=[2], GoL='L',
                                #                              Datas={'sense_time': sense_time,
                                #                                     'new_data': new_data},
                                #                              SQLs=None)
                                #     continue
                                # else:
                                #     self.cur_State = 5
                                #     break
                                self.cur_State = 5
                                break
                        else:
                            #     new_data = self.gen_new_data(View_List=[0, 1, 2])
                            #     self.connect_with_center(RoW='W', View_List=[0, 1, 2], GoL='L',
                            #                              Datas={'sense_time': sense_time,
                            #                                     'new_data': new_data},
                            #                              SQLs=None)
                            #     # time.sleep(1)
                            #     get_data, _ = self.connect_with_center(RoW='R', View_List=[3], GoL='L')
                            #
                            #     # print("\n\n\n")
                            #     # print("Charge tar view reading check")
                            #     # print(get_data)
                            #     # print(len(get_data))  # 1
                            #     # print(len(get_data[0]))  # 2
                            #     # print(len(get_data[0][1]))  # 可选充电目标点数目,目前的表格中初步估计为0
                            #     # print("\n\n\n")
                            #
                            #     charge_tar = get_data[0]
                            #
                            #     self.Local_View_Map.update_charge_stations(charge_tar)
                            self.cur_State = 2
                        # else:
                        #     self.cur_State = 5
                        #     break
                    elif self.TID == 1:
                        # working in rescue_coverage_task
                        if not self.is_work_done(1):
                            get_data = self.connect_with_center(RoW='R', View_List=[0, 1, 6, 4], GoL='L')
                            # 以下两句会将Local_View_Map中的数据更新到最新,第一句得到的数据均标记为未更新(因为是从center拿到的)
                            # 第二句中sense到的并且和Local_View_Map中数据不一致的要更新,并把所有更新过的标记为已更新
                            self.Local_View_Map.update_map(get_data[0:3])
                            self.Local_View_Map.update_rescue_targets(get_data[3])
                            self.cur_rescue_tar = self.choose_rescue_target()
                            sense_time = self.sense_within_range(env)
                            healthy = self.self_check()
                            if healthy:
                                new_data = self.gen_new_data(View_List=[0, 1, 2, 4])
                                self.connect_with_center(RoW='W', View_List=[0, 1, 2, 4], GoL='L',
                                                         Datas={'sense_time': sense_time,
                                                                'new_data': new_data},
                                                         SQLs=None)

                                next_nid, next_x, next_y = self.make_move_decision(tid=1, scale=(env.width, env.height))
                                if next_nid is not None:
                                    if abs(next_x - self.cur_PX) + abs(next_y - self.cur_PY) > 1:
                                        print("Error in moving decision for rescue tasks!")
                                        self.cur_State = 5
                                        break
                                    else:
                                        sense_time = self.move(next_nid, next_x, next_y)
                                        new_data = [
                                            [{'UID': self.UID, 'NID': self.cur_NID, 'VR': self.VR, 'LN': self.cur_LN,
                                              'CE': self.cur_E,
                                              'FS': 1, 'CL': self.cur_PLen, 'RC': self.cur_RCost}]]
                                        self.connect_with_center(RoW='W', View_List=[2], GoL='L',
                                                                 Datas={'sense_time': sense_time,
                                                                        'new_data': new_data},
                                                                 SQLs=None)
                                else:
                                    if self.VR < math.sqrt(env.width * env.width + env.height * env.height) / 2:
                                        self.VR = math.floor(math.sqrt(env.width * env.width + env.height * env.height) / 2)
                                        sense_time = time.time()
                                        new_data = [
                                            [{'UID': self.UID, 'NID': self.cur_NID, 'VR': self.VR, 'LN': self.cur_LN,
                                              'CE': self.cur_E,
                                              'FS': 1, 'CL': self.cur_PLen, 'RC': self.cur_RCost}]]
                                        self.connect_with_center(RoW='W', View_List=[2], GoL='L',
                                                                 Datas={'sense_time': sense_time,
                                                                        'new_data': new_data},
                                                                 SQLs=None)
                                        continue
                                    else:
                                        self.cur_State = 5
                                        break
                            # else:
                            #     new_data = self.gen_new_data(View_List=[0, 1, 2, 4])
                            #     self.connect_with_center(RoW='W', View_List=[0, 1, 2, 4], GoL='L',
                            #                              Datas={'sense_time': sense_time,
                            #                                     'new_data': new_data},
                            #                              SQLs=None)
                            #     # time.sleep(1)
                            #
                            #     get_data, _ = self.connect_with_center(RoW='R', View_List=[3], GoL='L')
                            #
                            #     charge_tar = get_data[0]
                            #     self.Local_View_Map.update_charge_stations(charge_tar)
                            #     self.cur_State = 2
                        else:
                            self.cur_State = 5
                            break
                    elif self.TID == 2:
                        # working in delivery_task
                        if not self.is_work_done(2):
                            get_data = self.connect_with_center(RoW='R', View_List=[0, 1, 6, 5], GoL='L')
                            # 以下两句会将Local_View_Map中的数据更新到最新,第一句得到的数据均标记为未更新(因为是从center拿到的)
                            # 第二句中sense到的并且和Local_View_Map中数据不一致的要更新,并把所有更新过的标记为已更新
                            self.Local_View_Map.update_map(get_data[0:3])
                            self.Local_View_Map.update_delivery_targets(get_data[3])
                            self.cur_delivery_tar = self.choose_delivery_target()
                            sense_time = self.sense_within_range(env)
                            healthy = self.self_check()
                            if healthy:
                                new_data = self.gen_new_data(View_List=[0, 1, 2, 5])
                                self.connect_with_center(RoW='W', View_List=[0, 1, 2, 5], GoL='L',
                                                         Datas={'sense_time': sense_time,
                                                                'new_data': new_data},
                                                         SQLs=None)

                                next_nid, next_x, next_y = self.make_move_decision(tid=2, scale=(env.width, env.height))
                                if next_nid is not None:
                                    sense_time = self.move(next_nid, next_x, next_y)
                                    new_data = [[{'UID': self.UID, 'NID': self.cur_NID, 'VR': self.VR, 'LN': self.cur_LN,
                                                  'CE': self.cur_E,
                                                  'FS': 1, 'CL': self.cur_PLen, 'RC': self.cur_RCost}]]
                                    self.connect_with_center(RoW='W', View_List=[2], GoL='L',
                                                             Datas={'sense_time': sense_time,
                                                                    'new_data': new_data},
                                                             SQLs=None)
                                else:
                                    if self.VR < math.sqrt(env.width * env.width + env.height * env.height) / 2:
                                        self.VR = math.floor(math.sqrt(env.width * env.width + env.height * env.height) / 2)
                                        sense_time = time.time()
                                        new_data = [
                                            [{'UID': self.UID, 'NID': self.cur_NID, 'VR': self.VR, 'LN': self.cur_LN,
                                              'CE': self.cur_E,
                                              'FS': 1, 'CL': self.cur_PLen, 'RC': self.cur_RCost}]]
                                        self.connect_with_center(RoW='W', View_List=[2], GoL='L',
                                                                 Datas={'sense_time': sense_time,
                                                                        'new_data': new_data},
                                                                 SQLs=None)
                                        continue
                                    else:
                                        self.cur_State = 5
                                        break
                            else:
                                new_data = self.gen_new_data(View_List=[0, 1, 2, 5])
                                self.connect_with_center(RoW='W', View_List=[0, 1, 2, 5], GoL='L',
                                                         Datas={'sense_time': sense_time,
                                                                'new_data': new_data},
                                                         SQLs=None)
                                # time.sleep(1)

                                get_data = self.connect_with_center(RoW='R', View_List=[3], GoL='L')
                                charge_tar = get_data[0]
                                self.Local_View_Map.update_charge_stations(charge_tar)
                                self.cur_State = 2
                        else:
                            self.cur_State = 5
                            break
                elif self.cur_State == 2:
                    # TODO: GO FOR CHARGING
                    # if self.cur_charge_tar is None:
                    #     self.cur_charge_tar = self.choose_charging_station()
                    # if self.cur_NID != self.cur_charge_tar.NID:
                    #     # 飞到指定地点的过程中,cur_state=2不变
                    #     # 但要注意判断需不需要变更指定地点
                    #     # 判断依据是每到一个新地点都需要重新获取一次的charge targets view
                    #     continue
                    # else:
                    #     # 到达指定地点时进行判断,看能不能充电
                    #     # 注意:如果是由UAV主动变更charge targets view中充电站的属性,必须是到达该点的时候
                    #     # 其他时候view的主动变更直接由center操作(可以理解为充电站主体主动变更并告知了center,center直接修改了相关table数据)
                    #     if self.cur_charge_tar.cur_utilization < self.cur_charge_tar.charging_cap:
                    #         self.cur_State = 4
                    #     elif self.cur_charge_tar.queue_length < self.cur_charge_tar.queue_cap:
                    #         self.cur_State = 3
                    #     elif self.cur_charge_tar.dock_num < self.cur_charge_tar.dock_cap:
                    #         self.cur_State = 3  # 暂时dock在充电站等待进入等待充电的队列,以及在充电队列
                    #         # 再设置个量和上面的直接进入等待充电队列的分开,交给state=3的部分判断
                    #     else:
                    #         self.cur_State = 5  # 没有地方停,没有地方充电,只能是退出任务,随便找地方降落等待回收
                    #         break
                    self.cur_State = 5
                    break
                elif self.cur_State == 3:
                    # TODO: WAITING FOR CHARGING
                    self.cur_State = 4
                    continue
                elif self.cur_State == 4:
                    # TODO: IN CHARGING
                    self.cur_State = 0
                    continue
                else:
                    self.cur_State = 5
                    self._running = False
                # TODO
                #  time.sleep(2)
            # 主进程要求终止后，需要处理的收尾工作
            if self.cur_State == 5:
                sense_time = time.time()
                new_data = [
                    [{'UID': self.UID, 'NID': self.cur_NID, 'VR': self.VR, 'LN': self.cur_LN, 'CE': self.cur_E,
                      'FS': 5, 'CL': self.cur_PLen, 'RC': self.cur_RCost}]]
                self.connect_with_center(RoW='W', View_List=[2], GoL='L',
                                         Datas={'sense_time': sense_time, 'new_data': new_data}, SQLs=None)
                self.connect_with_center(RoW='W', GoL='G', Compute=True, Func='SetAgentsWorkState',
                                         args={'work_done': True,
                                               'sense_time': time.time()})
                self._running = False
                print("Notify the center for the ending of drone {}.".format(self.UID))
            drone_end_clock = time.clock()
            self.cloud_cpu_clock = drone_end_clock - drone_start_clock - self.connect_cost
            return None
        except Exception as e:
            print(e)
            return None

    def is_allocated_task(self):
        try:
            if self.FID == 0:
                self.TID = 0
                return True
            elif self.FID == 1:
                self.TID = 1
                return True
            elif self.FID == 2:
                self.TID = 2
                return True
            else:
                # 还没有被分配任务
                self.TID = None
                return False
        except Exception as e:
            print(e)
            return False

    def sense_within_range(self, env):

        def get_local_info(g_env):
            local_nodes = {}
            within_list = []
            for key, node in self.Local_View_Map.Nodes.items():
                if math.pow(node.pos_x - self.cur_PX, 2) + math.pow(node.pos_y - self.cur_PY, 2) <= math.pow(self.SR,
                                                                                                             2):
                    env_node = g_env.Nodes[node.pos_x][node.pos_y]
                    within_list.append(node.NID)
                    if not isinstance(env_node, ChargingPoint):
                        if not env_node == node:
                            local_nodes[key] = env_node

            local_edges = {}
            for key, edge in self.Local_View_Map.Edges.items():
                if edge.from_p in within_list and edge.to_p in within_list:
                    env_edge = g_env.Edges[edge.EID]
                    if not env_edge == edge:
                        local_edges[key] = env_edge
            local_ = (local_nodes, local_edges)
            return local_

        concrete_local = get_local_info(g_env=env)
        # update local view using concrete_local
        sense_time = time.time()

        # update view map的时候不能只按照concrete local来,有一些数据必须保留,
        # 比如visit_count要在原本数据的基础上加1,当前位置的visited改为True等
        # print(list(concrete_local[0].keys()))
        if not isinstance(env.Nodes[self.cur_PX][self.cur_PY], ChargingPoint):
            concrete_local[0][self.cur_NID].visited = True
            concrete_local[0][self.cur_NID].visit_count = self.Local_View_Map.Nodes[self.cur_NID].visit_count + 1
        self.Local_View_Map.update_map(concrete_local, sense_time)

        # TODO:除了update_map,还要视情况看需不需要更新charging_targets,rescue_targets,delivery_targets
        # rescue_cur_state,delivery_cur_state
        def get_local_rescue_tars(g_env):
            rescue_tars = {}
            g_env.Nodes[self.cur_PX][self.cur_PY].victims_num = 0  # 所有victims都被救走了
            env_node = g_env.Nodes[self.cur_PX][self.cur_PY]
            rescue_tars[self.cur_NID] = env_node
            return rescue_tars

        def get_local_delivery_tars(g_env):
            delivery_tars = {}
            g_env.Nodes[self.cur_PX][self.cur_PY].load_demand_num = 0  # 不再需要运输了
            env_node = g_env.Nodes[self.cur_PX][self.cur_PY]
            delivery_tars[self.cur_NID] = env_node
            return delivery_tars

        def get_local_charge_tars(g_env):
            charge_tars = []
            return charge_tars

        if self.cur_rescue_tar is not None and len(self.cur_rescue_tar) > 0:
            if self.cur_NID == self.cur_rescue_tar[0] and self.cur_State == 1 and self.TID == 1:
                concrete_rescue_tars = get_local_rescue_tars(env)
                self.Local_View_Map.update_rescue_targets(concrete_rescue_tars, sense_time)
                self.cur_rescue_tar.pop(0)
        if self.cur_delivery_tar is not None and len(self.cur_delivery_tar) > 0:
            if self.cur_NID == self.cur_delivery_tar[0] and self.cur_State == 1 and self.TID == 2:
                concrete_delivery_tars = get_local_delivery_tars(env)
                self.Local_View_Map.update_delivery_targets(concrete_delivery_tars, sense_time)
                self.cur_delivery_tar.pop(0)
        if self.cur_charge_tar is not None:
            if self.cur_NID == self.cur_charge_tar.NID and self.cur_State == 2:
                concrete_charge_tars = get_local_charge_tars(env)
                self.Local_View_Map.update_charge_stations(concrete_charge_tars, sense_time)

        return sense_time

    def self_check(self):
        if self.cur_E > self.E * (
                1 - self.experiment_config.C_Threshold) and self.cur_RCost != self.experiment_config.S_Damage:
            return True
        else:
            return False

    def gen_new_data(self, View_List=None):
        # arguments: self.Local_View_Map中Edges与Nodes中对更新记录的标记位
        new_data = []
        for i_, view_index in enumerate(View_List):
            new_data.append([])
            if view_index == 0:
                for n_, new_node in self.Local_View_Map.Nodes.items():
                    if self.Local_View_Map.update_state[0][n_][0]:
                        if new_node.blocked:
                            node_type = 1
                        elif new_node.is_charge_p:
                            node_type = 2
                        elif new_node.danger_level == 1:
                            node_type = 3
                        else:
                            node_type = 0
                        new_record = {'VC': new_node.visit_count,
                                      'V': new_node.visited,
                                      'VN': new_node.victims_num,
                                      'NR': new_node.need_rescue,
                                      'NT': node_type,
                                      'NID': new_node.NID,
                                      'UID': self.UID}
                        new_data[i_].append(new_record)
            elif view_index == 1:
                for e_, new_edge in self.Local_View_Map.Edges.items():
                    if self.Local_View_Map.update_state[1][e_][0]:
                        new_record = {
                            'DIS': new_edge.distance,
                            'EID': new_edge.EID
                        }
                        new_data[i_].append(new_record)
            elif view_index == 2:
                new_record = {'UID': self.UID, 'NID': self.cur_NID, 'VR': self.VR, 'LN': self.cur_LN, 'CE': self.cur_E,
                              'FS': 1, 'CL': self.cur_PLen, 'RC': self.cur_RCost}
                new_data[i_].append(new_record)
            elif view_index == 3:
                for t_, new_tar in enumerate(self.Local_View_Map.charge_targets):
                    if self.Local_View_Map.update_state[2][t_][0]:
                        new_record = {'II': new_tar.is_inservice,
                                      'CU': new_tar.cur_utilization,
                                      'QL': new_tar.queue_length,
                                      'DN': new_tar.dock_num,
                                      'SID': new_tar.sid}
                        new_data[i_].append(new_record)
            elif view_index == 4:
                # 只有当到达指定目标点的时候才有new_data(Local_View_Map中相应位置才会被标记)
                # 否则为空
                for t_, (new_tar, is_completed) in self.Local_View_Map.rescue_targets.items():
                    if self.Local_View_Map.update_state[3][t_][0]:
                        new_record = {'VN': new_tar.victims_num,
                                      'LDN': new_tar.load_demand_num,
                                      'IC': is_completed,
                                      'TID': new_tar.NID}
                        new_data[i_].append(new_record)
            elif view_index == 5:
                # 只有当到达指定目标点的时候才有new_data(Local_View_Map中相应位置才会被标记)
                # 否则为空
                for t_, (new_tar, is_completed) in self.Local_View_Map.delivery_targets.items():
                    if self.Local_View_Map.update_state[4][t_][0]:
                        new_record = {'LDN': new_tar.load_demand_num,
                                      'IC': is_completed,
                                      'TID': new_tar.NID}
                        new_data[i_].append(new_record)

        return new_data

    def make_move_decision(self, tid, scale, healthy=True, search_strategy='HybridBoB',
                           rescue_strategy='Z_Random_SSP', delivery_strategy='Random_NN'):
        # TODO: realize different moving strategies.
        if healthy:
            if tid == 0:
                if search_strategy == 'old_HybridBoB':
                    # BoB算法决策的基础是Grid中相邻两点之间的距离相等均为1
                    # cur_node = self.Local_View_Map.Nodes[self.cur_NID]
                    # TODO: New Bob
                    # if self.start:
                    #     l_o_r = 0  # -1:left, 1:right
                    #     u_o_d = 0  # -1:down, 1:up
                    #     if self.cur_PX <= scale[0] / 2:
                    #         self.l_o_r = 1
                    #     else:
                    #         self.l_o_r = -1
                    #     if self.cur_PY <= scale[1] / 2:
                    #         self.u_o_d = 1
                    #     else:
                    #         self.u_o_d = -1
                    #     self.start = False
                    prior_chioce = [0, 2, 1, 3]
                    has_next = False
                    valid_next = []
                    if len(self.path_buffer) == 0:
                        urgent_stats = []
                        for i in range(4):
                            has_neighbor = False
                            next_x = self.action_space[i][0] + self.cur_PX
                            next_y = self.action_space[i][1] + self.cur_PY
                            if 0 <= next_x < scale[0] and 0 <= next_y < scale[1]:
                                next_nid = next_x * scale[1] + next_y
                                next_node = self.Local_View_Map.Nodes[next_nid]
                                if next_nid in list(self.Local_View_Map.Neighbors.keys()):
                                    has_neighbor = True
                                is_valid = (not next_node.blocked and not next_node.visited) and \
                                           (not has_neighbor)
                                if next_node.is_charge_p:
                                    urgent_stats.append(next_node)
                                if self.FID == 0 or self.FID == 2:
                                    if next_node.danger_level > 0:
                                        is_valid = False

                                has_next = has_next or is_valid
                                if is_valid:
                                    valid_next.append(True)
                                else:
                                    valid_next.append(False)
                            else:
                                valid_next.append(False)
                                continue
                        if has_next:
                            # TODO: New Bob
                            # print("result 1 x,y:", self.cur_PX, self.cur_PY)
                            # next_y = self.cur_PY + self.u_o_d
                            # if 0 <= next_y < scale[1]:
                            #     print("result 1 next_y", next_y)
                            #     next_nid = self.cur_PX * scale[1] + next_y
                            #     next_node = self.Local_View_Map.Nodes[next_nid]
                            # if 0 <= next_y < scale[1] and (next_node.is_charge_p or (
                            #         not next_node.blocked and not next_node.visited)):
                            #     print("1 result, u_o_d: {}, l_o_r: {}".format(self.u_o_d, self.l_o_r))
                            #     return next_nid, self.cur_PX, next_y
                            # else:
                            #     print("result 2 x,y:", self.cur_PX, self.cur_PY)
                            #     next_y = self.cur_PY - self.u_o_d
                            #     if 0 <= next_y < scale[1]:
                            #         print("result 2 next_y", next_y)
                            #         next_nid = self.cur_PX * scale[1] + next_y
                            #         next_node = self.Local_View_Map.Nodes[next_nid]
                            #     if 0 <= next_y < scale[1] and (next_node.is_charge_p or (
                            #             not next_node.blocked and not next_node.visited)):
                            #         self.u_o_d = -self.u_o_d
                            #         print("2 result, u_o_d: {}, l_o_r: {}".format(self.u_o_d, self.l_o_r))
                            #         return next_nid, self.cur_PX, next_y
                            #     else:
                            #         print("result 3 x,y:", self.cur_PX, self.cur_PY)
                            #         next_x = self.cur_PX + self.l_o_r
                            #         if 0 <= next_x < scale[0]:
                            #             print("result 3 next_x", next_x)
                            #             next_nid = next_x * scale[1] + self.cur_PY
                            #             next_node = self.Local_View_Map.Nodes[next_nid]
                            #         if 0 <= next_x < scale[0] and (next_node.is_charge_p or (
                            #                 not next_node.blocked and not next_node.visited)):
                            #             self.u_o_d = -self.u_o_d
                            #             print("3 result, u_o_d: {}, l_o_r: {}".format(self.u_o_d, self.l_o_r))
                            #             return next_nid, next_x, self.cur_PY
                            #         else:
                            #             print("result 4 x,y:", self.cur_PX, self.cur_PY)
                            #             next_x = self.cur_PX - self.l_o_r
                            #             if 0 <= next_x < scale[0]:
                            #                 print("result 4 next_x", next_x)
                            #                 next_nid = next_x * scale[1] + self.cur_PY
                            #                 next_node = self.Local_View_Map.Nodes[next_nid]
                            #             if 0 <= next_x < scale[0] and (next_node.is_charge_p or (
                            #                     not next_node.blocked and not next_node.visited)):
                            #                 self.u_o_d = -self.u_o_d
                            #                 self.l_o_r = -self.l_o_r
                            #                 print("4 result, u_o_d: {}, l_o_r: {}".format(self.u_o_d, self.l_o_r))
                            #                 return next_nid, next_x, self.cur_PY
                            #             else:
                            #                 raise CustomError("No valid next action when has_next was TRUE!")
                            #                 return None, None, None
                            next_nid = None
                            next_x = None
                            next_y = None
                            for i in prior_chioce:
                                if valid_next[i]:
                                    next_x = self.cur_PX + self.action_space[i][0]
                                    next_y = self.cur_PY + self.action_space[i][1]
                                    next_nid = next_x * scale[1] + next_y
                                    break
                            return next_nid, next_x, next_y
                        else:
                            if len(urgent_stats) > 0:
                                next_node = random.choice(urgent_stats)
                                next_nid = next_node.NID
                                next_x = next_node.pos_x
                                next_y = next_node.pos_y
                                return next_nid, next_x, next_y
                            else:
                                # TODO:bob_find_new_start中有bug,会导致途径障碍物点(没有处理周围全是障碍物的特殊情况)
                                new_start, min_len = self.bob_find_new_start()
                                if new_start:
                                    next_node = self.Local_View_Map.Nodes[self.path_buffer[0]]
                                    next_x = next_node.pos_x
                                    next_y = next_node.pos_y
                                    next_nid = next_node.NID
                                    return next_nid, next_x, next_y
                                else:
                                    return None, None, None
                    else:
                        new_start, min_len = self.bob_find_new_start()
                        if new_start:
                            next_node = self.Local_View_Map.Nodes[self.path_buffer[0]]
                            next_x = next_node.pos_x
                            next_y = next_node.pos_y
                            next_nid = next_node.NID
                            return next_nid, next_x, next_y
                        else:
                            return None, None, None
                elif search_strategy == 'HybridBoB':
                    if len(self.path_buffer) == 0:
                        not_end_point, next_x, next_y, self.his_step = boustrophedon_step(self.Local_View_Map, scale,
                                                                                          self.action_space,
                                                                                          self.cur_PX, self.cur_PY,
                                                                                          self.UID, self.FID,
                                                                                          self.his_step)

                        if not not_end_point:
                            # 这里要connected with center,告知center调用全局信息与该函数进行全局计算,然后把结果通过通信链接反馈回来

                            # local planning
                            # get_data, _ = self.connect_with_center(RoW='R',GoL='G',Compute=True, Func='Get_BT_Paths')
                            # back_points = find_backtracking_points(self.Local_View_Map, scale, agents_path = get_data[0])
                            back_points = self.connect_with_center(RoW='R', GoL='G', Compute=True,
                                                                   Func='H_BoB_BT_Points')
                            # # 以参数alpha的置信度选择信任自己的决策结果,还是接收全局的决策结果
                            # if not back_points or self.alpha<0.8:
                            #     back_points = get_data[0]
                            if back_points:
                                back_points = back_points[0]
                                # print("get_points from center:", back_points)
                            else:
                                while back_points is None:
                                    print("Error! Don't get back_points from center, try again!")
                                    back_points = self.connect_with_center(RoW='R', GoL='G', Compute=True,
                                                                           Func='H_BoB_BT_Points')
                                back_points = back_points[0]

                            # 这里要connected with center,告知center调用全局信息与该函数进行全局计算,然后把结果通过通信链接反馈回来

                            back_points_left = []
                            for p in range(len(back_points)):
                                if back_points[p] in list(self.Local_View_Map.Nodes.keys()):
                                    back_points_left.append(back_points[p])
                            del back_points
                            back_points = copy.deepcopy(back_points_left)
                            # local planning
                            if back_points and len(back_points) > 0:
                                tar_x, tar_y, self.path_buffer = find_shortest_backtracking_path(scale,
                                                                                                 self.Local_View_Map,
                                                                                                 self.cur_PX,
                                                                                                 self.cur_PY,
                                                                                                 back_points)
                            else:
                                self.path_buffer = None

                            # # global planning
                            # con_thread = MyThread(func=self.connect_with_center,
                            #                       args=('R', None, 'G', None, None, True, 'H_BoB_BT_Paths', None, True))
                            # con_thread.start()
                            #
                            # # get_data = self.connect_with_center(RoW='R', GoL='G', Compute=True,
                            # #                                        Func='H_BoB_BT_Paths')
                            #
                            # if not self.path_buffer or self.alpha < self.experiment_config.HYBRID_ALPHA_T:
                            #     con_wait_time = time.clock()
                            #     get_data = con_thread.get_result()
                            #     con_wait_time = time.clock() - con_wait_time
                            #     self.connect_cost += con_wait_time
                            #     self.connect_count += 1
                            #     if get_data:
                            #         if get_data[0]:
                            #             # print("get_path from center:", get_data)
                            #             self.path_buffer = copy.deepcopy(get_data[0])
                            #         else:
                            #             print("No valid backtracking path, work done!")
                            #             self.path_buffer = None
                            #     else:
                            #         while not get_data:
                            #             print("Error! Don't get back_paths from center, try again!")
                            #             get_data = self.connect_with_center(RoW='R', GoL='G', Compute=True,
                            #                                                 Func='H_BoB_BT_Paths')
                            #         self.path_buffer = copy.deepcopy(get_data[0])
                            #
                            # # 由于SetAgentsPath请求是在H_BoB_BT_Paths请求同时/之后发出的,而center如果是根据请求队列顺序处理请求的话,
                            # # 就算agent这里没有等待H_BoB_BT_Paths返回结果,在等待SetAgentsPath返回的时候实际上还是要等center处理完
                            # # 上一个请求
                            self.connect_with_center(RoW='W', GoL='G', Compute=True, Func='SetAgentsPath',
                                                     args={'back_paths': self.path_buffer,
                                                           'sense_time': time.time()})
                            if self.path_buffer:
                                start_p = self.path_buffer.pop(-1)
                                self.path_buffer.reverse()
                                next_nid = self.path_buffer[0]
                                next_x = int(next_nid / scale[1])
                                next_y = int(next_nid % scale[1])
                            else:
                                return None, None, None
                        else:
                            next_nid = next_x * scale[1] + next_y

                        return next_nid, next_x, next_y
                    else:
                        # if path_buffer is not empty, then there exist a path through covered area (known area
                        # within visited or blocked nodes)
                        next_nid = self.path_buffer[0]
                        next_x = int(next_nid / scale[1])
                        next_y = int(next_nid % scale[1])
                        return next_nid, next_x, next_y
                # elif search_strategy == 'BoB':

            elif tid == 1:
                prior_chioce = [0, 2, 1, 3]
                has_next = False
                valid_next = []
                if len(self.path_buffer) == 0:
                    if self.cur_rescue_tar is None or len(self.cur_rescue_tar) == 0:
                        urgent_stats = []
                        for i in range(4):
                            has_neighbor = False
                            next_x = self.action_space[i][0] + self.cur_PX
                            next_y = self.action_space[i][1] + self.cur_PY
                            if 0 <= next_x < scale[0] and 0 <= next_y < scale[1]:
                                next_nid = next_x * scale[1] + next_y
                                next_node = self.Local_View_Map.Nodes[next_nid]
                                if next_nid in list(self.Local_View_Map.Neighbors.keys()):
                                    has_neighbor = True
                                is_valid = (not next_node.blocked and not next_node.visited) and \
                                           (not has_neighbor)
                                if next_node.is_charge_p:
                                    urgent_stats.append(next_node)
                                if self.FID == 0 or self.FID == 2:
                                    if next_node.danger_level > 0:
                                        is_valid = False

                                has_next = has_next or is_valid
                                if is_valid:
                                    valid_next.append(True)
                                else:
                                    valid_next.append(False)
                            else:
                                valid_next.append(False)
                                continue
                        if has_next:
                            next_nid = None
                            next_x = None
                            next_y = None
                            for i in prior_chioce:
                                if valid_next[i]:
                                    next_x = self.cur_PX + self.action_space[i][0]
                                    next_y = self.cur_PY + self.action_space[i][1]
                                    next_nid = next_x * scale[1] + next_y
                                    break
                            return next_nid, next_x, next_y
                        else:
                            if len(urgent_stats) > 0:
                                next_node = random.choice(urgent_stats)
                                next_nid = next_node.NID
                                next_x = next_node.pos_x
                                next_y = next_node.pos_y
                                return next_nid, next_x, next_y
                            else:
                                next_x = None
                                next_y = None
                                next_nid = None
                                valid_next.clear()
                                has_neighbors = False
                                for i in range(4):
                                    has_neighbor = False
                                    next_x = self.action_space[i][0] + self.cur_PX
                                    next_y = self.action_space[i][1] + self.cur_PY
                                    if 0 <= next_x < scale[0] and 0 <= next_y < scale[1]:
                                        next_nid = next_x * scale[1] + next_y
                                        next_node = self.Local_View_Map.Nodes[next_nid]
                                        if next_nid in list(self.Local_View_Map.Neighbors.keys()):
                                            has_neighbor = True
                                        is_valid = not next_node.blocked and not has_neighbor
                                        if self.FID == 0 or self.FID == 2:
                                            if next_node.danger_level > 0:
                                                is_valid = False
                                        if is_valid:
                                            valid_next.append((next_nid, next_x, next_y))
                                    has_neighbors = has_neighbors or has_neighbor
                                if len(valid_next) > 0:
                                    next_nid, next_x, next_y = random.choice(valid_next)
                                elif has_neighbors:
                                    # 位置不动情况1
                                    # 说明被堵住了,周围全是障碍物和其他无人机,暂时保持不动,等待其他无人机移走
                                    # 不需要改变view range
                                    next_nid = self.cur_NID
                                    next_x = self.cur_PX
                                    next_y = self.cur_PY
                                else:
                                    # 位置不动情况2
                                    # 说明被堵住了,周围全是障碍物
                                    # 不需要改变view range, 在环境不会变的情况下就任务结束不能动了
                                    # 在环境会变的情况下需要等待障碍物被移除
                                    next_nid = self.cur_NID
                                    next_x = self.cur_PX
                                    next_y = self.cur_PY
                                return next_nid, next_x, next_y
                    else:
                        if self.cur_rescue_tar[0] in list(self.Local_View_Map.Nodes.keys()):
                            min_cost, path = self.dijkstra(tid=1)
                        else:
                            min_cost, path = self.dijkstra(tid=1, extended=True, extended_nids=[self.cur_rescue_tar[0]],
                                                           extended_poses=[
                                                               (int(math.floor(self.cur_rescue_tar[0] / scale[1])),
                                                                int(self.cur_rescue_tar[0] % scale[1]))],
                                                           env_scale=scale)
                        min_len = min_cost[self.cur_rescue_tar[0]]
                        if min_len < self.STATIC_INFO.EDGE_INX:
                            tmp = self.cur_rescue_tar[0]
                            self.path_buffer.insert(0, tmp)
                            while tmp != self.cur_NID:
                                n_ = path[tmp]
                                if n_ != self.cur_NID:
                                    self.path_buffer.insert(0, n_)
                                tmp = n_
                            next_node = self.Local_View_Map.Nodes[self.path_buffer[0]]
                            next_x = next_node.pos_x
                            next_y = next_node.pos_y
                            next_nid = next_node.NID
                            return next_nid, next_x, next_y
                        else:
                            self.path_buffer.clear()
                            # 随机运动一下
                            # 有target且当前位置无法到达target
                            next_x = None
                            next_y = None
                            next_nid = None
                            valid_next.clear()
                            has_neighbors = False
                            for i in range(4):
                                has_neighbor = False
                                next_x = self.action_space[i][0] + self.cur_PX
                                next_y = self.action_space[i][1] + self.cur_PY
                                if 0 <= next_x < scale[0] and 0 <= next_y < scale[1]:
                                    next_nid = next_x * scale[1] + next_y
                                    next_node = self.Local_View_Map.Nodes[next_nid]
                                    if next_nid in list(self.Local_View_Map.Neighbors.keys()):
                                        has_neighbor = True
                                    is_valid = not next_node.blocked and not has_neighbor
                                    if self.FID == 0 or self.FID == 2:
                                        if next_node.danger_level > 0:
                                            is_valid = False
                                    if is_valid:
                                        valid_next.append((next_nid, next_x, next_y))
                                has_neighbors = has_neighbors or has_neighbor
                            if len(valid_next) > 0:
                                next_nid, next_x, next_y = random.choice(valid_next)
                            elif has_neighbors:
                                # 位置不动情况3,有目标但没办法到达目标地点,且被周围堵住了随机动都动不了
                                # 周围全是障碍物和其他无人机,暂时保持不动,等待其他无人机移走
                                # 不需要改变view range
                                next_nid = self.cur_NID
                                next_x = self.cur_PX
                                next_y = self.cur_PY
                            else:
                                # 位置不动情况4,有目标但没办法到达目标地点,且被周围堵住了随机动都动不了
                                # 周围全是障碍物
                                # 不需要改变view range, 在环境不会变的情况下就任务结束不能动了
                                # 在环境会变的情况下需要等待障碍物被移除
                                next_nid = self.cur_NID
                                next_x = self.cur_PX
                                next_y = self.cur_PY
                            return next_nid, next_x, next_y
                else:
                    if self.cur_rescue_tar is not None and len(self.cur_rescue_tar) > 0:
                        # 由于信息不断在变,所以有路有目标的时候要更新一遍路path_buffer
                        if self.cur_rescue_tar[0] in list(self.Local_View_Map.Nodes.keys()):
                            min_cost, path = self.dijkstra(tid=1)
                        else:
                            min_cost, path = self.dijkstra(tid=1, extended=True, extended_nids=[self.cur_rescue_tar[0]],
                                                           extended_poses=[
                                                               (int(math.floor(self.cur_rescue_tar[0] / scale[1])),
                                                                int(self.cur_rescue_tar[0] % scale[1]))],
                                                           env_scale=scale)
                        min_len = min_cost[self.cur_rescue_tar[0]]
                        if min_len < self.STATIC_INFO.EDGE_INX:
                            tmp = self.cur_rescue_tar[0]
                            self.path_buffer.insert(0, tmp)
                            while tmp != self.cur_NID:
                                n_ = path[tmp]
                                if n_ != self.cur_NID:
                                    self.path_buffer.insert(0, n_)
                                tmp = n_
                            next_node = self.Local_View_Map.Nodes[self.path_buffer[0]]
                            next_x = next_node.pos_x
                            next_y = next_node.pos_y
                            next_nid = next_node.NID
                            return next_nid, next_x, next_y
                        else:
                            self.path_buffer.clear()
                            # 更新信息后发现到达不了当前的目标了
                            # 清楚原路径后随机动一下
                            next_x = None
                            next_y = None
                            next_nid = None
                            valid_next.clear()
                            has_neighbors = False
                            for i in range(4):
                                has_neighbor = False
                                next_x = self.action_space[i][0] + self.cur_PX
                                next_y = self.action_space[i][1] + self.cur_PY
                                if 0 <= next_x < scale[0] and 0 <= next_y < scale[1]:
                                    next_nid = next_x * scale[1] + next_y
                                    next_node = self.Local_View_Map.Nodes[next_nid]
                                    if next_nid in list(self.Local_View_Map.Neighbors.keys()):
                                        has_neighbor = True
                                    is_valid = not next_node.blocked and not has_neighbor
                                    if self.FID == 0 or self.FID == 2:
                                        if next_node.danger_level > 0:
                                            is_valid = False
                                    if is_valid:
                                        valid_next.append((next_nid, next_x, next_y))
                                has_neighbors = has_neighbors or has_neighbor
                            if len(valid_next) > 0:
                                next_nid, next_x, next_y = random.choice(valid_next)
                            elif has_neighbors:
                                # 位置不动情况3,有目标但没办法到达目标地点,且被周围堵住了随机动都动不了
                                # 周围全是障碍物和其他无人机,暂时保持不动,等待其他无人机移走
                                # 不需要改变view range
                                next_nid = self.cur_NID
                                next_x = self.cur_PX
                                next_y = self.cur_PY
                            else:
                                # 位置不动情况4,有目标但没办法到达目标地点,且被周围堵住了随机动都动不了
                                # 周围全是障碍物
                                # 不需要改变view range, 在环境不会变的情况下就任务结束不能动了
                                # 在环境会变的情况下需要等待障碍物被移除
                                next_nid = self.cur_NID
                                next_x = self.cur_PX
                                next_y = self.cur_PY
                            return next_nid, next_x, next_y
                    else:
                        # 原本的路还没走完目标突然没了
                        self.path_buffer.clear()
                        # 清除原有路径后,随机移动一下
                        next_x = None
                        next_y = None
                        next_nid = None
                        valid_next.clear()
                        has_neighbors = False
                        for i in range(4):
                            has_neighbor = False
                            next_x = self.action_space[i][0] + self.cur_PX
                            next_y = self.action_space[i][1] + self.cur_PY
                            if 0 <= next_x < scale[0] and 0 <= next_y < scale[1]:
                                next_nid = next_x * scale[1] + next_y
                                next_node = self.Local_View_Map.Nodes[next_nid]
                                if next_nid in list(self.Local_View_Map.Neighbors.keys()):
                                    has_neighbor = True
                                is_valid = not next_node.blocked and not has_neighbor
                                if self.FID == 0 or self.FID == 2:
                                    if next_node.danger_level > 0:
                                        is_valid = False
                                if is_valid:
                                    valid_next.append((next_nid, next_x, next_y))
                            has_neighbors = has_neighbors or has_neighbor
                        if len(valid_next) > 0:
                            next_nid, next_x, next_y = random.choice(valid_next)
                        elif has_neighbors:
                            # 位置不动情况1,没有目标
                            # 周围全是障碍物和其他无人机,暂时保持不动,等待其他无人机移走
                            # 不需要改变view range
                            next_nid = self.cur_NID
                            next_x = self.cur_PX
                            next_y = self.cur_PY
                        else:
                            # 位置不动情况2,没有目标
                            # 周围全是障碍物
                            # 不需要改变view range, 在环境不会变的情况下就任务结束不能动了
                            # 在环境会变的情况下需要等待障碍物被移除
                            next_nid = self.cur_NID
                            next_x = self.cur_PX
                            next_y = self.cur_PY
                        return next_nid, next_x, next_y
            elif tid == 2:
                con_time = 0
                cur_time = 0
                if len(self.path_buffer) == 0:
                    if self.cur_delivery_tar is None or len(self.cur_delivery_tar) == 0:
                        has_next = False
                        valid_next = []
                        urgent_stats = []
                        for i in range(4):
                            has_neighbor = False
                            next_x = self.action_space[i][0] + self.cur_PX
                            next_y = self.action_space[i][1] + self.cur_PY
                            if 0 <= next_x < scale[0] and 0 <= next_y < scale[1]:
                                next_nid = next_x * scale[1] + next_y
                                next_node = self.Local_View_Map.Nodes[next_nid]
                                if next_nid in list(self.Local_View_Map.Neighbors.keys()):
                                    has_neighbor = True
                                is_valid = (not next_node.blocked and not next_node.visited) and \
                                           (not has_neighbor)
                                if next_node.is_charge_p:
                                    urgent_stats.append(next_node)
                                if self.FID == 0 or self.FID == 2:
                                    if next_node.danger_level > 0:
                                        is_valid = False

                                has_next = has_next or is_valid
                                if is_valid:
                                    valid_next.append((next_nid, next_x, next_y))

                        if has_next:
                            next_nid, next_x, next_y = random.choice(valid_next)
                            return next_nid, next_x, next_y
                        else:
                            if len(urgent_stats) > 0:
                                next_node = random.choice(urgent_stats)
                                next_nid = next_node.NID
                                next_x = next_node.pos_x
                                next_y = next_node.pos_y
                                return next_nid, next_x, next_y
                            else:
                                less_valid_next = []
                                danger_valid_next = []
                                for i in range(4):
                                    has_neighbor = False
                                    next_x = self.action_space[i][0] + self.cur_PX
                                    next_y = self.action_space[i][1] + self.cur_PY
                                    if 0 <= next_x < scale[0] and 0 <= next_y < scale[1]:
                                        next_nid = next_x * scale[1] + next_y
                                        next_node = self.Local_View_Map.Nodes[next_nid]
                                        if next_nid in list(self.Local_View_Map.Neighbors.keys()):
                                            has_neighbor = True
                                        is_valid = (next_node.is_charge_p or not next_node.blocked) and \
                                                   (not has_neighbor)
                                        if is_valid:
                                            danger_valid_next.append((next_nid, next_x, next_y))
                                        if self.FID == 0 or self.FID == 2:
                                            if next_node.danger_level > 0:
                                                is_valid = False
                                        if is_valid:
                                            less_valid_next.append((next_nid, next_x, next_y))
                                if len(less_valid_next) > 0:
                                    next_nid, next_x, next_y = random.choice(less_valid_next)
                                elif len(danger_valid_next) > 0:
                                    next_nid, next_x, next_y = random.choice(danger_valid_next)
                                else:
                                    next_nid = self.cur_NID
                                    next_x = self.cur_PX
                                    next_y = self.cur_PY
                                return next_nid, next_x, next_y
                    else:
                        # 请求center计算当前点到所有目标点的最短路径(用floyd算法,一段时间内只算一遍)
                        get_data = self.connect_with_center(Compute=True, Func='Dijkstra')
                        con_time = time.time()
                        # 获取最短路径及最短距离后,按距离从小到大排序,选择最近的作为当前目标点
                        # 延当前目标点对应的最短路径运动
                        min_costs = get_data[0]
                        path = get_data[1]
                        tar_dis = {}
                        for tar in self.cur_delivery_tar:
                            tar_dis[tar] = min_costs[tar]
                        sorted_tars = sorted(tar_dis.items(), key=lambda kv: kv[1])
                        self.cur_delivery_tar.clear()
                        for e in sorted_tars:
                            self.cur_delivery_tar.append(e[0])
                        min_len = sorted_tars[0][1]
                        if min_len < self.STATIC_INFO.EDGE_INX:
                            tmp = self.cur_delivery_tar[0]
                            self.path_buffer.insert(0, tmp)
                            while tmp != self.cur_NID:
                                n_ = path[tmp]
                                if n_ != self.cur_NID:
                                    self.path_buffer.insert(0, n_)
                                tmp = n_
                            next_node = self.Local_View_Map.Nodes[self.path_buffer[0]]
                            next_x = next_node.pos_x
                            next_y = next_node.pos_y
                            next_nid = next_node.NID
                            return next_nid, next_x, next_y
                else:
                    cur_time = time.time()
                    diff = cur_time - con_time
                    if diff >= self.experiment_config.FLOYD_INTERVAL:
                        get_data = self.connect_with_center(Compute=True, Func='Dijkstra')
                        con_time = time.time()
                        # 否则重新请求计算,重新排序,重新选择最短并延当前目标点对应的最短路径运动
                        min_costs = get_data[0]
                        path = get_data[1]
                        tar_dis = {}
                        for tar in self.cur_delivery_tar:
                            tar_dis[tar] = min_costs[tar]
                        sorted_tars = sorted(tar_dis.items(), key=lambda kv: kv[1])
                        self.cur_delivery_tar.clear()
                        for e in sorted_tars:
                            self.cur_delivery_tar.append(e[0])
                        min_len = sorted_tars[0][1]
                        if min_len < self.STATIC_INFO.EDGE_INX:
                            tmp = self.cur_delivery_tar[0]
                            self.path_buffer.insert(0, tmp)
                            while tmp != self.cur_NID:
                                n_ = path[tmp]
                                if n_ != self.cur_NID:
                                    self.path_buffer.insert(0, n_)
                                tmp = n_
                            next_node = self.Local_View_Map.Nodes[self.path_buffer[0]]
                            next_x = next_node.pos_x
                            next_y = next_node.pos_y
                            next_nid = next_node.NID
                            return next_nid, next_x, next_y
                    else:
                        # 如果距离上次请求center计算最短路径时间小于预设值则直接运动
                        next_node = self.Local_View_Map.Nodes[self.path_buffer[0]]
                        next_x = next_node.pos_x
                        next_y = next_node.pos_y
                        next_nid = next_node.NID
                        return next_nid, next_x, next_y

        return None, None, None

    def choose_charging_station(self):
        # TODO: realize min cost decision
        tar = ChargingPoint(0, 0, 0, 0)
        return tar

    def choose_rescue_target(self):
        # TODO: realize min cost decision
        tar = list(self.Local_View_Map.rescue_targets.keys())
        return tar

    def choose_delivery_target(self):
        tar = list(self.Local_View_Map.delivery_targets.keys())
        return tar

    def bob_find_new_start(self):
        tar = 0
        if len(self.path_buffer) > 0:
            cur_tar = self.path_buffer[len(self.path_buffer) - 1]
            # 需要判断当前是否有比cur_tar更好的目标,如果没有则不变,如果有则更新self.path_buffer
            tar = cur_tar
            min_len = len(self.path_buffer)
        else:
            min_cost, path = self.dijkstra(tid=0)
            min_cost.pop(self.cur_NID)
            tmp_min_cost = list(min_cost.keys())
            for key in tmp_min_cost:
                if self.Local_View_Map.Nodes[key].visited or self.Local_View_Map.Nodes[key].blocked:
                    min_cost.pop(key)
            sorted_cost = sorted(min_cost.items(), key=lambda item: item[1])
            # 按照value排序,默认从小到大,返回tuple list[(key,value),...]
            if len(sorted_cost) > 0:
                cur_tar = sorted_cost[0][0]
                min_len = sorted_cost[0][1]
                if min_len < self.STATIC_INFO.EDGE_INX:
                    tmp = cur_tar
                    self.path_buffer.insert(0, tmp)
                    while tmp != self.cur_NID:
                        n_ = path[tmp]
                        if n_ != self.cur_NID:
                            self.path_buffer.insert(0, n_)
                        tmp = n_
                    tar = cur_tar
                else:
                    return None, self.STATIC_INFO.EDGE_INX
            else:
                return None, self.STATIC_INFO.EDGE_INX
        return tar, min_len

    def dijkstra(self, tid=1, extended=False, extended_nids=[], extended_poses=[], env_scale=None):
        visited = {self.cur_NID: 0}  # 包含所有已添加的点,并且key-value对表示key对应的点到initial点(即self.cur_NID)的最小距离
        h = [(0, self.cur_NID)]
        path = {}  # path[v]=a,代表到达v之前的一个点是a,需要回溯得到整个路径

        if extended:
            Nodes = copy.deepcopy(self.Local_View_Map.Nodes)
            Edges = copy.deepcopy(self.Local_View_Map.Edges)
            borders = []
            for key, nd in self.Local_View_Map.Nodes.items():
                nei_key = [key - 1, key + 1, key - env_scale[1], key + env_scale[1]]
                for j in range(len(nei_key)):
                    if nei_key[j] not in list(self.Local_View_Map.Nodes.keys()):
                        borders.append((key, nd.pos_x, nd.pos_y))
                        break
            for i in range(len(extended_nids)):
                nid = extended_nids[i]
                x = extended_poses[i][0]
                y = extended_poses[i][1]
                Nodes[extended_nids[i]] = Point(nid=nid, pos_x=x, pos_y=y)
                for (bn, px, py) in borders:
                    Edges[(bn, nid)] = Edge(eid=-1, from_p=bn, to_p=nid, distance=abs(px - x) + abs(py - y))
                    Edges[(nid, bn)] = Edge(eid=-1, from_p=bn, to_p=nid, distance=abs(px - x) + abs(py - y))
        else:
            Nodes = self.Local_View_Map.Nodes
            Edges = self.Local_View_Map.Edges

        if tid != 1:
            # danger district也是尽量不可经过的,除非完全堵住了才可以冒险,距离设置为width*height
            # danger <-> safe width*height
            # danger <-> danger width*height
            # danger <-> block INF
            for key, edge in Edges.items():
                if (Nodes[edge.from_p].danger_level == 1 and not Nodes[edge.to_p].blocked) \
                        or (Nodes[edge.to_p].danger_level == 1 and not Nodes[edge.from_p].blocked):
                    edge.distance = env_scale[0] * env_scale[1]

        nodes_index = set(set(range(len(Nodes))))

        while nodes_index and h:
            current_weight, min_node = heapq.heappop(h)
            try:
                while min_node not in nodes_index:
                    current_weight, min_node = heapq.heappop(h)
            except IndexError:
                break
            nodes_index.remove(min_node)

            for key, edge in Edges.items():
                if edge.from_p == min_node:
                    weight = current_weight + edge.distance
                    if edge.to_p not in visited or weight < visited[edge.to_p]:
                        visited[edge.to_p] = weight
                        heapq.heappush(h, (weight, edge.to_p))
                        path[edge.to_p] = min_node
                else:
                    continue
        return visited, path

    def move(self, next_nid, next_x, next_y):
        if len(self.path_buffer) > 0:
            self.path_buffer.pop(0)
        self.cur_PLen += self.Local_View_Map.Edges[(self.cur_NID, next_nid)].distance
        self.cur_E -= self.Local_View_Map.Edges[(self.cur_NID, next_nid)].travel_time
        self.cur_NID = next_nid
        self.cur_PX = next_x
        self.cur_PY = next_y
        # print(next_nid)
        if self.Local_View_Map.Nodes[next_nid].visited:
            self.hybrid_rd += 1
        # self.cur_RCost = self.cur_RCost + random.randint(0, 2 - self.cur_RCost)
        # 损坏状态随机变换,也可以假设始终保持不变
        sense_time = time.time()

        # self.VR = self.VR  # 根据具体情况有可能可以改变, 但一般认为应该在make_move_decision的时候改, 改完了重新回到IW状态下的0状态
        return sense_time

    def bob_move(self, next_nid, next_x, next_y):
        if len(self.path_buffer) > 0:
            self.path_buffer.pop(0)
        with map_lock[self.UID]:
            self.cur_PLen += global_map[self.UID].Edges[str(self.cur_NID) + '_' + str(next_nid)].distance
            self.cur_E -= global_map[self.UID].Edges[str(self.cur_NID) + '_' + str(next_nid)].travel_time
        self.cur_NID = next_nid
        self.cur_PX = next_x
        self.cur_PY = next_y
        # print(next_nid)
        # if global_map[self.UID].Nodes[next_nid].visited:
        #     self.broadcast_rd += 1
        if g_visited[next_nid]:
            self.broadcast_rd += 1
        sense_time = time.time()
        return sense_time

    def is_work_done(self, tid):
        ct = 0
        if tid == 0:
            while ct < 3:
                try:
                    get_data = self.connect_with_center(RoW='R', GoL='G',
                                                        SQLs=[
                                                            'SELECT end_time FROM public.search_coverage_task '
                                                            'WHERE start_time IS NOT NULL '
                                                            'AND responsible_fleet_id = {} '.format(
                                                                self.FID)])
                    if len(get_data[0][1]) > 0:  # 有任务
                        end_time = get_data[0][1][0][0]
                        if end_time is not None:
                            return True
                        else:
                            return False
                    else:
                        return True
                except Exception as e:
                    print(e)
                    ct += 1
        elif tid == 1:
            while ct < 3:
                try:
                    get_data = self.connect_with_center(RoW='R', GoL='G',
                                                        SQLs=['SELECT end_time FROM public.rescue_support_task '
                                                              'WHERE start_time IS NOT NULL '
                                                              'AND responsible_fleet_id = {} '.format(self.FID)])
                    if len(get_data[0][1]) > 0:
                        end_time = get_data[0][1][0][0]
                        if end_time is not None:
                            return True
                        else:
                            return False
                    else:
                        return True
                except Exception as e:
                    print(e)
                    ct += 1
        elif tid == 2:
            while ct < 3:
                try:
                    get_data = self.connect_with_center(RoW='R', GoL='G',
                                                        SQLs=['SELECT end_time FROM public.delivery_task '
                                                              'WHERE start_time IS NOT NULL '
                                                              'AND responsible_fleet_id = {} '.format(self.FID)])
                    if len(get_data[0][1]) > 0:
                        end_time = get_data[0][1][0][0]
                        if end_time is not None:
                            return True
                        else:
                            return False
                    else:
                        return True
                except Exception as e:
                    print(e)
                    ct += 1


class Cgrid(tk.Tk, object):

    def __init__(self, env, agents_info, agents_view):
        super(Cgrid, self).__init__()
        self.staticInfo = StaticInfo()
        self.exp_Info = ExperimentConfig()
        self.action_space = [(0, 1, 1), (0, -1, 1), (-1, 0, 1), (1, 0, 1), (0, 0, 1), (0, 0, 0)]
        self.n_actions = len(self.action_space)
        self.title('Concrete Environment')
        self.env = env
        self.map_w = env.width
        self.map_h = env.height
        self.agents_loc = agents_info[0]
        self.agents_e = agents_info[1]
        self.agents_f = agents_info[2]
        self.agents_view = agents_view
        self.geometry('{0}x{1}'.format(self.map_w * self.staticInfo.UNIT, self.map_h * self.staticInfo.UNIT))
        self._build_cgrid()

    def _build_cgrid(self):
        self.canvas = tk.Canvas(self, bg='white',
                                height=self.map_h * self.staticInfo.UNIT,
                                width=self.map_w * self.staticInfo.UNIT)
        # create grids
        # for c in range(0, self.map_w * self.staticInfo.UNIT, self.staticInfo.UNIT):
        #     x0, y0, x1, y1 = c, 0, c, self.map_h * self.staticInfo.UNIT
        #     self.canvas.create_line(x0, y0, x1, y1)
        # for r in range(0, self.map_h * self.staticInfo.UNIT, self.staticInfo.UNIT):
        #     x0, y0, x1, y1 = 0, r, self.map_w * self.staticInfo.UNIT, r
        #     self.canvas.create_line(x0, y0, x1, y1)

        self.grid_block = []
        self.grid_mark = []
        for x in range(0, self.map_w * self.staticInfo.UNIT, self.staticInfo.UNIT):
            self.grid_block.append([])
            self.grid_mark.append([])
            for y in range(self.map_h * self.staticInfo.UNIT, 0, -self.staticInfo.UNIT):
                i = len(self.grid_block) - 1
                j = len(self.grid_block[i])
                if self.env.Nodes[i][j].danger_level == 1:
                    colorval = "#%02x%02x%02x" % (255, 215, 0)
                else:
                    colorval = "#%02x%02x%02x" % (34, 139, 34)
                block = self.canvas.create_rectangle((x, y, x + self.staticInfo.UNIT, y - self.staticInfo.UNIT),
                                                     fill=colorval, outline='gray', disabledfill='gray')
                self.grid_block[len(self.grid_block) - 1].append(block)
                mark = self.canvas.create_oval((x + self.staticInfo.UNIT / 2 - self.staticInfo.UNIT / 32,
                                                y - self.staticInfo.UNIT / 2 - self.staticInfo.UNIT / 32,
                                                x + self.staticInfo.UNIT / 2 + self.staticInfo.UNIT / 32,
                                                y - self.staticInfo.UNIT / 2 + self.staticInfo.UNIT / 32),
                                               fill=colorval, outline=colorval, disabledfill='gray',
                                               disabledoutline='gray')
                self.grid_mark[len(self.grid_mark) - 1].append(mark)

        # create origin(原点)
        origin = np.array([self.staticInfo.UNIT / 2, self.staticInfo.UNIT * self.map_h - self.staticInfo.UNIT / 2])

        # create ordinary nodes, obstacle and charging station in env
        self.stats = []
        self.obs = []
        self.vbs = []
        for i in range(self.map_w):
            for j in range(self.map_h):
                if isinstance(self.env.Nodes[i][j], ChargingPoint):
                    # charging station
                    stat_center = origin + np.array([self.staticInfo.UNIT * i, self.staticInfo.UNIT * (-j)])
                    p1 = stat_center + np.array([0, -self.staticInfo.UNIT / 4])
                    p2 = stat_center + np.array([-self.staticInfo.UNIT / 4, self.staticInfo.UNIT / 4])
                    p3 = stat_center + np.array([self.staticInfo.UNIT / 4, self.staticInfo.UNIT / 4])
                    stat = self.canvas.create_polygon(
                        (p1[0], p1[1], p2[0], p2[1], p3[0], p3[1]),
                        fill='black', disabledfill='gray')
                    self.stats.append({'pos': (i, j), 'stat': stat})
                elif self.env.Nodes[i][j].blocked:
                    # obstacle
                    ob_center = origin + np.array([self.staticInfo.UNIT * i, self.staticInfo.UNIT * (-j)])
                    # p1 = ob_center + np.array([self.staticInfo.UNIT / 2, self.staticInfo.UNIT / 2])
                    # p2 = ob_center + np.array([self.staticInfo.UNIT / 2, -self.staticInfo.UNIT / 2])
                    # p3 = ob_center + np.array([-self.staticInfo.UNIT / 2, self.staticInfo.UNIT / 2])
                    # p4 = ob_center + np.array([-self.staticInfo.UNIT / 2, -self.staticInfo.UNIT / 2])
                    self.canvas.itemconfig(self.grid_block[i][j], fill='black')
                    self.canvas.itemconfig(self.grid_mark[i][j], fill='black', outline='black')
                    # line1 = self.canvas.create_line((p1[0], p1[1], p4[0], p4[1]), fill='red', disabledfill='black')
                    # line2 = self.canvas.create_line((p2[0], p2[1], p3[0], p3[1]), fill='red', disabledfill='black')
                    # self.obs.append({'pos': (i, j), 'l1': line1, 'l2': line2})
                else:
                    # ordinary safe/dangerous node
                    n_center = origin + np.array([self.staticInfo.UNIT * i, self.staticInfo.UNIT * (-j)])
                    p1 = n_center + np.array([-self.staticInfo.UNIT / 2, self.staticInfo.UNIT / 2])
                    p2 = n_center + np.array([-self.staticInfo.UNIT / 4, self.staticInfo.UNIT / 4])
                    if self.env.Nodes[i][j].need_rescue or self.env.Nodes[i][j].victims_num > self.exp_Info.S_max:
                        fill = 'red'
                    else:
                        fill = 'black'
                    block = self.canvas.create_rectangle((p1[0], p1[1], p2[0], p2[1]), fill='white',
                                                         disabledfill='gray', disabledoutline='gray')
                    text = self.canvas.create_text((p1[0] + self.staticInfo.UNIT / 8, p1[1] - self.staticInfo.UNIT / 8),
                                                   text='{}'.format(self.env.Nodes[i][j].victims_num),
                                                   fill=fill, disabledfill='gray')
                    self.vbs.append({'pos': (i, j), 'block': block, 'num': text})

        self.agents = []

        # create agents
        for i in range(len(self.agents_loc)):
            agent_center = origin + np.array([self.staticInfo.UNIT * self.agents_loc[i][0],
                                              -self.staticInfo.UNIT * self.agents_loc[i][1]])
            if self.agents_f[i] == 0:
                fill = 'white'
            elif self.agents_f[i] == 1:
                fill = 'blue'
            else:
                fill = 'purple'
            agent = self.canvas.create_oval(
                (agent_center[0] - self.staticInfo.UNIT / 4, agent_center[1] - self.staticInfo.UNIT / 4,
                 agent_center[0] + self.staticInfo.UNIT / 4, agent_center[1] + self.staticInfo.UNIT / 4),
                fill=fill
            )

            fill = ''
            if self.agents_e[i] == 0:
                fill = 'green'
            elif self.agents_e[i] == 1:
                fill = 'yellow'
            else:
                fill = 'red'
            light = self.canvas.create_rectangle(
                (agent_center[0] - self.staticInfo.UNIT / 8, agent_center[1] + self.staticInfo.UNIT / 8,
                 agent_center[0] + self.staticInfo.UNIT / 8, agent_center[1] - self.staticInfo.UNIT / 8),
                fill=fill
            )
            self.agents.append({'circle': agent, 'light': light})

        # disable env components out of view range

        for i in range(self.map_w):
            for j in range(self.map_h):
                for a in range(len(self.agents)):
                    if math.pow(self.agents_loc[a][0] - i, 2) + math.pow(self.agents_loc[a][1] - j, 2) <= math.pow(
                            self.agents_view[a], 2):
                        self.canvas.itemconfig(self.grid_block[i][j], state='normal')
                        self.canvas.itemconfig(self.grid_mark[i][j], state='normal')
                        break
                    else:
                        self.canvas.itemconfig(self.grid_block[i][j], state='disabled')
                        self.canvas.itemconfig(self.grid_mark[i][j], state='disabled')

        for each in self.vbs:
            re = self.canvas.itemcget(self.grid_block[each['pos'][0]][each['pos'][1]], 'state')
            if re == 'disabled':
                self.canvas.itemconfig(each['block'], state='disabled')
                self.canvas.itemconfig(each['num'], state='disabled')
        for each in self.stats:
            re = self.canvas.itemcget(self.grid_block[each['pos'][0]][each['pos'][1]], 'state')
            if re == 'disabled':
                self.canvas.itemconfig(each['stat'], state='disabled')
        # for each in self.obs:
        #     re = self.canvas.itemcget(self.grid_block[each['pos'][0]][each['pos'][1]], 'state')
        #     if re == 'disabled':
        #         self.canvas.itemconfig(each['l1'], state='disabled')
        #         self.canvas.itemconfig(each['l2'], state='disabled')

        # pack all
        self.canvas.pack()

    def step(self, new_env, new_locs, new_e, new_sr):
        s = []
        s_ = []
        for i, ag in enumerate(self.agents):
            x0, y0, x1, y1 = self.canvas.bbox(ag['circle'])
            coor = [(x0 + x1) / 2, (y0 + y1) / 2]
            s.append([math.floor(int(coor[0]) / int(self.staticInfo.UNIT)),
                      math.floor((self.map_h * self.staticInfo.UNIT - int(coor[1])) / self.staticInfo.UNIT)])
            self.canvas.itemconfig(self.grid_mark[s[i][0]][s[i][1]], state='normal', fill='red')
            base_action = np.array([(new_locs[i][0] - s[i][0]) * self.staticInfo.UNIT,
                                    -(new_locs[i][1] - s[i][1]) * self.staticInfo.UNIT])
            self.canvas.move(ag['circle'], base_action[0], base_action[1])  # move agent circle
            self.canvas.move(ag['light'], base_action[0], base_action[1])
            if new_e[i] == 0:
                fill = 'green'
            elif new_e[i] == 1:
                fill = 'yellow'
            else:
                fill = 'red'
            self.canvas.itemconfig(ag['light'], fill=fill)
            for r in range(int(max(0, new_locs[i][0] - new_sr[i])),
                           int(min(self.map_w, new_locs[i][0] + new_sr[i] + 1))):
                for c in range(int(max(0, new_locs[i][1] - new_sr[i])),
                               int(min(self.map_h, new_locs[i][1] + new_sr[i] + 1))):
                    if math.pow(r - new_locs[i][0], 2) + math.pow(c - new_locs[i][1], 2) <= new_sr[i] * new_sr[i]:
                        if self.canvas.itemcget(self.grid_block[r][c], 'state') == 'disabled':
                            self.canvas.itemconfig(self.grid_block[r][c], state='normal')
                            self.canvas.itemconfig(self.grid_mark[r][c], state='normal')

            for each in self.vbs:
                re = self.canvas.itemcget(self.grid_block[each['pos'][0]][each['pos'][1]], 'state')

                if re == 'normal':
                    self.canvas.itemconfig(each['block'], state='normal')
                    self.canvas.itemconfig(each['num'], state='normal')

            for each in self.stats:
                re = self.canvas.itemcget(self.grid_block[each['pos'][0]][each['pos'][1]], 'state')
                if re == 'normal':
                    self.canvas.itemconfig(each['stat'], state='normal')
            # for each in self.obs:
            #     re = self.canvas.itemcget(self.grid_block[each['pos'][0]][each['pos'][1]], 'state')
            #     if re == 'normal':
            #         self.canvas.itemconfig(each['l1'], state='normal')
            #         self.canvas.itemconfig(each['l2'], state='normal')
            s_.append([new_locs[i][0], new_locs[i][1]])

        for each in self.vbs:
            re = new_env.Nodes[each['pos'][0]][each['pos'][1]]
            if re.need_rescue or re.victims_num > self.exp_Info.S_max:
                fill = 'red'
            else:
                fill = 'black'
            self.canvas.itemconfig(each['num'], fill=fill)
        return s_

    def reset(self):
        self.update()
        time.sleep(0.5)
        for dict in self.agents:
            for key, value in dict.items():
                self.canvas.delete(value)
        origin = np.array([self.staticInfo.UNIT / 2, self.staticInfo.UNIT / 2])
        # re-create agents
        for i in range(len(self.agents_loc)):
            agent_center = origin + np.array([self.staticInfo.UNIT * self.agents_loc[i][0],
                                              self.staticInfo.UNIT * self.agents_loc[i][1]])
            agent = self.canvas.create_oval(
                (agent_center[0] - self.staticInfo.UNIT / 4, agent_center[1] + self.staticInfo.UNIT / 4,
                 agent_center[0] + self.staticInfo.UNIT / 4, agent_center[1] - self.staticInfo.UNIT / 4),
                fill='gray'
            )

            fill = ''
            if self.agents_e[i] == 0:
                fill = 'green'
            elif self.agents_e[i] == 1:
                fill = 'yellow'
            else:
                fill = 'red'
            light = self.canvas.create_rectangle(
                (agent_center[0] - self.staticInfo.UNIT / 8, agent_center[1] - self.staticInfo.UNIT / 8,
                 agent_center[0] + self.staticInfo.UNIT / 8, agent_center[1] + self.staticInfo.UNIT / 8),
                fill=fill
            )
            self.agents.append({'circle': agent, 'light': light})

        for i in self.map_w:
            for j in self.map_h:
                for a in range(len(self.agents)):
                    if math.pow(self.agents_loc[a][0] - i, 2) + math.pow(self.agents_loc[a][1] - j, 2) <= \
                            self.agents_view[a]:
                        self.canvas.itemconfig(self.grid_block[i][j], state='normal')
                        break
                    else:
                        self.canvas.itemconfig(self.grid_block[i][j], state='disabled')

        for each in self.vbs:
            re = self.canvas.itemcget(self.grid_block[each['pos'][0]][each['pos'][1]], 'state')

            if re == 'disabled':
                self.canvas.itemconfig(each['block'], state='disabled')
                self.canvas.itemconfig(each['num'], state='disabled')
            else:
                self.canvas.itemconfig(each['block'], state='normal')
                self.canvas.itemconfig(each['text'], state='normal')
        for each in self.stats:
            re = self.canvas.itemcget(self.grid_block[each['pos'][0]][each['pos'][1]], 'state')
            if re == 'disabled':
                self.canvas.itemconfig(each['stat'], state='disabled')
            else:
                self.canvas.itemconfig(each['stat'], state='normal')
        for each in self.obs:
            re = self.canvas.itemcget(self.grid_block[each['pos'][0]][each['pos'][1]], 'state')
            if re == 'disabled':
                self.canvas.itemconfig(each['l1'], state='disabled')
                self.canvas.itemconfig(each['l2'], state='disabled')
            else:
                self.canvas.itemconfig(each['l1'], state='normal')
                self.canvas.itemconfig(each['l2'], state='normal')

        # return observation
        agent_info = (self.agents_loc, self.agents_e)
        return agent_info


# def update(new_locs,new_e,new_sr):
# #     while True:
# #         if new_locs is None:
# #             break
# #         env.render(new_locs,new_e,new_sr)
# #         s_ = env.step(new_locs,new_e,new_sr)

# if __name__ == '__main__':
#
#     metadata = '../data/metadata.json'
#     if metadata and os.path.isfile(metadata):
#         with open(file=metadata, mode='r') as fr:
#             metadata = json.loads("".join(fr.readlines()))['metadata']
#             agent_g_num = metadata['agent_num']
#             charge_pos_list = metadata['charge_pos_list']
#             uav_count = 0
#             drone_locs = []
#             for j in range(len(agent_g_num)):
#                 drone_locs.append({})
#                 fleet_id = j
#                 for i in range(agent_g_num[j]):
#                     uav_id = uav_count
#                     uav_count += 1
#                     if j != 2:
#                         loc_node_id = random.randint(0, metadata['width'] * metadata['height'])
#                     else:
#                         loc_node_id = random.choice(charge_pos_list)
#                     drone_locs[j][uav_id] = loc_node_id
#             drone_num = uav_count
#     else:
#         charge_list = []
#         agent_g_num = [4]
#         drone_locs = []
#         uav_count = 0
#         width = 10
#         height = 10
#         for j in range(len(agent_g_num)):
#             drone_locs.append({})
#             fleet_id = j
#             for i in range(agent_g_num[j]):
#                 uav_id = uav_count
#                 uav_count += 1
#                 if j != 2:
#                     loc_node_id = random.randint(0, width * height)
#                 else:
#                     loc_node_id = random.choice(charge_list)
#                 drone_locs[j][uav_id] = loc_node_id
#         drone_num = uav_count
#
#     fleet = []
#     fleet_thread = []
#     env = ConcreteEnv(charge_list=[], drone_locs=drone_locs)
#
#     global_map = []
#     for i in range(drone_num):
#         global_map.append(GlobalViewMap(scale=(env.width, env.height)))
#
#     agents_path = []
#     next_pos = []
#     agents_pos = []
#     for i in range(drone_num):
#         agents_path.append(dict({}))
#         next_pos.append(dict({}))
#         agents_pos.append(dict({}))
#         for j in range(drone_num):
#             agents_path[i][j] = []
#             next_pos[i][j] = -1
#
#     # global_map = GlobalViewMap(scale=(env.width, env.height))
#     # agents_path = dict({})
#     # next_pos = dict({})
#     # for i in range(drone_num):
#     #     agents_path[i] = []
#     #     next_pos[i] = -1
#     # agents_pos = dict({})
#
#     # pos_lock = Lock()
#     # map_lock = Lock()
#     # paths_lock = Lock()
#     # next_lock = Lock()
#
#     map_lock = []
#     paths_lock = []
#     next_lock = []
#     pos_lock = []
#     for i in range(drone_num):
#         map_lock.append(Lock())
#         paths_lock.append(Lock())
#         next_lock.append(Lock())
#         pos_lock.append(Lock())
#
#     for i in range(drone_num):
#         fleet.append(
#             UAV(ID=i, X=int(drone_locs[0][i] / env.height), Y=int(drone_locs[0][i] % env.height),
#                 NID=drone_locs[0][i]))
#         print(i)
#         print(int(drone_locs[0][i] / env.height))
#         print(int(drone_locs[0][i] % env.height))
#         print(int(drone_locs[0][i]))
#         drone_con_thread = Thread(target=fleet[i].broadcast_run_search, args=(env,))
#         # drone_con_thread = Thread(target=fleet[i].test)
#         fleet_thread.append(drone_con_thread)
#         drone_con_thread.start()
#
#     # drawing the concrete env and all drones current state and their local_view
#     start_time = time.time()
#     cur_pos = []
#     cur_e = []
#     cur_sr = []
#     cur_f = []
#     for i in range(drone_num):
#         cur_pos.append([fleet[i].cur_PX, fleet[i].cur_PY])
#         cur_f.append(fleet[i].FID)
#         if fleet[i].cur_E >= fleet[i].E * (1 - fleet[i].experiment_config.W_Threshold):
#             new_e = 0
#         elif fleet[i].E * (1 - fleet[i].experiment_config.C_Threshold) <= fleet[i].cur_E < fleet[i].E * (
#                 1 - fleet[i].experiment_config.W_Threshold):
#             new_e = 1
#         else:
#             new_e = 2
#         cur_e.append(new_e)
#         cur_sr.append(fleet[i].SR)
#     env_window = Cgrid(env=env, agents_info=(cur_pos, cur_e, cur_f), agents_view=cur_sr)
#     # env_window.mainloop()
#
#     while True:
#         cur_pos = []
#         cur_e = []
#         cur_sr = []
#         for i in range(drone_num):
#             cur_pos.append([fleet[i].cur_PX, fleet[i].cur_PY])
#             new_e = -1
#             if fleet[i].cur_E >= fleet[i].E * (1 - fleet[i].experiment_config.W_Threshold):
#                 new_e = 0
#             elif fleet[i].E * (1 - fleet[i].experiment_config.C_Threshold) <= fleet[i].cur_E < fleet[i].E * (
#                     1 - fleet[i].experiment_config.W_Threshold):
#                 new_e = 1
#             else:
#                 new_e = 2
#             cur_e.append(new_e)
#             cur_sr.append(fleet[i].SR)
#         s_ = env_window.step(env, cur_pos, cur_e, cur_sr)
#         env_window.update_idletasks()
#         env_window.update()
#         time.sleep(0.1)
#         time_elapse = time.time() - start_time
#         if time_elapse > fleet[0].experiment_config.timeout:
#             break
#
#     fw = open('../log/broadcast_drone_statistic.txt', mode='w')
#     with fw:
#         for i in range(drone_num):
#             fw.write("drone {} end work with path length {}.\n".format(i, fleet[i].cur_PLen))
#
#     for i in range(drone_num):
#         fleet[i].terminate()
#         fleet_thread[i].join()
#
#     print("Drones' activities end!")


def get_size(obj, seen=None):
    """Recursively finds size of objects"""
    try:
        size = sys.getsizeof(obj)
        if seen is None:
            seen = set()
        obj_id = id(obj)
        if obj_id in seen:
            return 0
        # Important mark as seen *before* entering recursion to gracefully handle
        # self-referential objects
        seen.add(obj_id)
        if isinstance(obj, dict):
            size += sum([get_size(v, seen) for v in list(obj.values())])
            size += sum([get_size(k, seen) for k in list(obj.keys())])
        elif hasattr(obj, '__dict__'):
            size += get_size(obj.__dict__, seen)
        elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
            size += sum([get_size(i, seen) for i in obj])
        return size
    except Exception as e:
        print(e)
        return 0


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", dest="width", action="store", type=int, default=10)
    parser.add_argument("--height", dest="height", action="store", type=int, default=10)
    parser.add_argument("--charge_num", dest="charge_num", action="store", type=int, default=0)
    parser.add_argument("--obstacle_num", dest="obstacle_num", action="store", type=int, default=10)
    parser.add_argument("--danger_num", dest="danger_num", action="store", type=int, default=0)
    parser.add_argument("--agent_num", dest="agent_num", action="store", type=str, default='[4,0,0]')
    parser.add_argument("--charge_pos_list", dest='charge_pos_list', action="store", type=str, default='[]')
    parser.add_argument("--env_change_prob", dest='env_change_prob', action="store", type=str, default='[0.2,0.2,0.2]')
    parser.add_argument("--stat_change_prob", dest='stat_change_prob', action="store", type=str,
                        default='[0.1,0.1,0.1]')
    parser.add_argument("--view_range", dest='view_range', action="store", type=float, default=4.0)
    parser.add_argument("--sense_range", dest='sense_range', action="store", type=float, default=2.0)
    parser.add_argument("--time_tag", dest='time_tag', action="store", type=str,
                        default=time.strftime("%m%d%H%M", time.localtime()))
    parser.add_argument("--max_memory", dest='max_memory', action="store", type=float, default=5.0)

    args = parser.parse_args()
    return args


if __name__ == '__main__':

    # Get Drones Distriution from center
    qtool = QueryTool(database='multiAgents')
    col_nms_1, rows_1 = qtool.get_view(view_name='drones_cur_state')
    col_nms_2, rows_2 = qtool.get_view(view_name='charging_stations_config')
    col_nms_3, rows_3 = qtool.sql_execute(query="SELECT * FROM public.drones_cur_state,public.drones_config "
                                                "WHERE drones_config.uav_id = drones_cur_state.uav_id "
                                                "AND drones_config.fleet_id = 0")
    col_nms_4, rows_4 = qtool.sql_execute(query="SELECT * FROM public.drones_cur_state,public.drones_config "
                                                "WHERE drones_config.uav_id = drones_cur_state.uav_id "
                                                "AND drones_config.fleet_id = 1")
    col_nms_5, rows_5 = qtool.sql_execute(query="SELECT * FROM public.drones_cur_state,public.drones_config "
                                                "WHERE drones_config.uav_id = drones_cur_state.uav_id "
                                                "AND drones_config.fleet_id = 2")
    qtool.clear_db_connection()
    del qtool

    drone_num = len(rows_1)
    drone_locs = [{}, {}, {}]
    for row in rows_3:
        drone_locs[0][row[col_nms_3.index('uav_id')]] = row[col_nms_3.index('loc_node_id')]
    for row in rows_4:
        drone_locs[1][row[col_nms_4.index('uav_id')]] = row[col_nms_4.index('loc_node_id')]
    for row in rows_5:
        drone_locs[2][row[col_nms_5.index('uav_id')]] = row[col_nms_5.index('loc_node_id')]
    charge_list = []
    for row in rows_2:
        charge_list.append(row[col_nms_2.index('node_id')])

    # Initializing by arguments
    args = get_args()
    metadata = copy.deepcopy(args.__dict__)
    metadata['agent_num'] = json.loads(metadata['agent_num'])
    metadata['charge_pos_list'] = json.loads(metadata['charge_pos_list'])
    metadata['env_change_prob'] = json.loads(metadata['env_change_prob'])
    metadata['stat_change_prob'] = json.loads(metadata['stat_change_prob'])
    metadata['node_num'] = metadata['height'] * metadata['width']
    metadata['edge_num'] = (metadata['width'] - 1) * metadata['height'] * 2 + (metadata['height'] - 1) * metadata[
        'width'] * 2
    time_str = metadata["time_tag"]
    dir_name = str(metadata['width']) + '_' + str(metadata['height']) + '_' + str(
        drone_num) + '_' + time_str + '_' + str(metadata['view_range']) + '_' + str(metadata['max_memory'])
    root = os.path.abspath(os.path.dirname(os.getcwd()) + os.path.sep + ".")
    log_dir = os.path.join(os.path.join(root, 'log'), dir_name)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Initializing concrete environment
    env = ConcreteEnv(charge_list=[], drone_locs=drone_locs, metadata=metadata)

    yappi.clear_stats()
    yappi.set_clock_type("wall")
    yappi.start()
    # Shared parameters for monitoring memory usage
    x = []
    y = [[] for i in range(drone_num)]
    is_monitoring = True

    # Declare fleet and fleet thread
    fleet = []
    # f_ids = []
    fleet_thread = []
    exper_config = ExperimentConfig()
    exper_config.MAX_MEMORY = metadata['max_memory']


    # Define memory monitoring method
    def monitor_memory(mode, check_num):
        s = time.time()
        while is_monitoring:
            t = time.time() - s
            if mode == 0:
                # cloud-supported
                if len(fleet) == check_num:
                    x.append(t)
                    # print(" at time t:", t)
                    for i in range(len(fleet)):
                        local_memory = get_size(fleet[i].Local_View_Map.Nodes)
                        # print("Nodes memory:", local_memory)
                        local_memory += get_size(fleet[i].Local_View_Map.Edges)
                        # print("Edges memory:", get_size(fleet[i].Local_View_Map.Edges))
                        local_memory += get_size(fleet[i].Local_View_Map.Neighbors)
                        # print("Neighbors memory:", get_size(fleet[i].Local_View_Map.Neighbors))
                        local_memory += get_size(fleet[i].path_buffer)
                        # print("path buffer memory:", get_size(fleet[i].path_buffer))
                        y[i].append(local_memory)
            elif mode == 1:
                # broadcast
                if len(fleet) == check_num:
                    x.append(t)
                    # print(" at time t:", t)
                    for i in range(len(fleet)):
                        local_memory = get_size(global_map[i].Nodes)
                        # print("Nodes memory:", local_memory)
                        local_memory += get_size(global_map[i].Edges)
                        # print("Edges memory:", get_size(global_map[i].Edges))
                        local_memory += get_size(global_map[i].Neighbors)
                        # print("Neighbors memory:", get_size(global_map[i].Neighbors))
                        local_memory += get_size(agents_path[i])
                        # print("path memory:", get_size(agents_path[i]))
                        local_memory += get_size(agents_pos[i])
                        # print("agent pos memory:", get_size(agents_pos[i]))
                        y[i].append(local_memory)
            time.sleep(1)


    # Start the cloud-supported fleet threads
    for i in range(drone_num):
        fleet.append(UAV(ID=i, experiment_config=exper_config))
        drone_con_thread = Thread(target=fleet[i].run, args=(env,))
        # drone_con_thread = Thread(target=fleet[i].test)
        fleet_thread.append(drone_con_thread)
        drone_con_thread.start()
        # f_ids.append(drone_con_thread.ident)
    # Start memory monitoring threads
    monitor_thread = Thread(target=monitor_memory, args=(0, drone_num))
    monitor_thread.start()
    # Waiting for drone threads end
    # Record code total cpu time (max?)
    start_clock = time.clock()
    start_time = time.time()
    for i in range(drone_num):
        fleet_thread[i].join()
    end_clock = time.clock()
    end_time = time.time()
    print("Center-Drones' activities end!\n")
    # print("Thread ids: ", f_ids)
    # End monitoring thread
    is_monitoring = False
    monitor_thread.join()
    del monitor_thread

    func_stats = yappi.get_func_stats()
    func_stats.save('{}/hybrid_func.out'.format(log_dir), 'PSTAT')
    thread_stats = yappi.get_thread_stats()
    thread_stats.sort(sort_type='scnt').print_all(
        out=open('{}/hybrid_thread.out'.format(log_dir), 'w'))
    yappi.stop()
    yappi.clear_stats()

    # Record statistic
    # Memory analysis
    with plt.style.context('Solarize_Light2'):
        fig, ax = plt.subplots(nrows=1, ncols=1)
        for i in range(len(y)):
            ax.plot(x, y[i])
        plt.title('Memory - Time')
        plt.xlabel('Time', fontsize=14)
        plt.ylabel('Memory', fontsize=14)
        # ax.legend()
        # plt.show()
        fig.savefig('{}/hybrid_memory.pdf'.format(log_dir))
        # plt.close()
    # Time & Function analysis
    fw = open('{}/hybrid_statistic.txt'.format(log_dir),
              mode='w')
    with fw:
        fw.write("drone total cpu clock: {}.\n".format(end_clock - start_clock))
        fw.write("drone total running time: {}.\n".format(end_time - start_time))
        total_cpu_clock = 0
        max_cpu_clock = 0
        total_path_length = 0
        total_redundancy = 0
        for i in range(drone_num):
            fw.write("drone {} end work with path length {}.\n".format(i, fleet[i].cur_PLen))
            fw.write("drone {} end work with redundancy {}.\n".format(i, fleet[i].hybrid_rd))
            fw.write("drone {} cpu time: {}.\n".format(i, fleet[i].cloud_cpu_clock))
            fw.write(
                "drone {} communication cost: {}, communication count: {}, average communication time: {}.\n".format(
                    i, fleet[i].connect_cost, fleet[i].connect_count, fleet[i].connect_cost / fleet[i].connect_count))
            fw.write("drone {} memory changes {} within time {}.\n".format(i, y[i], x))
            total_cpu_clock += fleet[i].cloud_cpu_clock
            total_path_length += fleet[i].cur_PLen
            total_redundancy += fleet[i].hybrid_rd
            if fleet[i].cloud_cpu_clock > max_cpu_clock:
                max_cpu_clock = fleet[i].cloud_cpu_clock
        avg_cpu_clock = total_cpu_clock / drone_num
        avg_path_length = total_path_length / drone_num
        redundancy_ratio = total_redundancy / (metadata['width']*metadata['height'])

        qtool = QueryTool(database='multiAgents')
        qtool.safe_execute("SELECT * FROM grid_nodes")
        nodes_rows = qtool.cur.fetchall()
        nodes_colnames = [desc[0] for desc in qtool.cur.description]
        qtool.clear_db_connection()
        del qtool
        tar_count = 0
        complete_count = 0
        for row in nodes_rows:
            node_id = row[nodes_colnames.index('node_id')]
            visited = row[nodes_colnames.index('visited')]
            n_x = int(node_id / env.height)
            n_y = int(node_id % env.height)
            if not env.Nodes[n_x][n_y].blocked:
                tar_count += 1
                if visited:
                    complete_count += 1
        coverage_ratio = complete_count / tar_count
        fw.write("final total cpu clock: {}, avg cpu clock: {}, max cpu clock: {}.\n".format(
            total_cpu_clock, avg_cpu_clock, max_cpu_clock
        ))
        fw.write("final total path length: {}, avg path length:{}.\n".format(total_path_length, avg_path_length))
        fw.write("final coverage ratio: {}.\n".format(coverage_ratio))
        fw.write("final redundancy ratio: {}.\n".format(redundancy_ratio))
        fw.flush()

    yappi.set_clock_type("wall")
    yappi.start()
    # Reset parameters for memory monitoring
    x.clear()
    y.clear()
    y = [[] for i in range(drone_num)]
    is_monitoring = True

    # Reset fleet and fleet thread for broadcast fleet
    fleet.clear()
    fleet_thread.clear()
    # f_ids.clear()
    fleet = []
    fleet_thread = []
    f_ids = []

    # Declare global parameters for broadcast simulation
    global_map = []
    for i in range(drone_num):
        global_map.append(GlobalViewMap(scale=(env.width, env.height)))
    agents_path = []
    # next_pos = []
    agents_pos = []
    for i in range(drone_num):
        agents_path.append(dict({}))
        # next_pos.append(dict({}))
        agents_pos.append(dict({}))
        for j in range(drone_num):
            agents_path[i][j] = []
            # next_pos[i][j] = -1
    g_visited = [False for i in range(env.width*env.height)]
    # Declare global data locks for shared parameters in broadcast simulation
    map_lock = []
    paths_lock = []
    # next_lock = []
    pos_lock = []
    for i in range(drone_num):
        map_lock.append(Lock())
        paths_lock.append(Lock())
        # next_lock.append(Lock())
        pos_lock.append(Lock())
    # Start the broadcast drone threads
    for i in range(drone_num):
        fleet.append(
            UAV(ID=i, X=int(drone_locs[0][i] / env.height), Y=int(drone_locs[0][i] % env.height),
                NID=drone_locs[0][i], experiment_config=exper_config))
        drone_con_thread = Thread(target=fleet[i].broadcast_run_search, args=(env,))
        fleet_thread.append(drone_con_thread)
        drone_con_thread.start()
        # f_ids.append(drone_con_thread.ident)
    # Start memory monitoring thread
    monitor_thread = Thread(target=monitor_memory, args=(1, drone_num))
    monitor_thread.start()

    # Visualization Here

    # Waiting for drone threads end
    start_clock = time.clock()
    start_time = time.time()
    for i in range(drone_num):
        fleet_thread[i].join()
    end_clock = time.clock()
    end_time = time.time()
    print("Broadcast-Drones' activities end!\n")
    # print("Thread ids: ", f_ids)
    # End memory monitoring
    is_monitoring = False
    monitor_thread.join()
    del monitor_thread

    func_stats = yappi.get_func_stats()
    func_stats.save('{}/broadcast_func.out'.format(log_dir), 'PSTAT')
    thread_stats = yappi.get_thread_stats()
    thread_stats.sort(sort_type='scnt').print_all(
        out=open('{}/broadcast_thread.out'.format(log_dir), 'w'))
    yappi.stop()
    yappi.clear_stats()

    # Record statistic
    # Memory analysis
    with plt.style.context('Solarize_Light2'):
        fig, ax = plt.subplots(nrows=1, ncols=1)
        for i in range(len(y)):
            ax.plot(x, y[i])
        plt.title('Memory - Time')
        plt.xlabel('Time', fontsize=14)
        plt.ylabel('Memory', fontsize=14)
        fig.savefig('{}/broadcast_memory.pdf'.format(log_dir))
    # Time & Function analysis
    fw = open('{}/broadcast_statistic.txt'.format(log_dir), mode='w')
    with fw:
        fw.write("drone total cpu clock: {}.\n".format(end_clock - start_clock))
        fw.write("drone total running time: {}.\n".format(end_time - start_time))
        total_cpu_clock = 0
        max_cpu_clock = 0
        total_path_length = 0
        total_redundancy = 0
        for i in range(drone_num):
            fw.write("drone {} end work with path length {}.\n".format(i, fleet[i].cur_PLen))
            fw.write("drone {} end work with redundancy {}.\n".format(i, fleet[i].broadcast_rd))
            fw.write("drone {} cpu time: {}.\n".format(i, fleet[i].broadcast_cpu_clock))
            fw.write("drone {} memory changes {} within time {}.\n".format(i, y[i], x))
            total_cpu_clock += fleet[i].broadcast_cpu_clock
            total_path_length += fleet[i].cur_PLen
            total_redundancy += fleet[i].broadcast_rd
            if fleet[i].broadcast_cpu_clock > max_cpu_clock:
                max_cpu_clock = fleet[i].broadcast_cpu_clock
        avg_cpu_clock = total_cpu_clock / drone_num
        avg_path_length = total_path_length / drone_num
        redundancy_ratio = total_redundancy / (metadata['width']*metadata['height'])

        tar_count = 0
        complete_count = 0
        # for i in range(len(env.Nodes)):
        #     for j in range(len(env.Nodes[i])):
        #         if not env.Nodes[i][j].blocked:
        #             tar_count += 1
        #             tar_id = i * env.height + j
        #             if global_map[0].Nodes[tar_id].visited:
        #                 complete_count += 1
        complete_count =sum(g_visited)
        tar_count = env.width * env.height - int(metadata['obstacle_num'])
        coverage_ratio = complete_count / tar_count
        fw.write("final total cpu clock: {}, avg cpu clock: {}, max cpu clock: {}.\n".format(
            total_cpu_clock, avg_cpu_clock, max_cpu_clock
        ))
        fw.write("final total path length: {}, avg path length:{}.\n".format(total_path_length, avg_path_length))
        fw.write("final coverage ratio: {}.\n".format(coverage_ratio))
        fw.write("final redundancy ratio: {}.\n".format(redundancy_ratio))
        fw.flush()

    # Old Codes

    # start_time = time.time()
    # start_clock = time.clock()
    # while True:
    #     not_done = False
    #     for i in range(drone_num):
    #         not_done = not_done or fleet[i]._running
    #     time_elapse = time.time() - start_time
    #     if time_elapse > fleet[0].experiment_config.timeout or (not not_done):
    #         break
    # end_clock = time.clock()

    # metadata = '../data/metadata.json'
    # if metadata and os.path.isfile(metadata):
    #     with open(file=metadata, mode='r') as fr:
    #         metadata = json.loads("".join(fr.readlines()))['metadata']
    #         agent_g_num = metadata['agent_num']
    #         charge_pos_list = metadata['charge_pos_list']
    #         uav_count = 0
    #         drone_locs = []
    #         for j in range(len(agent_g_num)):
    #             drone_locs.append({})
    #             fleet_id = j
    #             for i in range(agent_g_num[j]):
    #                 uav_id = uav_count
    #                 uav_count += 1
    #                 if j != 2:
    #                     loc_node_id = random.randint(0, metadata['width'] * metadata['height'])
    #                 else:
    #                     loc_node_id = random.choice(charge_pos_list)
    #                 drone_locs[j][uav_id] = loc_node_id
    #         drone_num = uav_count
    # else:
    #     charge_list = []
    #     agent_g_num = [4]
    #     drone_locs = []
    #     uav_count = 0
    #     width = 10
    #     height = 10
    #     for j in range(len(agent_g_num)):
    #         drone_locs.append({})
    #         fleet_id = j
    #         for i in range(agent_g_num[j]):
    #             uav_id = uav_count
    #             uav_count += 1
    #             if j != 2:
    #                 loc_node_id = random.randint(0, width * height)
    #             else:
    #                 loc_node_id = random.choice(charge_list)
    #             drone_locs[j][uav_id] = loc_node_id
    #     drone_num = uav_count

    # # drawing the concrete env and all drones current state and their local_view
    # start_time = time.time()
    # cur_pos = []
    # cur_e = []
    # cur_sr = []
    # cur_f = []
    # for i in range(drone_num):
    #     cur_pos.append([fleet[i].cur_PX, fleet[i].cur_PY])
    #     cur_f.append(fleet[i].FID)
    #     if fleet[i].cur_E >= fleet[i].E * (1 - fleet[i].experiment_config.W_Threshold):
    #         new_e = 0
    #     elif fleet[i].E * (1 - fleet[i].experiment_config.C_Threshold) <= fleet[i].cur_E < fleet[i].E * (
    #             1 - fleet[i].experiment_config.W_Threshold):
    #         new_e = 1
    #     else:
    #         new_e = 2
    #     cur_e.append(new_e)
    #     cur_sr.append(fleet[i].SR)
    # env_window = Cgrid(env=env, agents_info=(cur_pos, cur_e, cur_f), agents_view=cur_sr)
    # # env_window.mainloop()
    #
    # while True:
    #     cur_pos = []
    #     cur_e = []
    #     cur_sr = []
    #     not_done = False
    #     for i in range(drone_num):
    #         not_done = not_done or fleet[i]._running
    #         cur_pos.append([fleet[i].cur_PX, fleet[i].cur_PY])
    #         new_e = -1
    #         if fleet[i].cur_E >= fleet[i].E * (1 - fleet[i].experiment_config.W_Threshold):
    #             new_e = 0
    #         elif fleet[i].E * (1 - fleet[i].experiment_config.C_Threshold) <= fleet[i].cur_E < fleet[i].E * (
    #                 1 - fleet[i].experiment_config.W_Threshold):
    #             new_e = 1
    #         else:
    #             new_e = 2
    #         cur_e.append(new_e)
    #         cur_sr.append(fleet[i].SR)
    #     s_ = env_window.step(env, cur_pos, cur_e, cur_sr)
    #     env_window.update_idletasks()
    #     env_window.update()
    #     time.sleep(0.1)
    #     time_elapse = time.time() - start_time
    #     if time_elapse > fleet[0].experiment_config.timeout or (not not_done):
    #         break
