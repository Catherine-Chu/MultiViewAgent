# -*- coding:utf-8 -*-
import sys

sys.path.append('../')
from framework.CustomExceptions import *
from framework.StaticConsensus import *
from framework.QueryTool import *
from scripts.DataGenerator import *
from baseline.BoB import *
from framework.EnvMap import *

import time
import uuid
from socket import *
import threading
from threading import Thread
from threading import Condition
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, PriorityQueue
import heapq
import tkinter as tk
import json
import math
import argparse
import copy
import yappi

class Center:
    '''
    1. 通信能力：
        1)能够接收到来自agent的读写数据请求
        2)能够分析来自agent的读写数据请求(数据读写请求应该即支持对view表的读写,也应该支持直接对table的读写,可以理解为,如果需要直接读table中的数据,
        相当于这个table表中的所有信息都需要所有无人机共享,不过一般这种都已经整合到view表中了,如果需要写table中的数据则可能是一方手机信息后写入,
        但这部分数据可能对自己没有用,不需要使用view保证对自己的同步,而是对另一方有用,又或者是只需要记录,不需要再读取和保持同步的表)
        3)能够针对读请求,从数据库中获取相应的数据
        4)能够针对写请求,对数据库中相应的数据进行修改
        5)能够对数据读写请求进行适当的回复
        6)能够处理并发读写请求
    2. 数据统计能力：
        1)每次从agent处获取新数据后,除了更新对应的表,还要通过计算更新任务状态统计表
    3. 数据计算能力：
        1)每次在agent想要获取任务/充电目标相关的view之前都要根据具体需求计算更新相应的表
    '''

    def __init__(self, metadata):
        self._running = True  # used to control the termination of center process and its child threads.
        self.STATIC_INFO = StaticInfo()  # static consensus info between agents and center
        self.experiment_config = ExperimentConfig()

        # arguments related to socket connections with agents
        self.MAX_QUEUE_LEN = 1000
        self.MAX_CON = 2000
        self.HOST = '127.0.0.1'
        self.PORT = 8888
        self.socket = None

        self.request_queue = []
        self.condition = Condition()  # R/W Lock
        self.resp_conditions = {}
        self.con_thread_pool = ThreadPoolExecutor(self.MAX_CON)  # control the accepted number of I/O threads.
        threading.stack_size(self.STATIC_INFO.THREAD_STACK_SIZE)  # control the stack memory size of each threads.
        self.query_tool = QueryTool(database='multiAgents')
        self.response_data = {}
        self.query_tool.safe_execute(query="TRUNCATE TABLE public.cur_processes")
        self.start_time = time.time()
        self.process_time = 0
        self.metadata = metadata
        self.agents_path = dict({})
        self.agents_state = dict({})
        for i in range(sum(self.metadata['agent_num'])):
            self.agents_path[i] = []
            self.agents_state[i] = False
        self.back_points = []
        self.back_points_stamp = time.time() - self.experiment_config.HYBRID_CAL_INTERVAL
        # For simplification, we define these two parameters for center to store the current backtracking path for
        # all agents, which should also be put into database
        self.cpt = ComputationUnit()

    def terminate(self):
        # 可以将未处理的请求用文件的形式暂存下来
        self._running = False
        if self.socket:
            self.socket.close()
        self.query_tool.clear_db_connection()

    def socket_communication(self):
        try:
            self.create_request_listener()  # create socket listener thread
            self.connect_with_agents()
        except Exception as e:
            print(e)
        # print("Communication channel is closed.")

    def create_request_listener(self):
        try:
            self.socket = socket(AF_INET, SOCK_STREAM)
            self.socket.bind((self.HOST, self.PORT))
            self.socket.listen()
        except Exception as e:
            print(e)
        # print("Socket is now listening.")

    def connect_with_agents(self):
        # listen函数实际是创建一个用于监听的独立线程
        # 使用listen可以同时建立多个和client的连接
        # accept函数则是返回一个连接实例，用conn标识
        # 这个实例可以理解为从监听线程中抽出来的，相当于确认监听到的信号，建立实际连接通道，并从中得到信息
        # 一直不accept，监听线程也会一直运行
        # 这里的while True是主线程(创立监听线程的父线程控制的)，也就是说父线程运行期间，不断的确认监听连接并处理收到的信息
        # 父线程无法在处理连接信息的同时并行的对存入队列中的请求进行处理(因为不能变成收到一个请求先处理让其他请求者等待)
        con_start_time = time.time()
        while self._running:
            conn, addr = self.socket.accept()
            # 必须为每一个连接建立一个线程，不然center无法在与一个agent连接的情况下处理其他连接
            # 使用线程池的好处是可以限制线程池大小，避免建立无限多的连接
            # 线程池中进程默认为后台线程，建立后无法通过其他手段干预或强制停止（是说无法在代码中操作）？
            self.con_thread_pool.submit(self.echo_agent, conn, addr)

            time_elapse = time.time() - con_start_time
            if time_elapse > self.experiment_config.timeout or sum(list(self.agents_state.values())) == len(
                    list(self.agents_state.keys())):
                self._running = False
                self.socket.close()
                break

    def echo_agent(self, conn, addr):
        # print("Connected by address: ", addr)

        try:
            temp_data = []
            while True:
                # self.socket.setblocking(0)
                # ready = select.select([self.socket], [], [], 60)
                data = conn.recv(1024*1024)
                # print(data.decode())
                if not data:
                    break
                data = data.decode()
                # print(data)

                if self.STATIC_INFO.END in data:
                    data = data[:data.find(self.STATIC_INFO.END)]
                    if data != "Data is received.":
                        temp_data.append(data)
                    break
                # 打印接收到的数据?
                # conn.sendall(data)

                if data == "Data is received.":
                    break
                else:
                    temp_data.append(data)

            data = ''.join(temp_data)
            # print("Receiving request data.")

            # conn.send("Request is received.".encode())  # 对agent的响应信息

            request_id = uuid.uuid1()
            self.resp_conditions[request_id] = Condition()

            self.after_receive_request(data, request_id)
            # print("uuid is:", request_id)
            # conn.send("Request is in queue.".encode())

            # 保证这里先运行,挂起等待才行

            if self.resp_conditions[request_id].acquire():

                # print("echo get response lock for request ", request_id)
                if request_id not in self.response_data.keys():
                    # print("Waiting for response data ready")
                    self.resp_conditions[request_id].wait()
                    # print("response data has been ready and notified the response thread.")
                elif 'data' not in self.response_data[request_id].keys():
                    # print("Waiting for response data ready")
                    self.resp_conditions[request_id].wait()
                    # print("response data has been ready and notified the response thread.")

                if self.response_data[request_id]['data']:
                    # conn.send("Data Ready.".encode())
                    resp_data = json.dumps(self.response_data[request_id]['data'])
                    conn.send(resp_data.encode())
                    # print('Has Sent Data Back To Drone.')
                else:
                    pass
                    # conn.send("Put is done.".encode())
                    # print('Has Update Data According To Drone.')
                conn.send("*".encode())
                self.response_data[request_id]['data_sent'] = True

                self.response_data[request_id].clear()
                self.response_data.pop(request_id)

                self.resp_conditions[request_id].release()
                self.resp_conditions.pop(request_id)

        except Exception as e:
            print("Exception arose when receiving request from agent!")
            print(e)

        conn.close()

    def after_receive_request(self, request, request_id):
        '''
        after_receive_request(由多个并行建立的request conn调用,作为多个并发的producer)
        process_request(一个consumer)
        producer与consumer同时操作request_queue这个资源
        :param request:
        :param request_id:
        :return:
        '''

        # Producer
        request = json.loads(request)
        request['uuid'] = request_id
        request['proc_id'] = 1

        req_time = None
        if request['RoW'] == 'R':
            req_time = request['request_time']
        else:
            req_time = request['sense_time']
        request['time_info'] = req_time

        # 注意在修改request_queue的时候加锁
        self.condition.acquire()

        # print("Add Lock To Request Queue.")

        if len(self.request_queue) == self.MAX_QUEUE_LEN:
            # print("Queue full, producer is waiting.")
            self.condition.wait()
            # print("Space in queue, Consumer notified the producer.")

        # 将新的请求记录插入self.request_queue以及cur_processes表,并在插入时保证顺序
        if len(self.request_queue) == 0:
            self.request_queue.insert(0, request)
            # print("Insert first request! ", len(self.request_queue))
        else:
            tmp_len = len(self.request_queue)
            for i in range(len(self.request_queue)):
                # 插入遵循以下原则:
                # 可插入的起始位置为列表中第一个PID不为0的位置，因为还存在在列表中且PID为0的记录意味着正在处理的任务
                if self.request_queue[i]['proc_id'] == 0:
                    continue
                else:
                    # 找到起始位置后根据TIME判断自己可以插入的位置，如果遇到TIME相同的则根据两条记录的读写属性判断应该按照什么顺序排序
                    # 如果是R_和R,则R_在R之后
                    # 如果是R_和W,则R_在W之后
                    # 如果是W_和R,则W_在R之前
                    # 如果是W_和W,则W_在W之后
                    if req_time > self.request_queue[i]['time_info']:
                        self.request_queue.insert(i, request)
                        break
                    elif req_time == self.request_queue[i]['time_info']:
                        if request['RoW'] == self.request_queue[i]['RoW'] or (
                                request['RoW'] == 'R' and self.request_queue[i]['RoW'] == 'W'):
                            continue
                        else:
                            self.request_queue.insert(i, request)
                            break
            if tmp_len == len(self.request_queue):
                # 说明经过上面的比较得知需要插在队尾
                self.request_queue.append(request)
            # print("Insert In Queue! ", len(self.request_queue))

        self.query_tool.safe_execute("INSERT INTO public.cur_processes VALUES "
                                     "({},{},'{}','{}','{}')".format(request['proc_id'], request['uav_id'],
                                                                     request['RoW'], time.strftime("%Y-%m-%d %H:%M:%S",
                                                                                                   time.localtime(
                                                                                                       request[
                                                                                                           'time_info'])),
                                                                     request['uuid']))
        # print("Request Insert Done!")
        # 由于cur_processes表中time_info表项类型为time,虽然支持这种语句的插入但只保留时刻,不保留日期
        # 改为timestamp类型的话可以保留日期和时刻

        # 如果插入时发现目前列表中没有PID为0的记录,则在插入结束后,将第一条写,或者前k条连续的读的记录PID均设为0
        if len(self.request_queue) > 0:
            if self.request_queue[0]['proc_id'] != 0:
                if self.request_queue[0]['RoW'] == 'W':
                    self.request_queue[0]['proc_id'] = 0
                    self.query_tool.safe_execute(
                        "UPDATE public.cur_processes SET proc_id = 0 WHERE req_uuid = '{}'".format(
                            self.request_queue[0]['uuid']))
                else:
                    for i in range(len(self.request_queue)):
                        if self.request_queue[i]['RoW'] == 'R':
                            self.request_queue[i]['proc_id'] = 0
                            self.query_tool.safe_execute(
                                "UPDATE public.cur_processes SET proc_id = 0 WHERE req_uuid = '{}'".format(
                                    self.request_queue[i]['uuid']))
                            continue
                        else:
                            break
        # print("PID update done!")

        self.condition.notify()
        self.condition.release()
        # print("Lock was released!")

        # return request_id

    def process_request_in_queue(self):
        # Consumer

        # 根据queue中收到的具体请求情况，对中心数据进行处理
        # 当需要数据更新的时候，针对不同情况，对所有相关数据进行处理（比如除了更新相应的view，还需要执行计算，更新状态信息）
        # 有一些计算或许可以通过直接在数据库中创建trigger处理
        self.process_time = 0
        p_start_time = time.clock()
        proc_start_time = time.time()
        db_operation_time = 0
        # 很难去除,因为发生在各种单元内除非所有的execute都返回一个执行时间参数并且都承接后减去,
        # 但有些运算模块里也用到了,再怎么把运算db开销传回来也很麻烦
        while self._running:

            self.condition.acquire()

            if len(self.request_queue) == 0:
                # print("Nothing in queue, consumer is waiting.")
                self.condition.wait(timeout=self.experiment_config.waittime)
                if len(self.request_queue) > 0:
                    # print("Producer added something to queue and notified the consumer.")
                    pass
                else:
                    # print("Processor end working.")
                    self._running = False
                    break

            # 取PID为0的requests

            merge_list = []
            i_list = []
            index_ = []
            j_list = []

            # print("current request queue:", self.request_queue)
            # bug: 完全一样的request在request_queue中重复出现两次,造成这里在已经处理完一次后第二次处理时报错
            for i in range(len(self.request_queue)):
                # print("p1.",len(self.request_queue))
                if self.request_queue[i]['proc_id'] == 0:
                    # print("process request ", i)
                    uuid = self.request_queue[i]['uuid']

                    # print("Process want to get response lock for request ", uuid)
                    self.resp_conditions[uuid].acquire()
                    # print("Process get response lock for request ", uuid)
                    # print("p2. acquire", uuid)

                    self.response_data[uuid] = {}
                    index_.append(i)
                    # 对每一条request,获取其对应的数据，或者更新相应的数据
                    # 这里比较关键的问题是处理需要并行读取的情况,怎么全部读取，然后分发，然后一起更新cur_processes
                    if self.request_queue[i]['RoW'] == 'R':
                        if 'Compute' in list(self.request_queue[i].keys()) and self.request_queue[i]['Compute']:
                            self.response_data[uuid]['data'] = None
                            if self.request_queue[i]['GoL'] == 'G':
                                try:
                                    if self.request_queue[i]['func'] == 'Dijkstra':
                                        grids = self.cpt.get_global_env_model(qt=self.query_tool)
                                        min_cost, path = self.cpt.dijkstra(Nodes=grids['nodes'],
                                                                           Edges=grids['edges'],
                                                                           src=self.request_queue[i]['loc_node_id'])
                                        self.response_data[uuid]['data'] = [min_cost, path]
                                    elif self.request_queue[i]['func'] == 'H_BoB_BT_Points':
                                        # if time.time() - self.back_points_stamp >= self.experiment_config.HYBRID_CAL_INTERVAL:
                                        grids = self.cpt.get_global_env_model(qt=self.query_tool)
                                        agents_pos = self.cpt.get_agents_distribution(qt=self.query_tool)
                                        view_map = GlobalViewMap(grid=grids, agents_pos=agents_pos)
                                        scale = (self.metadata['width'], self.metadata['height'])
                                        self.back_points = self.cpt.h_bob_bt_points(view_map, scale, None,
                                                                                    self.agents_path)
                                        # self.back_points_stamp = time.time()
                                        self.response_data[uuid]['data'] = [self.back_points]
                                    elif self.request_queue[i]['func'] == 'H_BoB_BT_Paths':
                                        loc_id = self.request_queue[i]['loc_node_id']
                                        scale = (self.metadata['width'], self.metadata['height'])
                                        cur_x = int(loc_id / scale[1])
                                        cur_y = int(loc_id % scale[1])
                                        grids = self.cpt.get_global_env_model(qt=self.query_tool)
                                        agents_pos = self.cpt.get_agents_distribution(qt=self.query_tool)
                                        view_map = GlobalViewMap(grid=grids, agents_pos=agents_pos)
                                        # back_points = self.request_queue[i]['args']['back_points']
                                        tar_x, tar_y, back_paths = self.cpt.h_bob_bt_paths(scale, view_map, cur_x,
                                                                                           cur_y,
                                                                                           self.back_points)
                                        # print("center back_paths:", back_paths)
                                        self.response_data[uuid]['data'] = [back_paths]
                                    self.response_data[uuid]['data_ready'] = True
                                    self.resp_conditions[uuid].notify()
                                    self.resp_conditions[uuid].release()
                                except Exception as e:
                                    print(e)
                                    self.resp_conditions[uuid].notify()
                                    self.resp_conditions[uuid].release()
                        else:
                            merge_list.append(uuid)
                            i_list.append(i)
                    else:
                        self.response_data[uuid]['data'] = None
                        if self.request_queue[i]['GoL'] == 'G':
                            if 'Compute' in list(self.request_queue[i].keys()) and self.request_queue[i]['Compute']:
                                if self.request_queue[i]['func'] == 'SetAgentsPath':
                                    if self.request_queue[i]['args']['back_paths'] is not None:
                                        self.agents_path[int(self.request_queue[i]['uav_id'])] = \
                                            self.request_queue[i]['args']['back_paths']
                                    else:
                                        self.agents_path[int(self.request_queue[i]['uav_id'])] = []
                                elif self.request_queue[i]['func'] == 'SetAgentsWorkState':
                                    self.agents_state[int(self.request_queue[i]['uav_id'])] = \
                                        self.request_queue[i]['args']['work_done']
                            else:
                                for w_sql in self.request_queue[i]['sql_list']:
                                    self.query_tool.safe_execute(w_sql)
                        else:
                            for j in range(len(self.request_queue[i]['view_index_list'])):
                                vi = self.request_queue[i]['view_index_list'][j]
                                if vi == 0:
                                    # drone_local_nodes
                                    for new_row in self.request_queue[i]['view_data_list'][j]:
                                        self.query_tool.safe_execute('UPDATE drone_local_nodes '
                                                                     'SET visit_count={},visited={},victims_num={},need_rescue={},node_type={} '
                                                                     'WHERE node_id = {} AND uav_id = {}'
                                                                     .format(new_row['VC'],
                                                                             new_row['V'],
                                                                             new_row['VN'],
                                                                             new_row['NR'],
                                                                             new_row['NT'],
                                                                             new_row['NID'],
                                                                             new_row['UID']
                                                                             ))
                                elif vi == 1:
                                    # drone_local_edges
                                    for new_row in self.request_queue[i]['view_data_list'][j]:
                                        self.query_tool.safe_execute(
                                            "UPDATE public.drone_local_edges SET distance={} WHERE edge_id ={}"
                                                .format(new_row['DIS'],
                                                        new_row['EID']))

                                elif vi == 2:
                                    # drone_self_info
                                    for new_row in self.request_queue[i]['view_data_list'][j]:
                                        self.query_tool.safe_execute("UPDATE public.drone_self_info "
                                                                     "SET loc_node_id={},view_range={}, "
                                                                     "load_num={},cur_electricity={}, "
                                                                     "flying_state={},cur_path_length={}, "
                                                                     "cur_resource_cost={} WHERE uav_id ={}".
                                                                     format(new_row['NID'],
                                                                            new_row['VR'],
                                                                            new_row['LN'],
                                                                            new_row['CE'],
                                                                            new_row['FS'],
                                                                            new_row['CL'],
                                                                            new_row['RC'],
                                                                            new_row['UID']))
                                elif vi == 3:
                                    # drone_charge_targets
                                    for new_row in self.request_queue[i]['view_data_list'][j]:
                                        self.query_tool.safe_execute("UPDATE public.drone_charge_targets "
                                                                     "SET is_inservice={}, cur_utilization={}, "
                                                                     "queue_length={}, dock_num={} WHERE station_id={}"
                                                                     .format(new_row['II'],
                                                                             new_row['CU'],
                                                                             new_row['QL'],
                                                                             new_row['DN'],
                                                                             new_row['SID']))
                                elif vi == 4:
                                    # drone_rescue_targets
                                    for new_row in self.request_queue[i]['view_data_list'][j]:
                                        self.query_tool.safe_execute("UPDATE public.drone_rescue_targets "
                                                                     "SET victims_num={}, load_demand_num={},"
                                                                     "is_completed={} WHERE target_id={}"
                                                                     .format(new_row['VN'],
                                                                             new_row['LDN'],
                                                                             new_row['IC'],
                                                                             new_row['TID']))
                                elif vi == 5:
                                    # drone_delivery_targets
                                    for new_row in self.request_queue[i]['view_data_list'][j]:
                                        self.query_tool.safe_execute("UPDATE public.drone_delivery_targets "
                                                                     "SET load_demand_num={}, is_completed={}"
                                                                     " WHERE target_id={}".format(new_row['LDN'],
                                                                                                  new_row['IC'],
                                                                                                  new_row['TID']))
                        # TODO: rescue and delivery targets maintaince is useless in searching task
                        # so we comment it temporary
                        # self.check_targets()
                        j_list.append(uuid)
                else:
                    break

            if len(j_list) > 0:
                for uuid in j_list:
                    # print("p3. write notify", uuid)
                    self.response_data[uuid]['data_ready'] = True
                    self.resp_conditions[uuid].notify()
                    self.resp_conditions[uuid].release()

            if len(merge_list) > 0:
                self.separate_views_data(i_list)
                # 如果是读操作，更新self.response_data[req_uuid].data中的数据为要返回的数据
                for uuid_ in merge_list:
                    self.response_data[uuid_]['data_ready'] = True
                    # print("p4. read notify", uuid_)
                    self.resp_conditions[uuid_].notify()
                    self.resp_conditions[uuid_].release()

            time.sleep(1)

            for i_ in reversed(index_):
                # self.response_data[uuid_].clear()
                # self.response_data.pop(uuid_)
                # print(len(self.request_queue))
                # print("index_ i_",i_)
                # print("uuid",uuid)

                del_ = self.request_queue.pop(i_)
                self.query_tool.safe_execute(
                    "DELETE FROM public.cur_processes WHERE req_uuid = '{}'".format(del_['uuid']))
            # print('Delete completed request!')

            # 如果是写操作，更新self.response_data[req_uuid].data中的数据为None
            # 更新self.response_data[req_uuid].data_ready = True
            # 使用while循环进行等待，等待connection将相应的数据发出，即self.response_data[req_uuid].data_sent=True
            # 从self.request_queue中移除相应数据

            # 分析self.request_queue中的剩余的请求，并将前n条连续读或者第一条写的PID置为0

            # print("After processing, ", len(self.request_queue))

            if len(self.request_queue) > 0:
                if self.request_queue[0]['proc_id'] != 0:
                    if self.request_queue[0]['RoW'] == 'W':
                        self.request_queue[0]['proc_id'] = 0
                        self.query_tool.safe_execute(
                            "UPDATE public.cur_processes SET proc_id = 0 WHERE req_uuid = '{}'".format(
                                self.request_queue[0]['uuid']))
                    else:
                        for i in range(len(self.request_queue)):
                            if self.request_queue[i]['RoW'] == 'R':
                                self.request_queue[i]['proc_id'] = 0
                                self.query_tool.safe_execute(
                                    "UPDATE public.cur_processes SET proc_id = 0 WHERE req_uuid = '{}'".format(
                                        self.request_queue[i]['uuid']))
                                continue
                            else:
                                break
            # print('Identify new request!')

            self.condition.notify()
            self.condition.release()

            # time_elapse = time.time() - proc_start_time
            # if time_elapse > self.experiment_config.timeout or sum(list(self.agents_state.values())) == len(
            #         list(self.agents_state.keys())):
            #     self._running = False

        end_time = time.clock()
        self.process_time = end_time - p_start_time
        if len(self.request_queue) > 0:
            with open('{}/LeftRequests.log'.format(log_dir), mode='w') as fw:
                while len(self.request_queue) > 0:
                    fw.write(str(self.request_queue.pop(0)) + '\n')

    def separate_views_data(self, i_list):

        for read_req_i in i_list:
            req = self.request_queue[read_req_i]
            uuid = req['uuid']
            data = []
            # TODO: if several read requests want to get the same view with different uav_id.
            # We can get the whole view by once and separate to different request, instead of select data in loop.
            # That means we must analysis the request in concurrent read list first.
            # This is only useful in current one-process-thread implementation.
            # For multiple parallel processing threads, even two are requesting for the same view, it will be
            # processed by two threads, so it is impossible for combination, but can happen at the same time.
            if req['GoL'] == 'G':
                for sql in req['sql_list']:
                    try:
                        data.append([])
                        self.query_tool.safe_execute(sql)
                        r_rows = self.query_tool.cur.fetchall()
                        colnames = [desc[0] for desc in self.query_tool.cur.description]
                        data[len(data) - 1].append(colnames)
                        data[len(data) - 1].append(r_rows)
                    except psycopg2.ProgrammingError as exc:
                        print(exc)
                        self.query_tool.conn.rollback()
                    except psycopg2.InterfaceError as exc:
                        print(exc)
                        self.query_tool.conn = psycopg2.connect(database=self.query_tool.database,
                                                                user=self.query_tool.user, password=
                                                                self.query_tool.password, host=self.query_tool.host,
                                                                port=self.query_tool.port)
                        self.query_tool.cur = self.query_tool.conn.cursor()
            else:
                for j in range(len(req['view_index_list'])):
                    try:
                        vi = req['view_index_list'][j]
                        data.append([])
                        if vi == 0:
                            # drone_local_nodes
                            self.query_tool.safe_execute("SELECT * FROM public.drone_local_nodes WHERE uav_id={}"
                                                         .format(req['uav_id']))
                        elif vi == 1:
                            # drone_local_edges
                            self.query_tool.safe_execute("SELECT * FROM public.drone_local_edges WHERE uav_id={}"
                                                         .format(req['uav_id']))
                        elif vi == 2:
                            # drone_self_info
                            self.query_tool.safe_execute("SELECT * FROM public.drone_self_info WHERE uav_id={}"
                                                         .format(req['uav_id']))
                        elif vi == 3:
                            # drone_charge_targets
                            self.query_tool.safe_execute("SELECT * FROM public.drone_charge_targets WHERE uav_id={}"
                                                         .format(req['uav_id']))
                        elif vi == 4:
                            # drone_rescue_targets
                            self.query_tool.safe_execute("SELECT * FROM public.drone_rescue_targets WHERE uav_id={}"
                                                         .format(req['uav_id']))
                        elif vi == 5:
                            # drone_delivery_targets
                            self.query_tool.safe_execute("SELECT * FROM public.drone_delivery_targets WHERE uav_id={}"
                                                         .format(req['uav_id']))
                        elif vi == 6:
                            # drone_local_neighbors
                            self.query_tool.safe_execute("SELECT * FROM public.drone_local_neighbors WHERE uav_id={}"
                                                         .format(req['uav_id']))

                        r_rows = self.query_tool.cur.fetchall()
                        colnames = [desc[0] for desc in self.query_tool.cur.description]
                        data[len(data) - 1].append(colnames)
                        data[len(data) - 1].append(r_rows)
                    except psycopg2.ProgrammingError as exc:
                        print(exc)
                        self.query_tool.conn.rollback()
                    except psycopg2.InterfaceError as exc:
                        print(exc)
                        self.query_tool.conn = psycopg2.connect(database=self.query_tool.database,
                                                                user=self.query_tool.user, password=
                                                                self.query_tool.password, host=self.query_tool.host,
                                                                port=self.query_tool.port)
                        self.query_tool.cur = self.query_tool.conn.cursor()

            self.response_data[uuid]['data'] = data

    def check_state(self):
        time.sleep(self.experiment_config.center_check_interval)
        while self._running:

            # drawing current state of all drones and global view map

            # check search_coverage task state
            # and update the search_coverage_task, search_coverage_history_state tables

            self.query_tool.safe_execute(
                "SELECT area_id, responsible_fleet_id FROM public.search_coverage_task WHERE start_time IS NOT NULL")

            rows = self.query_tool.cur.fetchall()
            for row in rows:

                aid = row[0]
                fid = row[1]
                self.query_tool.safe_execute("SELECT AVG(cur_path_length) AS avg_step "
                                             "FROM public.drones_cur_state, public.drones_config "
                                             "WHERE drones_config.uav_id=drones_cur_state.uav_id AND fleet_id={}".format(
                    fid))
                move_step = self.query_tool.cur.fetchall()[0][0]
                self.query_tool.safe_execute("SELECT COUNT(node_id) FROM public.grid_nodes "
                                             "WHERE node_type=0 AND visited=FALSE ")
                unvisited_num = self.query_tool.cur.fetchall()[0][0]
                self.query_tool.safe_execute("SELECT COUNT(node_id) FROM public.grid_nodes "
                                             "WHERE node_type=1 or node_type=2")
                other_num = self.query_tool.cur.fetchall()[0][0]
                self.query_tool.safe_execute("SELECT COUNT(node_id) FROM public.grid_nodes")
                total_num = self.query_tool.cur.fetchall()[0][0]
                coverage_ratio = 1 - float(unvisited_num) / float(total_num - other_num)
                self.query_tool.safe_execute("SELECT COUNT(public.drones_cur_state.uav_id) "
                                             "FROM public.drones_cur_state, public.drones_config "
                                             "WHERE drones_config.uav_id = drones_cur_state.uav_id "
                                             "AND flying_state=1 AND fleet_id={} ".format(fid))
                on_working_num = self.query_tool.cur.fetchall()[0][0]
                self.query_tool.safe_execute("SELECT COUNT(public.drones_cur_state.uav_id) "
                                             "FROM public.drones_cur_state, public.drones_config "
                                             "WHERE drones_config.uav_id = drones_cur_state.uav_id "
                                             "AND fleet_id={} ".format(fid))
                total_num = self.query_tool.cur.fetchall()[0][0]
                self.query_tool.safe_execute("SELECT COUNT(public.drones_cur_state.uav_id) "
                                             "FROM public.drones_cur_state, public.drones_config "
                                             "WHERE drones_config.uav_id = drones_cur_state.uav_id "
                                             "AND flying_state=5 AND fleet_id={} ".format(fid))
                done_working_num = self.query_tool.cur.fetchall()[0][0]
                working_uav_ratio = float(on_working_num) / float(total_num)
                cur_t = time.time()
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(cur_t))
                cur_working_time = cur_t - self.start_time
                iscompleted = not bool(unvisited_num)

                if iscompleted:
                    self.query_tool.safe_execute("UPDATE public.drones_cur_state "
                                                 "SET flying_state=5 "
                                                 "WHERE uav_id in "
                                                 "(SELECT public.drones_cur_state.uav_id "
                                                 "FROM public.drones_cur_state, public.drones_config "
                                                 "WHERE drones_cur_state.uav_id = drones_config.uav_id AND fleet_id = {})".format(
                        fid))

                iscompleted = iscompleted or (done_working_num == total_num)
                self.query_tool.safe_execute("INSERT INTO public.search_coverage_history_states "
                                             "VALUES ({},'{}',{},{},{},'{}s',{})".format(aid, timestamp, move_step,
                                                                                         coverage_ratio,
                                                                                         working_uav_ratio,
                                                                                         cur_working_time,
                                                                                         iscompleted))
                if iscompleted:
                    self.query_tool.safe_execute(
                        "UPDATE public.search_coverage_task "
                        "SET end_coverage_ratio={},end_time='{}' "
                        "WHERE area_id={} and responsible_fleet_id={}".format(
                            coverage_ratio, timestamp, aid, fid))
            # check rescue_support task state
            # and update the rescue_support_task, rescue_support_task_targets, rescue_support_cur_state tables
            # TODO: realizing the check process for rescue_support_task
            # 检查当前正在进行的rescue_support任务的area

            # 对每一个有任务的area,检查area区域内符合条件的任务点,新的任务点插入rescue_support_task_targets,
            # 以及rescue_support_cur_state,并更新rescue_support_task的target_num
            # 如果可以的话，对于rescue_support_cur_state中未分配给无人机的任务点进行任务分配

            # 统计rescue_support_cur_state中已分配出去的target的完成情况,如果is_completed=True,则更新相应target在
            # rescue_support_task_targets表中的over_time.
            _, rows = self.query_tool.sql_execute("SELECT target_id,cur_timestamp FROM public.rescue_support_cur_state "
                                                  "WHERE is_allocated=True and is_completed=True")
            for row in rows:
                tar_id = row[0]
                timestamp = row[1]
                self.query_tool.sql_execute("UPDATE public.rescue_support_task_targets "
                                            "SET over_time ='{}' "
                                            "WHERE target_id={}".format(timestamp, tar_id))
            complete_count = len(rows)
            _, r = self.query_tool.sql_execute("SELECT targets_num FROM public.rescue_support_task "
                                               "WHERE area_id=0")
            if complete_count == r[0][0]:
                self.query_tool.sql_execute("UPDATE public.rescue_support_task "
                                            "SET end_time='{}', end_completed_ratio={}".format(timestamp, 1))

            # 如果同area下任务0已结束,则任务1的任务数不会再增长,这种情况下如果所有的target都有overtime了,
            # 更新rescue_support_task的end_time以及end_completed_ratio

            # 如果负责任务1的所有飞机都处于5状态,则更新rescue_support_task的end_time以及end_completed_ratio

            # self.query_tool.safe_execute("SELECT area_id,responsible_fleet_id "
            #                             "FROM public.rescue_support_task "
            #                             "WHERE start_time IS NOT NULL")
            # rows = self.query_tool.cur.fetchall()

            time.sleep(self.experiment_config.center_check_interval)

    def check_targets(self):
        # 检查符合条件的rescue_targets
        col_names, re_tars = self.query_tool.sql_execute("SELECT * FROM public.grid_nodes "
                                                         "WHERE need_rescue=TRUE or (victims_num>0 and node_type=3)")
        _, cur_tars = self.query_tool.sql_execute("SELECT target_id FROM public.rescue_support_task_targets")

        n_tars = []
        for row in re_tars:
            tar_id = row[col_names.index('node_id')]
            n_tars.append(tar_id)
            victims_num = row[col_names.index('victims_num')]
            load_demand_num = 0
            is_allocated = True
            is_completed = False
            responsible_uav_id = 2
            cur_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            _, re = self.query_tool.sql_execute("SELECT * FROM public.rescue_support_task_targets "
                                                "WHERE target_id = {}".format(tar_id))
            if len(re) == 0:
                # 更新rescue_support_task中的targets_num
                self.query_tool.safe_execute("UPDATE public.rescue_support_task "
                                             "SET targets_num=targets_num+1 "
                                             "WHERE area_id = 0")
                # 更新rescue_support_targets表中的记录
                self.query_tool.safe_execute("INSERT INTO "
                                             "public.rescue_support_task_targets(area_id, target_id, find_time, over_time)"
                                             "VALUES (0, {}, '{}', null)".format(tar_id, cur_timestamp))
                # 更新rescue_support_cur_state表中的记录
                self.query_tool.safe_execute("INSERT INTO "
                                             "public.rescue_support_cur_state "
                                             "VALUES(0,{},{},{},{},{},{},'{}')".format(
                    tar_id, victims_num, load_demand_num, is_allocated, is_completed, responsible_uav_id, cur_timestamp
                ))
        for row in cur_tars:
            if row[0] not in n_tars:
                victims_num = 0
                load_demand_num = 0
                cur_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                # 在环境不会自己变化的时候,这种情况只发生在任务完成时,改变了rescue位置的victims_number或者need_rescue状态
                # # 更新rescue_support_task中的targets_num
                # self.query_tool.sql_execute("UPDATE public.rescue_support_task "
                #                             "SET targets_num=targets_num-1"
                #                             "WHERE area_id = 0")
                # 更新rescue_support_targets表中的记录
                self.query_tool.safe_execute("UPDATE public.rescue_support_task_targets "
                                             "SET over_time='{}'"
                                             "WHERE target_id ={}".format(cur_timestamp, row[0]))
                # 更新rescue_support_cur_state表中的记录
                self.query_tool.safe_execute("UPDATE public.rescue_support_cur_state "
                                             "SET victims_num={},load_demand_num={},is_completed=true, cur_timestamp='{}' "
                                             "WHERE target_id={} and area_id=0"
                    .format(
                    victims_num, load_demand_num, cur_timestamp, row[0]
                ))

        # 检查符合条件的delivery_targets
        col_names, re_tars = self.query_tool.sql_execute("SELECT * FROM public.grid_nodes "
                                                         "WHERE victims_num>{}".format(self.experiment_config.S_max))
        _, cur_tars = self.query_tool.sql_execute("SELECT target_id FROM public.delivery_task_targets")

        n_tars = []
        for row in re_tars:
            tar_id = row[col_names.index('node_id')]
            n_tars.append(tar_id)
            load_demand_num = 1
            is_allocated = True
            is_completed = False
            responsible_uav_id = 3
            cur_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            _, re = self.query_tool.sql_execute("SELECT * FROM public.delivery_task_targets "
                                                "WHERE target_id = {}".format(tar_id))
            if len(re) == 0:
                # 更新rescue_support_task中的targets_num
                self.query_tool.safe_execute("UPDATE public.delivery_task "
                                             "SET targets_num=targets_num+1"
                                             " WHERE area_id = 0")
                # 更新rescue_support_targets表中的记录
                self.query_tool.safe_execute("INSERT INTO "
                                             "public.delivery_task_targets(area_id, target_id, find_time, over_time)"
                                             "VALUES (0, {}, '{}', null)".format(tar_id, cur_timestamp))
                # 更新rescue_support_cur_state表中的记录
                self.query_tool.safe_execute("INSERT INTO public.delivery_cur_state"
                                             " VALUES(0,{},{},{},{},{},'{}')".format(
                    tar_id, load_demand_num, is_allocated, is_completed, responsible_uav_id, cur_timestamp
                ))
        for row in cur_tars:
            if row[0] not in n_tars:
                load_demand_num = 1
                cur_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                # 在环境不会自己变化的时候,这种情况不会发生
                # 更新delivery_task中的targets_num
                self.query_tool.safe_execute("UPDATE public.delivery_task "
                                             "SET targets_num=targets_num-1"
                                             " WHERE area_id = 0")
                # 更新rescue_support_targets表中的记录
                self.query_tool.safe_execute("DELETE FROM public.delivery_task_targets "
                                             "WHERE target_id ={} and area_id=0".format(row[0]))
                # 更新rescue_support_cur_state表中的记录
                self.query_tool.safe_execute("DELETE FROM public.delivery_cur_state "
                                             "WHERE target_id={} and area_id=0"
                                             .format(row[0]))

    # TODO: 如center与agent处于平等交互地位，即center不仅仅是被动接收agent的请求，同时可以主动建立请求，则需要再建立相应的新的连接
    def create_request_connection(self):
        pass

    def before_send_request(self):
        pass


