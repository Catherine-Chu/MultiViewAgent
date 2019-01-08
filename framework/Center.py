# -*- coding:utf-8 -*-
import sys

sys.path.append('../')
from framework.CustomExceptions import *
from framework.StaticConsensus import *
from framework.QueryTool import *
from scripts.DataGenerator import *

import time
import uuid
from socket import *
import threading
from threading import *
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, PriorityQueue
import heapq
import json


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

    def __init__(self, ):
        self._running = True  # used to control the termination of center process and its child threads.
        self.STATIC_INFO = StaticInfo()  # static consensus info between agents and center
        self.experiment_config = ExperimentConfig()

        # arguments related to socket connections with agents
        self.MAX_QUEUE_LEN = 1000
        self.MAX_CON = 2000
        self.HOST = '127.0.0.1'
        self.PORT = 65432
        self.socket = None
        self.request_queue = []
        self.condition = Condition()  # R/W Lock
        self.resp_conditions = {}
        self.con_thread_pool = ThreadPoolExecutor(self.MAX_CON)  # control the accepted number of I/O threads.
        threading.stack_size(self.STATIC_INFO.THREAD_STACK_SIZE)  # control the stack memory size of each threads.
        self.query_tool = QueryTool(database='multiAgents')
        self.response_data = {}
        self.query_tool.cur.execute("TRUNCATE TABLE public.cur_processes")
        self.start_time = None

    def terminate(self):
        # 可以将未处理的请求用文件的形式暂存下来
        self._running = False
        # if self.socket:
        #     self.socket.close()
        self.query_tool.clear_db_connection()

    def create_request_listener(self):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.bind((self.HOST, self.PORT))
        self.socket.listen()
        print("Socket is now listening.")

    def connect_with_agents(self):
        # listen函数实际是创建一个用于监听的独立线程
        # 使用listen可以同时建立多个和client的连接
        # accept函数则是返回一个连接实例，用conn标识
        # 这个实例可以理解为从监听线程中抽出来的，相当于确认监听到的信号，建立实际连接通道，并从中得到信息
        # 一直不accept，监听线程也会一直运行
        # 这里的while True是主线程(创立监听线程的父线程控制的)，也就是说父线程运行期间，不断的确认监听连接并处理收到的信息
        # 父线程无法在处理连接信息的同时并行的对存入队列中的请求进行处理(因为不能变成收到一个请求先处理让其他请求者等待)
        self.start_time = time.time()
        while self._running:
            conn, addr = self.socket.accept()
            # 必须为每一个连接建立一个线程，不然center无法在与一个agent连接的情况下处理其他连接
            # 使用线程池的好处是可以限制线程池大小，避免建立无限多的连接
            # 线程池中进程默认为后台线程，建立后无法通过其他手段干预或强制停止（是说无法在代码中操作）？
            self.con_thread_pool.submit(self.echo_agent, conn, addr)
            time_elapse = time.time() - self.start_time
            if time_elapse > self.experiment_config.timeout:
                self.terminate()

    def echo_agent(self, conn, addr):
        print("Connected by address: ", addr)
        while True:
            try:
                data = conn.recv(4096)
                if not data:
                    break
                # 打印接收到的数据?
                # conn.sendall(data)
                print(data.decode())
                data = data.decode()
                if data == "Data is received.":
                    continue
                else:
                    print("Receiving request data.")

                    conn.send("Request is received.".encode())  # 对agent的响应信息

                    request_id = self.after_receive_request(data)

                    resp_condition = Condition()
                    self.resp_conditions[request_id] = resp_condition

                    print("uuid is:", request_id)
                    conn.send("Request is in queue.".encode())

                    # print(self.response_data)
                    # print(self.response_data[request_id].keys())
                    # while not self.response_data:
                    #     continue
                    # while request_id not in self.response_data.keys():
                    #     continue
                    # while 'data_ready' not in self.response_data[request_id].keys():
                    #     continue
                    # while not self.response_data[request_id]['data_ready']:
                    #     continue
                    # time.sleep(10)
                    # print(self.response_data)
                    # print(self.response_data[request_id].keys())
                    # print(self.response_data[request_id]['data'])
                    # TODO: Debug the Lock Logic
                    # producer,consumer,another consumer relayed on consumer

                    # 保证这里先运行,挂起等待才行

                    self.resp_conditions[request_id].acquire()
                    print("echo get response lock for request ", request_id)

                    if request_id not in self.response_data.keys():
                        print("Waiting for response data ready")
                        self.resp_conditions[request_id].wait()
                        print("response data has been ready and notified the response thread.")
                    elif 'data' not in self.response_data[request_id].keys():
                        print("Waiting for response data ready")
                        self.resp_conditions[request_id].wait()
                        print("response data has been ready and notified the response thread.")

                    if self.response_data[request_id]['data']:
                        conn.send("Data Ready.".encode())
                        resp_data = json.dumps(self.response_data[request_id]['data'])
                        conn.send(resp_data.encode())
                        print('Has Sent Data Back To Drone.')
                    else:
                        conn.send("Put is done.".encode())
                        print('Has Update Data According To Drone.')
                    self.response_data[request_id]['data_sent'] = True

                    self.response_data[request_id].clear()
                    self.response_data.pop(request_id)

                    self.resp_conditions[request_id].release()
                    self.resp_conditions.pop(request_id)

            except Exception as e:
                print("Exception arose when receiving request from agent!")
                print(e)
                break
        conn.close()

    # after_receive_request(多个并行的producer) 与 process_request(一个consumer)应该是两个/多个并行的线程
    # 同时操作request_queue这个资源
    # 应该注意会不会发生读写冲突，必要的话需要加锁
    def after_receive_request(self, request):
        # Producer
        request_id = uuid.uuid1()  # 作为这个request的唯一标示，当处理这个request后，在remove这几条记录前需要向请求发起方反馈结果

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

        print("Add Lock To Request Queue.")

        if len(self.request_queue) == self.MAX_QUEUE_LEN:
            print("Queue full, producer is waiting.")
            self.condition.wait()
            print("Space in queue, Consumer notified the producer.")

        # 将新的请求记录插入self.request_queue以及cur_processes表,并在插入时保证顺序
        if len(self.request_queue) == 0:
            self.request_queue.insert(0, request)
            print("Insert first request! ", len(self.request_queue))

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
                    elif req_time == self.request_queue[i]['time_info']:
                        if request['RoW'] == self.request_queue[i]['RoW'] or (
                                request['RoW'] == 'R' and self.request_queue[i]['RoW'] == 'W'):
                            continue
                        else:
                            self.request_queue.insert(i, request)
            if tmp_len == len(self.request_queue):
                # 说明经过上面的比较得知需要插在队尾
                self.request_queue.append(request)
            print("Insert In Queue! ", len(self.request_queue))
        self.query_tool.cur.execute("INSERT INTO public.cur_processes VALUES "
                                    "({},{},'{}','{}','{}')".format(request['proc_id'], request['uav_id'],
                                                                    request['RoW'], time.strftime("%Y-%m-%d %H:%M:%S",
                                                                                                  time.localtime(
                                                                                                      request[
                                                                                                          'time_info'])),
                                                                    request['uuid']))
        print("Request Insert Done!")
        # 由于cur_processes表中time_info表项类型为time,虽然支持这种语句的插入但只保留时刻,不保留日期
        # 改为timestamp类型的话可以保留日期和时刻

        # 如果插入时发现目前列表中没有PID为0的记录,则在插入结束后,将第一条写,或者前k条连续的读的记录PID均设为0
        if self.request_queue[0]['proc_id'] != 0:
            if self.request_queue[0]['RoW'] == 'W':
                self.request_queue[0]['proc_id'] = 0
                self.query_tool.cur.execute("UPDATE public.cur_processes SET proc_id = 0 WHERE req_uuid = '{}'".format(
                    self.request_queue[0]['uuid']))
            else:
                for i in range(len(self.request_queue)):
                    if self.request_queue[i]['RoW'] == 'R':
                        self.request_queue[i]['proc_id'] = 0
                        self.query_tool.cur.execute(
                            "UPDATE public.cur_processes SET proc_id = 0 WHERE req_uuid = '{}'".format(
                                self.request_queue[i]['uuid']))
                        continue
                    else:
                        break
        print("PID update done!")

        self.condition.notify()
        self.condition.release()
        print("Lock was released!")

        return request_id

    def process_request_in_queue(self):
        # Consumer

        # 根据queue中收到的具体请求情况，对中心数据进行处理
        # 当需要数据更新的时候，针对不同情况，对所有相关数据进行处理（比如除了更新相应的view，还需要执行计算，更新状态信息）
        # 有一些计算或许可以通过直接在数据库中创建trigger处理
        while self._running:

            self.condition.acquire()

            if len(self.request_queue) == 0:
                print("Nothing in queue, consumer is waiting.")
                self.condition.wait()
                print("Producer added something to queue and notified the consumer.")

            # 取PID为0的requests

            merge_list = []
            i_list = []
            index_ = []
            j_list = []
            for i in range(len(self.request_queue)):
                if self.request_queue[i]['proc_id'] == 0:
                    print("process request ", i)
                    uuid = self.request_queue[i]['uuid']

                    print("Process want to get response lock for request ", uuid)
                    self.resp_conditions[uuid].acquire()
                    print("Process get response lock for request ", uuid)

                    self.response_data[uuid] = {}
                    index_.append((i, uuid))
                    # 对每一条request,获取其对应的数据，或者更新相应的数据
                    # 这里比较关键的问题是处理需要并行读取的情况,怎么全部读取，然后分发，然后一起更新cur_processes
                    if self.request_queue[i]['RoW'] == 'R':
                        merge_list.append(uuid)
                        i_list.append(i)
                    else:
                        self.response_data[uuid]['data'] = None
                        if self.request_queue[i]['GoL'] == 'G':
                            for w_sql in self.request_queue[i]['sql_list']:
                                self.query_tool.cur.execute(w_sql)
                        else:
                            for j in range(len(self.request_queue[i]['view_index_list'])):
                                vi = self.request_queue[i]['view_index_list'][j]
                                if vi == 0:
                                    # drone_local_nodes
                                    for new_row in self.request_queue[i]['view_data_list'][j]:
                                        print('new_row: ', new_row)
                                        self.query_tool.cur.execute('SELECT * FROM drone_local_nodes')
                                        print(self.query_tool.cur.fetchall())
                                        self.query_tool.cur.execute('SELECT * FROM cur_processes')
                                        print(self.query_tool.cur.fetchall())
                                        self.query_tool.cur.execute('UPDATE drone_local_nodes '
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
                                        print(self.query_tool.cur.query)
                                        print(self.query_tool.cur.statusmessage)
                                        self.query_tool.cur.execute('SELECT * FROM drone_local_nodes')
                                        print(self.query_tool.cur.fetchall())
                                        self.query_tool.cur.execute('SELECT * FROM grid_nodes')
                                        print(self.query_tool.cur.fetchall())
                                elif vi == 1:
                                    # drone_local_edges
                                    for new_row in self.request_queue[i]['view_data_list'][j]:
                                        self.query_tool.cur.execute("UPDATE public.drone_local_edges "
                                                                    "SET distance={} WHERE edge_id ={}"
                                                                    .format(new_row['DIS'],
                                                                            new_row['EID']))
                                elif vi == 2:
                                    # drone_self_info
                                    print("I am here!")
                                    print(self.request_queue[i]['view_data_list'])
                                    print(isinstance(self.request_queue[i]['view_data_list'], list))
                                    for new_row in self.request_queue[i]['view_data_list'][j]:
                                        print("view 2 new data")
                                        print(new_row)
                                        print(isinstance(new_row, dict))
                                        self.query_tool.cur.execute("UPDATE public.drone_self_info "
                                                                    "SET loc_node_id={},view_range={},"
                                                                    "load_num={},cur_electricity={},"
                                                                    "flying_state={},cur_path_length={},"
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
                                        self.query_tool.cur.execute("UPDATE public.drone_charge_targets "
                                                                    "SET is_inservice={}, cur_utilization={}, "
                                                                    "queue_length={}, dock_num={} WHERE station_id={}"
                                                                    .format(new_row['II'],
                                                                            new_row['CU'],
                                                                            new_row['QL'],
                                                                            new_row['DN'],
                                                                            new_row['SID']))
                                elif vi == 4:
                                    # drone_rescue_targets
                                    for new_row in self.request_queue_queue[i]['view_data_list'][j]:
                                        self.query_tool.cur.execute("UPDATE public.drone_rescue_targets "
                                                                    "SET victims_num={}, load_demand_num={},"
                                                                    "is_completed={} WHERE target_id={}"
                                                                    .format(new_row['VN'],
                                                                            new_row['LDN'],
                                                                            new_row['IC'],
                                                                            new_row['TID']))
                        j_list.append(uuid)
                else:
                    break

            if len(j_list) > 0:
                for uuid in j_list:
                    self.response_data[uuid]['data_ready'] = True
                    self.resp_conditions[uuid].notify()
                    self.resp_conditions[uuid].release()
                    # while ('data_sent' not in self.response_data[uuid].keys()) or (
                    #         not self.response_data[uuid]['data_sent']):
                    #     continue

            if len(merge_list) > 0:
                self.separate_views_data(i_list)
                # 如果是读操作，更新self.response_data[req_uuid].data中的数据为要返回的数据
                for uuid_ in merge_list:
                    self.response_data[uuid_]['data_ready'] = True
                    self.resp_conditions[uuid].notify()
                    self.resp_conditions[uuid].release()
                    # print('here 0.')
                # for uuid_ in merge_list:
                #     while ('data_sent' not in self.response_data[uuid_].keys()) or (not self.response_data[uuid_]['data_sent']):
                #         print("here 1.")
                #         continue
            # self.condition.notify()
            # self.condition.release()

            # if False in ['data_sent' in self.response_data[i].keys() for i in self.response_data.keys()]:
            #     print("Waiting for all data sent")
            #     self.condition.wait()
            #     print("All data has been sent and notified the processor")
            #
            # if len(self.request_queue) == 0:
            #     print("Nothing in queue, consumer is waiting.")
            #     self.condition.wait()
            #     print("Producer added something to queue and notified the consumer.")

            time.sleep(3)

            for (i_, uuid_) in index_:
                # self.response_data[uuid_].clear()
                # self.response_data.pop(uuid_)
                del_ = self.request_queue.pop(i_)
                self.query_tool.cur.execute(
                    "DELETE FROM public.cur_processes WHERE req_uuid = '{}'".format(del_['uuid']))

            print('Delete completed request!')

            # 如果是写操作，更新self.response_data[req_uuid].data中的数据为None
            # 更新self.response_data[req_uuid].data_ready = True
            # 使用while循环进行等待，等待connection将相应的数据发出，即self.response_data[req_uuid].data_sent=True
            # 从self.request_queue中移除相应数据

            # 分析self.request_queue中的剩余的请求，并将前n条连续读或者第一条写的PID置为0

            print("After processing, ", len(self.request_queue))
            if len(self.request_queue) > 0:
                if self.request_queue[0]['proc_id'] != 0:
                    if self.request_queue[0]['RoW'] == 'W':
                        self.request_queue[0]['proc_id'] = 0
                        self.query_tool.cur.execute(
                            "UPDATE public.cur_processes SET proc_id = 0 WHERE req_uuid = '{}'".format(
                                self.request_queue[0]['uuid']))
                    else:
                        for i in range(len(self.request_queue)):
                            if self.request_queue[i]['RoW'] == 'R':
                                self.request_queue[i]['proc_id'] = 0
                                self.query_tool.cur.execute(
                                    "UPDATE public.cur_processes SET proc_id = 0 WHERE req_uuid = '{}'".format(
                                        self.request_queue[i]['uuid']))
                                continue
                            else:
                                break
            print('Identify new request!')

            self.condition.notify()
            self.condition.release()

        if len(self.request_queue) > 0:
            with open('../log/LeftRequests.log', mode='w') as fw:
                while len(self.request_queue) > 0:
                    fw.write(str(self.request_queue.pop(index=0)) + '\n')

    def separate_views_data(self, i_list):

        for read_req_i in i_list:
            # print(read_req_i)
            req = self.request_queue[read_req_i]
            # print(req)
            uuid = req['uuid']
            data = []

            if req['GoL'] == 'G':
                for sql in req['sql_list']:
                    data.append([])
                    self.query_tool.cur.execute(sql)
                    r_rows = self.query_tool.cur.fetchall()
                    colnames = [desc[0] for desc in self.query_tool.cur.description]
                    data[len(data) - 1].append(colnames)
                    data[len(data) - 1].append(r_rows)
            else:
                # print(req['view_index_list'])
                # print(isinstance(req['view_index_list'],list))
                for j in range(len(req['view_index_list'])):
                    vi = req['view_index_list'][j]
                    data.append([])
                    if vi == 0:
                        # drone_local_nodes
                        self.query_tool.cur.execute("SELECT * FROM public.drone_local_nodes WHERE uav_id={}"
                                                    .format(req['uav_id']))
                    elif vi == 1:
                        # drone_local_edges
                        self.query_tool.cur.execute("SELECT * FROM public.drone_local_edges WHERE uav_id={}"
                                                    .format(req['uav_id']))
                    elif vi == 2:
                        # drone_self_info
                        self.query_tool.cur.execute("SELECT * FROM public.drone_self_info WHERE uav_id={}"
                                                    .format(req['uav_id']))
                    elif vi == 3:
                        # drone_charge_targets
                        self.query_tool.cur.execute("SELECT * FROM public.drone_charge_targets WHERE uav_id={}"
                                                    .format(req['uav_id']))
                    elif vi == 4:
                        # drone_rescue_targets
                        self.query_tool.cur.execute("SELECT * FROM public.drone_rescue_targets WHERE uav_id={}"
                                                    .format(req['uav_id']))
                    r_rows = self.query_tool.cur.fetchall()
                    colnames = [desc[0] for desc in self.query_tool.cur.description]
                    data[len(data) - 1].append(colnames)
                    data[len(data) - 1].append(r_rows)

            self.response_data[uuid]['data'] = data

    def check_state(self):

        time.sleep(5)

        while self._running:

            # drawing current state of all drones and global view map

            # check search_coverage task state
            # and update the search_coverage_task, search_coverage_history_state tables
            self.query_tool.cur.execute("SELECT area_id,responsible_fleet_id "
                                        "FROM public.search_coverage_task "
                                        "WHERE start_time IS NOT NULL")
            rows = self.query_tool.cur.fetchall()
            for row in rows:
                aid = row[0]
                fid = row[1]
                self.query_tool.cur.execute("SELECT AVG(cur_path_length) AS avg_step "
                                            "FROM public.drones_cur_state, public.drones_config "
                                            "WHERE drones_config.uav_id=drones_cur_state.uav_id AND fleet_id={}".format(
                    fid))
                move_step = self.query_tool.cur.fetchall()[0][0]
                self.query_tool.cur.execute("SELECT COUNT(node_id) FROM public.grid_nodes "
                                            "WHERE node_type=0 AND visited=FALSE ")
                unvisited_num = self.query_tool.cur.fetchall()[0][0]
                self.query_tool.cur.execute("SELECT COUNT(node_id) FROM public.grid_nodes "
                                            "WHERE node_type=1 or node_type=2")
                other_num = self.query_tool.cur.fetchall()[0][0]
                self.query_tool.cur.execute("SELECT COUNT(node_id) FROM public.grid_nodes")
                total_num = self.query_tool.cur.fetchall()[0][0]
                coverage_ratio = 1 - float(unvisited_num) / float(total_num - other_num)
                self.query_tool.cur.execute("SELECT COUNT(public.drones_cur_state.uav_id) "
                                            "FROM public.drones_cur_state, public.drones_config "
                                            "WHERE drones_config.uav_id = drones_cur_state.uav_id "
                                            "AND flying_state=1 AND fleet_id={} ".format(fid))
                on_working_num = self.query_tool.cur.fetchall()[0][0]
                self.query_tool.cur.execute("SELECT COUNT(public.drones_cur_state.uav_id) "
                                            "FROM public.drones_cur_state, public.drones_config "
                                            "WHERE drones_config.uav_id = drones_cur_state.uav_id "
                                            "AND fleet_id={} ".format(fid))
                total_num = self.query_tool.cur.fetchall()[0][0]
                self.query_tool.cur.execute("SELECT COUNT(public.drones_cur_state.uav_id) "
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
                    self.query_tool.cur.execute("UPDATE public.drones_cur_state "
                                                "SET flying_state=5 "
                                                "WHERE uav_id in "
                                                "(SELECT public.drones_cur_state.uav_id "
                                                "FROM public.drones_cur_state, public.drones_config "
                                                "WHERE drones_cur_state.uav_id = drones_config.uav_id AND fleet_id = {})".format(fid))

                iscompleted = iscompleted or (done_working_num == total_num)
                self.query_tool.cur.execute("INSERT INTO public.search_coverage_history_states "
                                            "VALUES ({},'{}',{},{},{},'{}s',{})".format(aid, timestamp, move_step,
                                                                                        coverage_ratio,
                                                                                        working_uav_ratio,
                                                                                        cur_working_time, iscompleted))
                if iscompleted:
                    self.query_tool.cur.execute(
                        "UPDATE public.search_coverage_task "
                        "SET end_coverage_ratio={},end_time={} "
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

            # 如果同area下任务0已结束,则任务1的任务数不会再增长,这种情况下如果所有的target都有overtime了,
            # 更新rescue_support_task的end_time以及end_completed_ratio

            # 如果负责任务1的所有飞机都处于5状态,则更新rescue_support_task的end_time以及end_completed_ratio

            # self.query_tool.cur.execute("SELECT area_id,responsible_fleet_id "
            #                             "FROM public.rescue_support_task "
            #                             "WHERE start_time IS NOT NULL")
            # rows = self.query_tool.cur.fetchall()

            time.sleep(self.experiment_config.center_check_interval)



    # # 如center与agent处于平等交互地位，即center不仅仅是被动接收agent的请求，同时可以主动建立请求，则需要再建立相应的新的连接
    # def create_request_connection(self):
    #
    # def before_send_request(self):


if __name__ == "__main__":
    center = Center()
    with open(file='../data/metadata.json', mode='r') as fr:
        metadata = json.loads("".join(fr.readlines()))['metadata']
        dg = GlobalDataInitializer(agent_num=metadata['agent_num'],
                                   map_width=metadata['width'],
                                   map_height=metadata['height'],
                                   charge_num=metadata['charge_num'],
                                   charge_pos_list=metadata['charge_pos_list'],
                                   obstacle_num=metadata['obstacle_num'],
                                   db_used=True
                                   )
        dg.initNewMapViews()
        dg.initNewAgentViews()
        dg.ClearDBInitializer()

    process_thread = Thread(target=center.process_request_in_queue)
    process_thread.start()  # process thread

    check_thread = Thread(target=center.check_state)
    check_thread.start()

    center.create_request_listener()  # create socket listener thread
    center.connect_with_agents()

    time.sleep(10)  # waiting for ending listening
    check_thread.join()
    process_thread.join()  # waiting for ending processing

    # response_thread = Thread(target=center.connect_with_agents)
    # 如果该语句直接写在main thread中, 不用单独线程控制的话将是一个无限循环
    # 不能执行下面的center.terminate()主动终止进程
    # response_thread.start()

    # center._running = False
    # process_thread.join()
    # time.sleep(60)

    # accept会阻塞进程，等待accept队列中有元素,也就是维持在connect listen状态下等待新的连接
    # 即response_thread被accept阻塞了,这时候调用terminal并不会影响其进入循环(因为循环已经被阻塞了)
    # 而由于center中直接释放了socket,所以会报错.
    # ConnectionAbortedError: [Errno 53] Software caused connection abort
    # 如果这个问题不处理的话,不知道process_thread会不会受影响直接不执行收尾处理了？
    # 如果直接中断的话process_thread占用的锁资源不知道会不会收到影响

    # center.terminate()
    # response_thread.join()
    # process_thread.join()
