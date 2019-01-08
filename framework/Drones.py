# -*- coding:utf-8 -*-
import sys
import math
import random
import time
from socket import *
from threading import Thread
import json
import heapq
import tkinter as tk
import numpy as np

sys.path.append('../')
from framework.CustomExceptions import *
from framework.StaticConsensus import *
from framework.QueryTool import *
from framework.EnvMap import *


class UAV:

    def __init__(self, ID, experiment_config):
        self._running = True  # used to control the termination of agent process and its child threads.
        self.STATIC_INFO = StaticInfo()  # static consensus info between agents and center
        self.experiment_config = experiment_config

        # arguments related to socket connections with center
        self.HOST = '127.0.0.1'
        self.PORT = 65432
        self.socket = None
        self.UID = ID

        self.Local_View_Map = LocalViewMap()  # 空局部地图View
        self.cur_charge_tar = None
        self.cur_rescue_tar = None

        self.action_space = [(0, 1, 1), (0, -1, 1), (-1, 0, 1), (1, 0, 1), (0, 0, 1), (0, 0, 0)]
        self.path_buffer = []
        self.start = True

        self.state_init()


    def state_init(self):
        get_data, _ = self.connect_with_center(RoW='R', View_List=[2], GoL='L')  # list
        # print(get_data)
        # print(len(get_data))
        # print(get_data[0])
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
        # 在init情况下,所有uav的flying_state只有可能是0或1
        # 在reset情况下,首先reset的是数据库中drones,map等相关的数据,然后再重新从数据中init
        # 即无人机reset函数的调用必须在环境reset及中心全局数据reset之后
        # 1)环境状态reset 2)全局数据reset 3)中心属性reset 4)agents属性reset
        # 如果环境和关于环境的全局数据保持最新状态，仅想要reset所有的无人机则
        # 1)全局数据中关于drones state的数据reset 2)中心中有关drones的属性reset 3)agents属性reset
        self.TID = None

    def reset(self):
        if self.socket is not None:
            self.socket.close()
        self.socket = None
        self._running = True
        self.state_init()

    def terminate(self):
        self._running = False
        # if self.socket is not None:
        #     self.socket.close()

    def connect_with_center(self, RoW='R', View_List=None, GoL='L', Datas=None, SQLs=None):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.connect((self.HOST, self.PORT))

        send_data = self.before_send_request(RoW, View_List, GoL, Datas, SQLs)
        send_data = json.dumps(send_data)
        # print(send_data)
        self.socket.send(send_data.encode())
        get_data = None
        while True:
            try:
                data = self.socket.recv(16384)
                if not data:
                    print("Without receiving data.")
                    break
                data = data.decode()
                # print(data)

                if data == "Request is received." or data == "Request is in queue." or data == 'Data Ready.':
                    print(data)
                    continue
                elif data == "Put is done.":
                    print("Put is done")
                    break
                else:
                    print("Receiving meaningful data.")
                    data = json.loads(data)
                    if isinstance(data, list):
                        self.socket.send('Data is received.'.encode())
                        get_data = data
                        break
                    else:
                        raise CustomError('Returned wrong data!')

            except Exception as e:
                print("Exception when receiving data from center.")
                print(e)
                break
        # time.sleep(4)
        self.socket.close()
        return get_data, True

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
        # init request(read) test
        # pass
        # self.state_init()
        while self._running:
            # read request test
            # pass
            get_data, _ = self.connect_with_center(RoW='R', View_List=[3], GoL='L')
            # print(get_data)
            get_data, _ = self.connect_with_center(RoW='R', View_List=[4], GoL='L')
            # print(get_data)
            # print(get_data)
            # # pass
            # self.connect_with_center(RoW='R',View_List=[0,1,2],GoL='L')
            # # pass
            # self.connect_with_center(RoW='R',SQLs=["SELECT * FROM public.drones_config","SELECT * FROM public.nodes_config"],GoL='G')
            # time.sleep(5)
            # # write request test
            # # pass
            # self.connect_with_center(RoW='W',View_List=[0],GoL='L',Datas={'sense_time':time.time(),
            #                                                               'new_data':[[{'UID':self.UID,
            #                                                                           'NID':self.cur_NID,
            #                                                                           'VC':1,
            #                                                                           'V': True,
            #                                                                           'VN':random.randint(0,10),
            #                                                                           'NR': False,
            #                                                                           'NT': 0,
            #                                                                           }]]
            #                                                               })
            # # pass
            # self.connect_with_center(RoW='W',SQLs=["UPDATE public.rescue_support_cur_state "
            #                                        "SET is_allocated= FALSE, responsible_uav_id= NULL "
            #                                        "WHERE target_id = {}".format(self.cur_NID)],GoL='G', Datas={'sense_time':time.time()})

            break

    def run(self, env):
        # State Machine
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
                    # print("No TID?", self.TID)
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
                    if not self.is_work_done(0):
                        get_data, _ = self.connect_with_center(RoW='R', View_List=[0, 1], GoL='L')
                        # 以下两句会将Local_View_Map中的数据更新到最新,第一句得到的数据均标记为未更新(因为是从center拿到的)
                        # 第二句中sense到的并且和Local_View_Map中数据不一致的要更新,并把所有更新过的标记为已更新
                        # print(get_data)
                        self.Local_View_Map.update_map(get_data)
                        # print(self.Local_View_Map.Nodes)
                        # print(self.Local_View_Map.Edges)
                        sense_time = self.sense_within_range(env)
                        healthy = self.self_check()
                        if healthy:
                            new_data = self.gen_new_data(View_List=[0, 1, 2])
                            self.connect_with_center(RoW='W', View_List=[0, 1, 2], GoL='L',
                                                     Datas={'sense_time': sense_time,
                                                            'new_data': new_data},
                                                     SQLs=None)

                            next_nid, next_x, next_y = self.make_move_decision(tid=0, scale=(env.width, env.height))
                            print("next_nid is ", next_nid)
                            print("next x is", next_x)
                            print("next y is", next_y)
                            print("\n\n\n")
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
                                if self.VR < math.sqrt(env.width * env.width + env.height * env.height):
                                    self.VR = math.ceil(math.sqrt(env.width * env.width + env.height * env.height))
                                    sense_time = time.time()
                                    new_data = [[{'UID': self.UID, 'NID': self.cur_NID, 'VR': self.VR, 'LN': self.cur_LN,
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
                            new_data = self.gen_new_data(View_List=[0, 1, 2])
                            self.connect_with_center(RoW='W', View_List=[0, 1, 2], GoL='L',
                                                     Datas={'sense_time': sense_time,
                                                            'new_data': new_data},
                                                     SQLs=None)
                            # time.sleep(1)
                            get_data, _ = self.connect_with_center(RoW='R', View_List=[3], GoL='L')

                            # print("\n\n\n")
                            # print("Charge tar view reading check")
                            # print(get_data)
                            # print(len(get_data))  # 1
                            # print(len(get_data[0]))  # 2
                            # print(len(get_data[0][1]))  # 可选充电目标点数目,目前的表格中初步估计为0
                            # print("\n\n\n")

                            charge_tar = get_data[0]

                            self.Local_View_Map.update_charge_stations(charge_tar)
                            self.cur_State = 2
                    else:
                        self.cur_State = 5
                        break
                elif self.TID == 1:
                    # working in rescue_coverage_task
                    if not self.is_work_done(1):
                        get_data, _ = self.connect_with_center(RoW='R', View_List=[0, 1, 4], GoL='L')
                        # 以下两句会将Local_View_Map中的数据更新到最新,第一句得到的数据均标记为未更新(因为是从center拿到的)
                        # 第二句中sense到的并且和Local_View_Map中数据不一致的要更新,并把所有更新过的标记为已更新
                        self.Local_View_Map.update_map(get_data[0:2])
                        self.Local_View_Map.update_rescue_targets(get_data[2])
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
                                    new_data = [[{'UID': self.UID, 'NID': self.cur_NID, 'VR': self.VR, 'LN': self.cur_LN,
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
                            new_data = self.gen_new_data(View_List=[0, 1, 2, 4])
                            self.connect_with_center(RoW='W', View_List=[0, 1, 2, 4], GoL='L',
                                                     Datas={'sense_time': sense_time,
                                                            'new_data': new_data},
                                                     SQLs=None)
                            # time.sleep(1)

                            get_data, _ = self.connect_with_center(RoW='R', View_List=[3], GoL='L')

                            # print("\n\n\n")
                            # print("Charge tar view reading check")
                            # print(get_data)
                            # print(len(get_data))  # 1
                            # print(len(get_data[0]))  # 2
                            # print(len(get_data[0][1]))  # 可选充电目标点数目,目前的表格中初步估计为0
                            # print("\n\n\n")

                            charge_tar = get_data[0]
                            self.Local_View_Map.update_charge_stations(charge_tar)
                            self.cur_State = 2
                    else:
                        self.cur_State = 5
                        break
            elif self.cur_State == 2:
                # TODO: GO FOR CHARGING
                if self.cur_charge_tar is None:
                    self.cur_charge_tar = self.choose_charging_station()
                if self.cur_NID != self.cur_charge_tar.NID:
                    # 飞到指定地点的过程中,cur_state=2不变
                    # 但要注意判断需不需要变更指定地点
                    # 判断依据是每到一个新地点都需要重新获取一次的charge targets view
                    continue
                else:
                    # 到达指定地点时进行判断,看能不能充电
                    # 注意:如果是由UAV主动变更charge targets view中充电站的属性,必须是到达该点的时候
                    # 其他时候view的主动变更直接由center操作(可以理解为充电站主体主动变更并告知了center,center直接修改了相关table数据)
                    if self.cur_charge_tar.cur_utilization < self.cur_charge_tar.charging_cap:
                        self.cur_State = 4
                    elif self.cur_charge_tar.queue_length < self.cur_charge_tar.queue_cap:
                        self.cur_State = 3
                    elif self.cur_charge_tar.dock_num < self.cur_charge_tar.dock_cap:
                        self.cur_State = 3  # 暂时dock在充电站等待进入等待充电的队列,以及在充电队列
                        # 再设置个量和上面的直接进入等待充电队列的分开,交给state=3的部分判断
                    else:
                        self.cur_State = 5  # 没有地方停,没有地方充电,只能是退出任务,随便找地方降落等待回收
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
            time.sleep(2)
        # 主进程要求终止后，需要处理的收尾工作
        if self.cur_State == 5:
            sense_time = time.time()
            new_data = [
                [{'UID': self.UID, 'NID': self.cur_NID, 'VR': self.VR, 'LN': self.cur_LN, 'CE': self.cur_E,
                  'FS': 5, 'CL': self.cur_PLen, 'RC': self.cur_RCost}]]
            self.connect_with_center(RoW='W', View_List=[2], GoL='L',
                                     Datas={'sense_time': sense_time, 'new_data': new_data}, SQLs=None)
            self._running = False
        return None

    # 下面的应该全是辅助run函数实现的函数
    def is_allocated_task(self):
        task_data, _ = self.connect_with_center(RoW='R', GoL='G', SQLs=[
            "SELECT area_id, responsible_fleet_id, end_time FROM public.rescue_support_task",
            "SELECT area_id, responsible_fleet_id, end_time FROM public.search_coverage_task"])

        # print('\n\n\n')
        # print("is allocated check!")
        # print(len(task_data))  # 2
        # print(len(task_data[0]))  # 2
        # print(len(task_data[1]))  # 2
        # print(len(task_data[0][1]))  # 1
        # print(len(task_data[1][1]))  # 1
        # print('\n\n\n')

        rescue_support_task = task_data[0][1][0]  # tuple, only one area
        search_coverage_task = task_data[1][1][0]  # tuple, only one area
        if self.FID == search_coverage_task[1] and not search_coverage_task[2]:
            self.TID = 0
            return True
        elif self.FID == rescue_support_task[1] and not rescue_support_task[2]:
            self.TID = 1
            return True
        elif self.FID == search_coverage_task[1] and search_coverage_task[2]:
            # 曾经被分配任务,且任务已结束
            self.TID = 0
            return False
        elif self.FID == rescue_support_task[1] and rescue_support_task[2]:
            self.TID = 1
            return False
        else:
            # 还没有被分配任务
            self.TID = None
            return False

    def sense_within_range(self, env):

        def get_local_info(g_env):
            local_nodes = {}
            for key, node in self.Local_View_Map.Nodes.items():
                env_node = g_env.Nodes[node.pos_x][node.pos_y]
                if not isinstance(env_node, ChargingPoint):
                    if not env_node == node:
                        local_nodes[key] = env_node
            local_edges = {}
            for key, edge in self.Local_View_Map.Edges.items():
                env_edge = g_env.Edges[edge.EID]
                if not env_edge == edge:
                    local_edges[key] = env_edge
            local_ = (local_nodes, local_edges)
            return local_

        concrete_local = get_local_info(g_env=env)
        # update local view using concrete_local
        sense_time = time.time()

        # print(list(concrete_local[0].keys()))
        # print(self.cur_PX)
        # print(self.cur_PY)
        # print(len(env.Nodes))
        # print(len(env.Nodes[self.cur_PX]))
        if not isinstance(env.Nodes[self.cur_PX][self.cur_PY], ChargingPoint):
            concrete_local[0][self.cur_NID].visited = True
            concrete_local[0][self.cur_NID].visit_count = self.Local_View_Map.Nodes[self.cur_NID].visit_count + 1

        # TODO:update view map的时候不能只按照concrete local来,有一些数据必须保留,
        # 比如visit_count要在原本数据的基础上加1,当前位置的visited改为True等
        self.Local_View_Map.update_map(concrete_local, sense_time)

        # TODO:除了update_map,还要视情况看需不需要update_charging_targets和update_rescue_targets
        def get_local_rescue_tars(g_env):
            rescue_tars = []
            return rescue_tars

        def get_local_charge_tars(g_env):
            charge_tars = []
            return charge_tars

        if self.cur_rescue_tar is not None:
            if self.cur_NID == self.cur_rescue_tar.NID and self.cur_State == 1 and self.TID == 1:
                concrete_rescue_tars = get_local_rescue_tars(env)
                self.Local_View_Map.update_rescue_targets(concrete_rescue_tars, sense_time)
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
                for t_, new_tar in enumerate(self.Local_View_Map.rescue_targets):
                    if self.Local_View_Map.update_state[3][t_][0]:
                        new_record = {'VN': new_tar.victims_num,
                                      'LDN': new_tar.load_demand_num,
                                      'IC': not new_tar.need_rescue,
                                      'TID': new_tar.NID}
                        new_data[i_].append(new_record)

        return new_data

    def make_move_decision(self, tid, scale, healthy=True, strategy='BoB'):
        # TODO: realize different moving strategies.
        if healthy:
            if tid == 0:
                if strategy == 'BoB':
                    print("\n\n\n")
                    print("Now in BoB")
                    print("Now agent on:", self.cur_NID)
                    # BoB算法决策的基础是Grid中相邻两点之间的距离相等均为1
                    # print(self.Local_View_Map.Nodes.keys())
                    cur_node = self.Local_View_Map.Nodes[self.cur_NID]
                    if self.start:
                        l_o_r = 0  # -1:left, 1:right
                        u_o_d = 0  # -1:down, 1:up
                        if self.cur_PX <= scale[0] / 2:
                            self.l_o_r = 1
                        else:
                            self.l_o_r = -1
                        if self.cur_PY <= scale[1] / 2:
                            self.u_o_d = 1
                        else:
                            self.u_o_d = -1
                        self.start = False
                    has_next = False
                    valid_next = []
                    if len(self.path_buffer) == 0:
                        for i in range(4):
                            next_x = self.action_space[i][0] + self.cur_PX
                            next_y = self.action_space[i][1] + self.cur_PY
                            if 0 <= next_x < scale[0] and 0 <= next_y < scale[1]:
                                next_nid = next_x * scale[1] + next_y

                                # print("\n\n\n")
                                # print("cur x,y:", self.cur_PX, self.cur_PY)
                                # print("cur nid is:", self.cur_NID)
                                # print("next x,y:", next_x, next_y)
                                # print("next nid is:", next_nid)
                                # print("size of local view:", len(self.Local_View_Map.Nodes))
                                # print(self.Local_View_Map.Nodes.keys)
                                # print("\n\n\n")

                                next_node = self.Local_View_Map.Nodes[next_nid]

                                is_valid = next_node.is_charge_p or (not next_node.blocked and not next_node.visited)
                                has_next = has_next or is_valid

                                if is_valid:
                                    valid_next.append(True)
                                else:
                                    valid_next.append(False)
                            else:
                                valid_next.append(False)
                                continue
                        print("has_next is ", has_next)
                        print("valid_next is", valid_next)
                        if has_next:
                            print("result 1 x,y:", self.cur_PX, self.cur_PY)
                            next_y = self.cur_PY + self.u_o_d
                            if 0 <= next_y < scale[1]:
                                print("result 1 next_y", next_y)
                                next_nid = self.cur_PX * scale[1] + next_y
                                next_node = self.Local_View_Map.Nodes[next_nid]
                            if 0 <= next_y < scale[1] and (next_node.is_charge_p or (
                                    not next_node.blocked and not next_node.visited)):
                                print("1 result, u_o_d: {}, l_o_r: {}".format(self.u_o_d, self.l_o_r))
                                return next_nid, self.cur_PX, next_y
                            else:
                                print("result 2 x,y:", self.cur_PX, self.cur_PY)
                                next_y = self.cur_PY - self.u_o_d
                                if 0 <= next_y < scale[1]:
                                    print("result 2 next_y", next_y)
                                    next_nid = self.cur_PX * scale[1] + next_y
                                    next_node = self.Local_View_Map.Nodes[next_nid]
                                if 0 <= next_y < scale[1] and (next_node.is_charge_p or (
                                        not next_node.blocked and not next_node.visited)):
                                    self.u_o_d = -self.u_o_d
                                    print("2 result, u_o_d: {}, l_o_r: {}".format(self.u_o_d, self.l_o_r))
                                    return next_nid, self.cur_PX, next_y
                                else:
                                    print("result 3 x,y:", self.cur_PX, self.cur_PY)
                                    next_x = self.cur_PX + self.l_o_r
                                    if 0 <= next_x < scale[0]:
                                        print("result 3 next_x", next_x)
                                        next_nid = next_x * scale[1] + self.cur_PY
                                        next_node = self.Local_View_Map.Nodes[next_nid]
                                    if 0 <= next_x < scale[0] and (next_node.is_charge_p or (
                                            not next_node.blocked and not next_node.visited)):
                                        self.u_o_d = -self.u_o_d
                                        print("3 result, u_o_d: {}, l_o_r: {}".format(self.u_o_d, self.l_o_r))
                                        return next_nid, next_x, self.cur_PY
                                    else:
                                        print("result 4 x,y:", self.cur_PX, self.cur_PY)
                                        next_x = self.cur_PX - self.l_o_r
                                        if 0 <= next_x < scale[0]:
                                            print("result 4 next_x", next_x)
                                            next_nid = next_x * scale[1] + self.cur_PY
                                            next_node = self.Local_View_Map.Nodes[next_nid]
                                        if 0 <= next_x < scale[0] and (next_node.is_charge_p or (
                                                not next_node.blocked and not next_node.visited)):
                                            self.u_o_d = -self.u_o_d
                                            self.l_o_r = -self.l_o_r
                                            print("4 result, u_o_d: {}, l_o_r: {}".format(self.u_o_d, self.l_o_r))
                                            return next_nid, next_x, self.cur_PY
                                        else:
                                            raise CustomError("No valid next action when has_next was TRUE!")
                                            return None, None, None
                        else:
                            # TODO:bob_find_new_start中有bug,会导致途径障碍物点(没有处理周围全是障碍物的特殊情况)
                            # print("I am here 1!")
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
                        # print("I am here 2!")
                        new_start, min_len = self.bob_find_new_start()
                        if new_start:
                            next_node = self.Local_View_Map.Nodes[self.path_buffer[0]]
                            next_x = next_node.pos_x
                            next_y = next_node.pos_y
                            next_nid = next_node.NID
                            return next_nid, next_x, next_y
                        else:
                            return None, None, None
            elif tid == 1:
                next_nid = self.cur_NID
                next_x = self.cur_PX
                next_y = self.cur_PY
        return next_nid, next_x, next_y

    def choose_charging_station(self):
        # TODO: realize min cost decision
        tar = ChargingPoint(0, 0, 0, 0)
        return tar

    def choose_rescue_target(self):
        # TODO: realize min cost decision
        tar = Point(0, 0, 0)
        return tar

    def bob_find_new_start(self):
        tar = 0
        if len(self.path_buffer) > 0:
            cur_tar = self.path_buffer[len(self.path_buffer) - 1]
            # 需要判断当前是否有比cur_tar更好的目标,如果没有则不变,如果有则更新self.path_buffer
            tar = cur_tar
            min_len = len(self.path_buffer)
        else:
            min_cost, path = self.dijkstra()
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

    def dijkstra(self):
        visited = {self.cur_NID: 0}  # 包含所有已添加的点,并且key-value对表示key对应的点到initial点(即self.cur_NID)的最小距离
        h = [(0, self.cur_NID)]
        path = {}  # path[v]=a,代表到达v之前的一个点是a,需要回溯得到整个路径

        nodes_index = set(set(range(len(self.Local_View_Map.Nodes))))

        while nodes_index and h:
            current_weight, min_node = heapq.heappop(h)
            try:
                while min_node not in nodes_index:
                    current_weight, min_node = heapq.heappop(h)
            except IndexError:
                break
            nodes_index.remove(min_node)

            for key, edge in self.Local_View_Map.Edges.items():
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
        # self.cur_RCost = self.cur_RCost + random.randint(0, 2 - self.cur_RCost)
        # 损坏状态随机变换,也可以假设始终保持不变
        sense_time = time.time()

        # self.VR = self.VR  # 根据具体情况有可能可以改变, 但一般认为应该在make_move_decision的时候改, 改完了重新回到IW状态下的0状态
        return sense_time

    def is_work_done(self, tid):
        ct = 0
        if tid == 0:
            while ct < 3:
                try:
                    get_data, returned = self.connect_with_center(RoW='R', GoL='G',
                                                                  SQLs=[
                                                                      'SELECT end_time FROM public.search_coverage_task '
                                                                      'WHERE start_time IS NOT NULL '
                                                                      'AND responsible_fleet_id = {} '.format(
                                                                          self.FID)])
                    # print('\n\n\n')
                    # print("is work done check!")
                    # print(len(get_data))  # 1
                    # print(len(get_data[0]))  # 2
                    # print(len(get_data[0][1]))  # fleet负责的任务数
                    # print(returned)
                    # print(get_data)
                    # print('\n\n\n')

                    # print(get_data)
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
                    get_data, _ = self.connect_with_center(RoW='R', GoL='G',
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


class Cgrid(tk.Tk, object):

    def __init__(self, env, agents_info, agents_view):
        super(Cgrid, self).__init__()
        self.staticInfo = StaticInfo()
        self.action_space = [(0, 1, 1), (0, -1, 1), (-1, 0, 1), (1, 0, 1), (0, 0, 1), (0, 0, 0)]
        self.n_actions = len(self.action_space)
        self.title('Concrete Environment')
        self.env = env
        self.map_w = env.width
        self.map_h = env.height
        self.agents_loc = agents_info[0]
        self.agents_e = agents_info[1]
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
        for x in range(0, self.map_w * self.staticInfo.UNIT, self.staticInfo.UNIT):
            self.grid_block.append([])
            for y in range(0, self.map_h * self.staticInfo.UNIT, self.staticInfo.UNIT):
                block = self.canvas.create_rectangle((x, y, x + self.staticInfo.UNIT, y + self.staticInfo.UNIT),
                                                     fill='white', disabledfill='black')
                self.grid_block[len(self.grid_block) - 1].append(block)

        # create origin(原点)
        origin = np.array([self.staticInfo.UNIT / 2, self.staticInfo.UNIT / 2])

        # create ordinary nodes, obstacle and charging station in env
        self.stats = []
        self.obs = []
        self.vbs = []
        for i in range(self.map_w):
            for j in range(self.map_h):
                if isinstance(self.env.Nodes[i][j], ChargingPoint):
                    # charging station
                    stat_center = origin + np.array([self.staticInfo.UNIT * i, self.staticInfo.UNIT * j])
                    p1 = stat_center + np.array([0, self.staticInfo.UNIT / 4])
                    p2 = stat_center + np.array([-self.staticInfo.UNIT / 4, -self.staticInfo.UNIT / 4])
                    p3 = stat_center + np.array([self.staticInfo.UNIT / 4, -self.staticInfo.UNIT / 4])
                    stat = self.canvas.create_polygon(
                        (p1[0], p1[1], p2[0], p2[1], p3[0], p3[1]),
                        fill='green', disabledfill='black')
                    self.stats.append({'pos': (i, j), 'stat': stat})
                elif self.env.Nodes[i][j].blocked:
                    # obstacle
                    ob_center = origin + np.array([self.staticInfo.UNIT * i, self.staticInfo.UNIT * j])
                    p1 = ob_center + np.array([self.staticInfo.UNIT / 2, self.staticInfo.UNIT / 2])
                    p2 = ob_center + np.array([self.staticInfo.UNIT / 2, -self.staticInfo.UNIT / 2])
                    p3 = ob_center + np.array([-self.staticInfo.UNIT / 2, self.staticInfo.UNIT / 2])
                    p4 = ob_center + np.array([-self.staticInfo.UNIT / 2, -self.staticInfo.UNIT / 2])
                    self.canvas.itemconfig(self.grid_block[i][j], fill='brown')
                    line1 = self.canvas.create_line((p1[0], p1[1], p4[0], p4[1]), fill='red', disabledfill='black')
                    line2 = self.canvas.create_line((p2[0], p2[1], p3[0], p3[1]), fill='red', disabledfill='black')
                    self.obs.append({'pos': (i, j), 'l1': line1, 'l2': line2})
                else:
                    # ordinary node
                    n_center = origin + np.array([self.staticInfo.UNIT * i, self.staticInfo.UNIT * j])
                    p1 = n_center + np.array([-self.staticInfo.UNIT / 2, -self.staticInfo.UNIT / 2])
                    p2 = n_center + np.array([-self.staticInfo.UNIT / 4, -self.staticInfo.UNIT / 4])
                    if self.env.Nodes[i][j].need_rescue:
                        fill = 'purple'
                    else:
                        fill = 'blue'
                    block = self.canvas.create_rectangle((p1[0], p1[1], p2[0], p2[1]), fill=fill, outline='black',
                                                         disabledfill='black')
                    text = self.canvas.create_text((p1[0], p1[1]),
                                                   text='{}'.format(self.env.Nodes[i][j].victims_num),
                                                   anchor='sw', fill='white', disabledfill='white')
                    self.vbs.append({'pos': (i, j), 'block': block, 'num': text})
        self.agents = []

        # create agents
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

        # disable env components out of view range

        for i in range(self.map_w):
            for j in range(self.map_h):
                for a in range(len(self.agents)):
                    if math.pow(self.agents_loc[a][0]-i,2) + math.pow(self.agents_loc[a][1]-j,2)<= math.pow(self.agents_view[a],2):
                        self.canvas.itemconfig(self.grid_block[i][j], state='normal')
                        break
                    else:
                        self.canvas.itemconfig(self.grid_block[i][j], state='disabled')

        for each in self.vbs:
            re = self.canvas.itemcget(self.grid_block[each['pos'][0]][each['pos'][1]], 'state')

            if re == 'disabled':
                self.canvas.itemconfig(each['block'], state='disabled')
                self.canvas.itemconfig(each['num'], state='disabled')
        for each in self.stats:
            re = self.canvas.itemcget(self.grid_block[each['pos'][0]][each['pos'][1]], 'state')
            if re == 'disabled':
                self.canvas.itemconfig(each['stat'], state='disabled')
        for each in self.obs:
            re = self.canvas.itemcget(self.grid_block[each['pos'][0]][each['pos'][1]], 'state')
            if re == 'disabled':
                self.canvas.itemconfig(each['l1'], state='disabled')
                self.canvas.itemconfig(each['l2'], state='disabled')

        # pack all
        self.canvas.pack()

    def step(self, new_locs, new_e, new_sr):
        s = []
        s_ =[]
        for i, ag in enumerate(self.agents):
            coor=self.canvas.coords(ag['circle'])
            s.append([int(coor[0])/self.staticInfo.UNIT, int(coor[1])/self.staticInfo.UNIT])
            base_action = np.array([(new_locs[i][0]-s[i][0]) * self.staticInfo.UNIT,
                                    (new_locs[i][1]-s[i][1])*self.staticInfo.UNIT])
            self.canvas.move(ag['circle'], base_action[0], base_action[1])  # move agent circle
            self.canvas.move(ag['light'], base_action[0],base_action[1])
            if new_e[i] == 0:
                fill = 'green'
            elif new_e[i] == 1:
                fill = 'yellow'
            else:
                fill = 'red'
            self.canvas.itemconfig(ag['light'], fill=fill)
            for r in range(max(0,new_locs[i][0]-new_sr[i]),min(self.map_w,new_locs[i][0]+new_sr[i]+1)):
                for c in range(max(0,new_locs[i][1]-new_sr[i]),min(self.map_h,new_locs[i][1]+new_sr[1]+1)):
                    if math.pow(r-new_locs[i][0],2)+math.pow(c-new_locs[i][1],2)<= new_sr[i]*new_sr[i]:
                        if self.canvas.itemcget(self.grid_block[r][c],'state') == 'disabled':
                            self.canvas.itemconfig(self.grid_block[r][c],state='normal')

            for each in self.vbs:
                re = self.canvas.itemcget(self.grid_block[each['pos'][0]][each['pos'][1]], 'state')

                if re == 'normal':
                    self.canvas.itemconfig(each['block'], state='normal')
                    self.canvas.itemconfig(each['num'], state='normal')

            for each in self.stats:
                re = self.canvas.itemcget(self.grid_block[each['pos'][0]][each['pos'][1]], 'state')
                if re == 'normal':
                    self.canvas.itemconfig(each['stat'], state='normal')
            for each in self.obs:
                re = self.canvas.itemcget(self.grid_block[each['pos'][0]][each['pos'][1]], 'state')
                if re == 'normal':
                    self.canvas.itemconfig(each['l1'], state='normal')
                    self.canvas.itemconfig(each['l2'], state='normal')
            s_.append([new_locs[i][0],new_locs[i][1]])
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

    def render(self,new_locs,new_e,new_sr):
        time.sleep(0.1)
        self.update(new_locs,new_e,new_sr)

def update(new_locs,new_e,new_sr):
    while True:
        if new_locs is None:
            break
        env.render(new_locs,new_e,new_sr)
        s_ = env.step(new_locs,new_e,new_sr)



if __name__ == '__main__':

    qtool = QueryTool(database='multiAgents')
    col_nms_1, rows_1 = qtool.get_view(view_name='drones_cur_state')
    col_nms_2, rows_2 = qtool.get_view(view_name='charging_stations_config')
    qtool.clear_db_connection()

    drone_num = len(rows_1)
    drone_locs = {}
    for row in rows_1:
        drone_locs[row[col_nms_1.index('uav_id')]] = row[col_nms_1.index('loc_node_id')]
    charge_list = []
    for row in rows_2:
        charge_list.append(row[col_nms_2.index('node_id')])

    fleet = []
    fleet_thread = []
    env = ConcreteEnv(charge_list=charge_list, drone_locs=drone_locs)

    for i in range(drone_num):
        fleet.append(UAV(ID=i, experiment_config=ExperimentConfig()))
        drone_con_thread = Thread(target=fleet[i].run, args=(env,))
        # drone_con_thread = Thread(target=fleet[i].test)
        fleet_thread.append(drone_con_thread)
        drone_con_thread.start()

    # drawing the concrete env and all drones current state and their local_view
    # start_time = time.time()
    # cur_pos = []
    # cur_e = []
    # cur_sr = []
    # for i in range(drone_num):
    #     cur_pos.append([fleet[i].cur_PX, fleet[i].cur_PY])
    #     cur_e.append(fleet[i].cur_E)
    #     cur_sr.append(fleet[i].SR)
    # env_window = Cgrid(env= env,agents_info=(cur_pos,cur_e),agents_view=cur_sr)
    # env_window.mainloop()
    #
    # while True:
    #     cur_pos = []
    #     cur_e = []
    #     cur_sr = []
    #     for i in range(drone_num):
    #         cur_pos.append([fleet[i].cur_PX, fleet[i].cur_PY])
    #         cur_e.append(fleet[i].cur_E)
    #         cur_sr.append(fleet[i].SR)
    #
    #     time.sleep(0.2)
    #     s_ = env_window.step(cur_pos, cur_e, cur_sr)
    #     time.sleep(3)
    #     time_elapse = time.time() - start_time
    #     if time_elapse > fleet[0].experiment_config.timeout:
    #         break


    time.sleep(600)

    for i in range(drone_num):
        fleet[i].terminate()
        fleet_thread[i].join()

    print("Drones' activities end!")