class ComputationUnit:

    def __init__(self):
        pass

    @staticmethod
    def get_global_env_model(qt):
        qt.safe_execute("SELECT * FROM public.nodes_config ORDER BY node_id ASC")
        loc_rows = qt.cur.fetchall()
        loc_col_names = [desc[0] for desc in qt.cur.description]
        qt.safe_execute("SELECT * FROM public.grid_nodes ORDER BY node_id ASC")
        info_rows = qt.cur.fetchall()
        info_col_names = [desc[0] for desc in qt.cur.description]
        grids = dict({})
        grids['nodes'] = {}
        for i in range(len(loc_rows)):
            x = int(loc_rows[i][loc_col_names.index('pos_x')])
            y = int(loc_rows[i][loc_col_names.index('pos_y')])
            id = int(loc_rows[i][loc_col_names.index('node_id')])
            node_type = int(info_rows[id][info_col_names.index('node_type')])
            visited = bool(info_rows[id][info_col_names.index('visited')])
            victims_num = int(info_rows[id][info_col_names.index('victims_num')])
            need_rescue = bool(info_rows[id][info_col_names.index('need_rescue')])
            grids['nodes'][id] = Point(nid=id, pos_x=x, pos_y=y, node_type=node_type, victims_num=victims_num,
                                       need_rescue=need_rescue, visited=visited)
        qt.safe_execute("SELECT * FROM public.grid_edges ORDER BY edge_id ASC")
        edge_rows = qt.cur.fetchall()
        edge_col_names = [desc[0] for desc in qt.cur.description]
        grids['edges'] = {}
        for j in range(len(edge_rows)):
            from_p = int(edge_rows[j][edge_col_names.index('from_id')])
            to_p = int(edge_rows[j][edge_col_names.index('to_id')])
            eid = int(edge_rows[j][edge_col_names.index('edge_id')])
            dis = int(edge_rows[j][edge_col_names.index('distance')])
            if (grids['nodes'][from_p].danger_level == 1 and not grids['nodes'][to_p].blocked) \
                    or (grids['nodes'][to_p].danger_level == 1 and not grids['nodes'][from_p].blocked):
                dis = len(grids['nodes'])
            grids['edges'][str(from_p) + '_' + str(to_p)] = Edge(eid=eid, from_p=from_p, to_p=to_p, distance=dis)
        return grids

    @staticmethod
    def get_agents_distribution(qt):
        qt.safe_execute("SELECT uav_id, loc_node_id FROM public.drones_cur_state ORDER BY loc_node_id ASC")
        distribution = qt.cur.fetchall()
        dis_name = [desc[0] for desc in qt.cur.description]
        agents_pos = dict({})
        for i in range(len(distribution)):
            loc = int(distribution[i][dis_name.index('loc_node_id')])
            uid = int(distribution[i][dis_name.index('uav_id')])
            agents_pos[loc] = uid
        return agents_pos

    @staticmethod
    def dijkstra(Nodes, Edges, src):
        visited = {src: 0}  # 包含所有已添加的点,并且key-value对表示key对应的点到initial点(即self.cur_NID)的最小距离
        h = [(0, src)]
        path = {}  # path[v]=a,代表到达v之前的一个点是a,需要回溯得到整个路径

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

    @staticmethod
    def h_bob_bt_points(view_map, scale, agents_pos, agents_path):
        return find_backtracking_points(view_map, scale, agents_pos, agents_path)

    @staticmethod
    def h_bob_bt_paths(scale, view_map, cur_x, cur_y, back_points):
        target_x, target_y, back_path = find_shortest_backtracking_path(scale, view_map, cur_x, cur_y, back_points)
        return target_x, target_y, back_path


class Ggrid(tk.Tk, object):

    def __init__(self, grids, agents_info):
        super(Ggrid, self).__init__()
        self.staticInfo = StaticInfo()
        self.exp_Info = ExperimentConfig()
        self.action_space = [(0, 1, 1), (0, -1, 1), (-1, 0, 1), (1, 0, 1), (0, 0, 1), (0, 0, 0)]
        self.n_actions = len(self.action_space)
        self.title('Global Environment Model')
        self.grids = grids
        self.map_w = grids['width']
        self.map_h = grids['height']
        self.agents_loc = agents_info[0]
        self.agents_e = agents_info[1]
        self.agents_f = agents_info[2]
        self.geometry('{0}x{1}'.format(self.map_w * self.staticInfo.UNIT, self.map_h * self.staticInfo.UNIT))
        self._build_ggrid()

    def _build_ggrid(self):
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
                j = len(self.grid_block[i]) - 1
                if self.grids['nodes'][i][j].danger_level == 1:
                    colorval = "#%02x%02x%02x" % (255, 215, 0)
                else:
                    colorval = "#%02x%02x%02x" % (34, 139, 34)
                block = self.canvas.create_rectangle((x, y, x + self.staticInfo.UNIT, y - self.staticInfo.UNIT),
                                                     fill=colorval, outline='gray', disabledfill='gray')
                self.grid_block[len(self.grid_block) - 1].append(block)
                if self.grids['nodes'][i][j].visited:
                    mark_fill = 'red'
                else:
                    mark_fill = colorval
                mark = self.canvas.create_oval((x + self.staticInfo.UNIT / 2 - self.staticInfo.UNIT / 32,
                                                y - self.staticInfo.UNIT / 2 - self.staticInfo.UNIT / 32,
                                                x + self.staticInfo.UNIT / 2 + self.staticInfo.UNIT / 32,
                                                y - self.staticInfo.UNIT / 2 + self.staticInfo.UNIT / 32),
                                               fill=mark_fill, outline=colorval, disabledfill=colorval,
                                               disabledoutline=colorval)
                self.grid_mark[len(self.grid_mark) - 1].append(mark)

        # create origin(原点)
        origin = np.array([self.staticInfo.UNIT / 2, self.staticInfo.UNIT * self.map_h - self.staticInfo.UNIT / 2])

        # create ordinary nodes, obstacle and charging station in env
        self.stats = {}
        self.vbs = {}
        for i in range(self.map_w):
            for j in range(self.map_h):
                if self.grids['nodes'][i][j].is_charge_p:
                    # charging station
                    stat_center = origin + np.array([self.staticInfo.UNIT * i, self.staticInfo.UNIT * (-j)])
                    p1 = stat_center + np.array([0, -self.staticInfo.UNIT / 4])
                    p2 = stat_center + np.array([-self.staticInfo.UNIT / 4, self.staticInfo.UNIT / 4])
                    p3 = stat_center + np.array([self.staticInfo.UNIT / 4, self.staticInfo.UNIT / 4])
                    stat = self.canvas.create_polygon(
                        (p1[0], p1[1], p2[0], p2[1], p3[0], p3[1]),
                        fill='black', disabledfill='gray')
                    self.stats[(i, j)] = stat
                elif self.grids['nodes'][i][j].blocked:
                    # obstacle
                    self.canvas.itemconfig(self.grid_block[i][j], fill='black')
                else:
                    # ordinary node
                    n_center = origin + np.array([self.staticInfo.UNIT * i, self.staticInfo.UNIT * (-j)])
                    p1 = n_center + np.array([-self.staticInfo.UNIT / 2, self.staticInfo.UNIT / 2])
                    p2 = n_center + np.array([-self.staticInfo.UNIT / 4, self.staticInfo.UNIT / 4])
                    if self.grids['nodes'][i][j].need_rescue or self.grids['nodes'][i][
                        j].victims_num > self.exp_Info.S_max:
                        fill = 'red'
                    else:
                        fill = 'black'
                    block = self.canvas.create_rectangle((p1[0], p1[1], p2[0], p2[1]), fill='white',
                                                         disabledfill='gray', disabledoutline='gray')
                    text = self.canvas.create_text((p1[0] + self.staticInfo.UNIT / 8, p1[1] - self.staticInfo.UNIT / 8),
                                                   text='{}'.format(self.grids['nodes'][i][j].victims_num),
                                                   fill=fill, disabledfill='gray')
                    self.vbs[(i, j)] = {'block': block, 'num': text}

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

        # pack all
        self.canvas.pack()

    def step(self, new_grids, new_locs, new_e):
        origin = np.array([self.staticInfo.UNIT / 2, self.staticInfo.UNIT * self.map_h - self.staticInfo.UNIT / 2])
        # Update grids
        for i in range(self.map_w):
            for j in range(self.map_h):
                if new_grids['nodes'][i][j].is_charge_p:
                    # TODO: update charging station, we assume that there are no change of charging station now
                    if not ((i, j) in self.stats):
                        stat_center = origin + np.array([self.staticInfo.UNIT * i, self.staticInfo.UNIT * (-j)])
                        p1 = stat_center + np.array([0, -self.staticInfo.UNIT / 4])
                        p2 = stat_center + np.array([-self.staticInfo.UNIT / 4, self.staticInfo.UNIT / 4])
                        p3 = stat_center + np.array([self.staticInfo.UNIT / 4, self.staticInfo.UNIT / 4])
                        new_stat = self.canvas.create_polygon(
                            (p1[0], p1[1], p2[0], p2[1], p3[0], p3[1]),
                            fill='black', disabledfill='gray')
                        self.stats[(i, j)] = new_stat
                        if (i, j) in self.vbs:
                            self.canvas.delete(self.vbs[(i, j)]['block'])
                            self.canvas.delete(self.vbs[(i, j)]['num'])
                elif new_grids['nodes'][i][j].blocked:
                    # obstacle
                    self.canvas.itemconfig(self.grid_block[i][j], fill='black')
                    self.canvas.itemconfig(self.grid_mark[i][j], fill='black', outline='black')
                    if (i, j) in self.vbs:
                        self.canvas.delete(self.vbs[(i, j)]['block'])
                        self.canvas.delete(self.vbs[(i, j)]['num'])
                    if (i, j) in self.stats:
                        self.canvas.delete(self.stats[(i, j)])
                else:
                    # ordinary node
                    if new_grids['nodes'][i][j].danger_level == 1:
                        colorval = "#%02x%02x%02x" % (255, 215, 0)
                    else:
                        colorval = "#%02x%02x%02x" % (34, 139, 34)
                    self.canvas.itemconfig(self.grid_block[i][j], fill=colorval)
                    if new_grids['nodes'][i][j].visited:
                        self.canvas.itemconfig(self.grid_mark[i][j], fill='red')
                    else:
                        self.canvas.itemconfig(self.grid_mark[i][j], fill=colorval, outline=colorval)
                    if (i, j) in self.vbs:
                        if new_grids['nodes'][i][j].need_rescue or new_grids['nodes'][i][
                            j].victims_num > self.exp_Info.S_max:
                            fill = 'red'
                        else:
                            fill = 'black'
                        self.canvas.itemconfig(self.vbs[(i, j)]['num'],
                                               text='{}'.format(new_grids['nodes'][i][j].victims_num),
                                               fill=fill)
                    else:
                        n_center = origin + np.array([self.staticInfo.UNIT * i, self.staticInfo.UNIT * (-j)])
                        p1 = n_center + np.array([-self.staticInfo.UNIT / 2, self.staticInfo.UNIT / 2])
                        p2 = n_center + np.array([-self.staticInfo.UNIT / 4, self.staticInfo.UNIT / 4])
                        if self.grids['nodes'][i][j].need_rescue or new_grids['nodes'][i][
                            j].victims_num > self.exp_Info.S_max:
                            fill = 'red'
                        else:
                            fill = 'black'
                        block = self.canvas.create_rectangle((p1[0], p1[1], p2[0], p2[1]), fill='white',
                                                             disabledfill='gray', disabledoutline='gray')
                        text = self.canvas.create_text(
                            (p1[0] + self.staticInfo.UNIT / 8, p1[1] - self.staticInfo.UNIT / 8),
                            text='{}'.format(self.grids['nodes'][i][j].victims_num),
                            fill=fill, disabledfill='gray')
                        self.vbs.append({'pos': (i, j), 'block': block, 'num': text})

        s = []
        s_ = []
        for i, ag in enumerate(self.agents):
            x0, y0, x1, y1 = self.canvas.bbox(ag['circle'])
            coor = [(x0 + x1) / 2, (y0 + y1) / 2]
            s.append([math.floor(int(coor[0]) / int(self.staticInfo.UNIT)),
                      math.floor((self.map_h * self.staticInfo.UNIT - int(coor[1])) / self.staticInfo.UNIT)])
            self.canvas.itemconfig(self.grid_mark[s[i][0]][s[i][1]], state='normal')
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
            s_.append([new_locs[i][0], new_locs[i][1]])
        return s_


def get_current_data(qt, width, height, W_, C_):
    qt.safe_execute("SELECT * FROM public.nodes_config ORDER BY node_id ASC")
    loc_rows = qt.cur.fetchall()
    loc_col_names = [desc[0] for desc in qt.cur.description]
    qt.safe_execute("SELECT * FROM public.grid_nodes ORDER BY node_id ASC")
    info_rows = qt.cur.fetchall()
    info_col_names = [desc[0] for desc in qt.cur.description]
    grids = {}
    grids['width'] = width
    grids['height'] = height
    grids['nodes'] = []
    for i in range(width):
        grids['nodes'].append([])
        for j in range(height):
            grids['nodes'][i].append(j)
    for i in range(len(loc_rows)):
        x = int(loc_rows[i][loc_col_names.index('pos_x')])
        y = int(loc_rows[i][loc_col_names.index('pos_y')])
        id = int(loc_rows[i][loc_col_names.index('node_id')])
        node_type = int(info_rows[id][info_col_names.index('node_type')])
        visited = bool(info_rows[id][info_col_names.index('visited')])
        victims_num = int(info_rows[id][info_col_names.index('victims_num')])
        need_rescue = bool(info_rows[id][info_col_names.index('need_rescue')])
        grids['nodes'][x][y] = Point(nid=id, pos_x=x, pos_y=y, node_type=node_type, victims_num=victims_num,
                                     need_rescue=need_rescue, visited=visited)

    qt.safe_execute("SELECT * FROM public.drones_cur_state ORDER BY uav_id ASC")
    drone_infos = qt.cur.fetchall()
    drone_col_names = [desc[0] for desc in qt.cur.description]
    cur_pos = []
    cur_e = []
    cur_f = []
    for info in drone_infos:
        uid = int(info[drone_col_names.index('uav_id')])
        nid = int(info[drone_col_names.index('loc_node_id')])
        x = int(loc_rows[nid][loc_col_names.index('pos_x')])
        y = int(loc_rows[nid][loc_col_names.index('pos_y')])
        cur_pos.append([x, y])
        e = float(info[drone_col_names.index('cur_electricity')])
        qt.safe_execute("SELECT max_electricity,fleet_id FROM public.drones_config WHERE uav_id={}".format(uid))
        resp = qt.cur.fetchall()
        max_e = float(resp[0][0])
        new_f = int(resp[0][1])
        if e >= max_e * (1 - W_):
            new_e = 0
        elif max_e * (1 - C_) <= e < max_e * (1 - W_):
            new_e = 1
        else:
            new_e = 2
        cur_e.append(new_e)
        cur_f.append(new_f)
    return grids, cur_pos, cur_e, cur_f


def render_global_views(cur_center, width, height, W_, C_, timeout):
    qt = QueryTool(database='multiAgents')
    start_time = time.time()
    grids, cur_pos, cur_e, cur_f = get_current_data(qt, width, height, W_, C_)
    view_window = Ggrid(grids=grids, agents_info=(cur_pos, cur_e, cur_f))

    while True:
        time.sleep(0.1)
        new_grids, cur_pos, cur_e, _ = get_current_data(qt, width, height, W_, C_)
        s_ = view_window.step(new_grids, cur_pos, cur_e)
        view_window.update_idletasks()
        view_window.update()
        time_elapse = time.time() - start_time

        if time_elapse > timeout or sum(list(cur_center.agents_state.values())) == len(
                list(cur_center.agents_state.keys())):
            break
    qt.clear_db_connection()


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

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    yappi.clear_stats()
    yappi.set_clock_type("wall")
    yappi.start()
    # cpu clock by default, we also can use wall clock (inncluding thread waiting time)

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

    dg = GlobalDataInitializer(agent_num=metadata['agent_num'],
                               map_width=metadata['width'],
                               map_height=metadata['height'],
                               charge_num=metadata['charge_num'],
                               danger_num=metadata['danger_num'],
                               charge_pos_list=metadata['charge_pos_list'],
                               obstacle_num=metadata['obstacle_num'],
                               db_used=True,
                               view_range=metadata['view_range'],
                               sense_range=metadata['sense_range']
                               )
    dg.initNewMapViews()
    dg.initNewAgentViews()
    dg.initNewTaskViews()
    dg.ClearDBInitializer()

    dir_name = str(metadata['width']) + '_' + str(metadata['height']) + '_' + str(
        sum(metadata['agent_num'])) + '_' + metadata['time_tag'] + '_' + str(metadata['view_range'])
    root = os.path.abspath(os.path.dirname(os.getcwd()) + os.path.sep + ".")
    log_dir = os.path.join(os.path.join(root,'log'),dir_name)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    center = Center(metadata)

    process_thread = Thread(target=center.process_request_in_queue)
    process_thread.setName("process_thread")
    process_thread.start()  # process thread
    proc_pid = process_thread.ident
    print("process thread {}.".format(proc_pid))

    # TODO: check_thread used for checking rescue & delivery & searching completion state and update the db
    # task state table is useless now in searching task, we don't used it to identify the task status
    # and it is time-consuming to maintain task status in db for center
    # check_thread = Thread(target=center.check_state)
    # check_thread.start()  # check thread

    socket_thread = Thread(target=center.socket_communication)
    socket_thread.setName("communication_thread")
    socket_thread.start()  # socket thread
    comm_pid = socket_thread.ident
    print("comm thread {}.".format(comm_pid))

    start_clock = time.clock()
    start_time = time.time()

    # Code for visualization of data in the center DB
    # W_ = center.experiment_config.W_Threshold
    # C_ = center.experiment_config.C_Threshold
    # timeout = center.experiment_config.timeout
    # render_global_views(center, metadata['width'], metadata['height'], W_, C_, timeout)

    process_thread.join()  # waiting for ending processing
    center.terminate()
    socket_thread.join()
    end_clock = time.clock()
    end_time = time.time()

    func_stats = yappi.get_func_stats()
    func_stats.save('{}/center_func.out'.format(log_dir), 'PSTAT')
    thread_stats = yappi.get_thread_stats()
    thread_stats.sort(sort_type='scnt').print_all(
        out=open('{}/center_thread.out'.format(log_dir), 'w'))
    yappi.stop()
    yappi.clear_stats()

    fw = open('{}/center_statistic.txt'.format(log_dir), mode='w')
    with fw:
        fw.write("center processing cpu clock: {}.\n".format(center.process_time))
        fw.write("center total cpu clock: {}.\n".format(end_clock - start_clock))
        fw.write("center total running time: {}.\n".format(end_time - start_time))
        fw.flush()

    # Old Codes

    # Initializing by reading the configuration file
    # with open(file='../data/metadata.json', mode='r') as fr:
    #     metadata = json.loads("".join(fr.readlines()))['metadata']
    #     dg = GlobalDataInitializer(agent_num=metadata['agent_num'],
    #                                map_width=metadata['width'],
    #                                map_height=metadata['height'],
    #                                charge_num=metadata['charge_num'],
    #                                danger_num=metadata['danger_num'],
    #                                charge_pos_list=metadata['charge_pos_list'],
    #                                obstacle_num=metadata['obstacle_num'],
    #                                db_used=True
    #                                )
    #     dg.initNewMapViews()
    #     dg.initNewAgentViews()
    #     dg.initNewTaskViews()
    #     dg.ClearDBInitializer()

    # The following code in the main thread (when waiting for the end of two child threads)
    # will increase the cpu clock for computing cost in if clause
    # start_clock = time.clock()
    # start_time = time.time()
    # while True:
    #     time_elapse = time.time() - start_time
    #     if time_elapse > center.experiment_config.timeout or sum(list(center.agents_state.values())) == len(
    #             list(center.agents_state.keys())):
    #         break
    # end_clock = time.clock()
