# -*- coding:utf-8 -*-
import sys
sys.path.append('../')
from framework.CustomExceptions import *
from framework.StaticConsensus import *
from framework.QueryTool import *
from framework.EnvMap import *
import random
import time
from socket import *
from threading import *
import json

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

    def state_init(self):
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
        self.cur_RCost = rows[0][colnames.index('cur_resource_cost')]
        self.cur_LN = rows[0][colnames.index('load_num')]
        # 在init情况下,所有uav的flying_state只有可能是0或1
        # 在reset情况下,首先reset的是数据库中drones,map等相关的数据,然后再重新从数据中init
        # 即无人机reset函数的调用必须在环境reset及中心全局数据reset之后
        # 1)环境状态reset 2)全局数据reset 3)中心属性reset 4)agents属性reset
        # 如果环境和关于环境的全局数据保持最新状态，仅想要reset所有的无人机则
        # 1)全局数据中关于drones state的数据reset 2)中心中有关drones的属性reset 3)agents属性reset
        self.TID = None

    def reset(self):
        if self.socket:
            self.socket.close()
        self.socket = None
        self._running = True
        self.state_init()

    def terminate(self):
        self._running = False
        if self.socket:
            self.socket.close()

    def connect_with_center(self, RoW='R', View_List = None, GoL='L', Datas=None, SQLs=None):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.connect((self.HOST, self.PORT))

        send_data = self.before_send_request(RoW, View_List, GoL, Datas, SQLs)
        send_data = json.dumps(send_data)
        print(send_data)
        self.socket.send(send_data.encode())
        get_data = None
        while True:
            try:
                data = self.socket.recv(16384)
                if not data:
                    print("Without receiving data.")
                    break
                data = data.decode()
                print(data)

                if data == "Request is received." or data == "Request is in queue." or data == 'Data Ready.':
                    continue
                elif data == "Put is done.":
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
        self.socket.close()
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
        # init request(read) test
        # pass
        self.state_init()
        while self._running:
            # read request test
            # pass
            self.connect_with_center(RoW='R',View_List=[0], GoL='L')
            # pass
            self.connect_with_center(RoW='R',View_List=[0,1,2],GoL='L')
            # pass
            self.connect_with_center(RoW='R',SQLs=["SELECT * FROM public.drones_config","SELECT * FROM public.nodes_config"],GoL='G')
            time.sleep(5)
            # write request test
            # pass
            self.connect_with_center(RoW='W',View_List=[0],GoL='L',Datas={'sense_time':time.time(),
                                                                          'new_data':[[{'UID':self.UID,
                                                                                      'NID':self.cur_NID,
                                                                                      'VC':1,
                                                                                      'V': True,
                                                                                      'VN':random.randint(0,10),
                                                                                      'NR': False,
                                                                                      'NT': 0,
                                                                                      }]]
                                                                          })
            # pass
            self.connect_with_center(RoW='W',SQLs=["UPDATE public.rescue_support_cur_state "
                                                   "SET is_allocated= FALSE, responsible_uav_id= NULL "
                                                   "WHERE target_id = {}".format(self.cur_NID)],GoL='G', Datas={'sense_time':time.time()})

            break

    def run(self, env):

        self.state_init()

        while self._running:
            # 无人机正常飞行过程中的主要逻辑，包括什么时候调用self.connect_with_center函数/创建线程
            if self.cur_State == 0:
                # WW: Waiting For Work State
                if self.check_is_allocated():
                    self.cur_State = 1
                    sense_time = time.time()
                    new_data = [{'uav_id': self.UID, 'flying_state': 1}]
                    Thread(target=self.connect_with_center,
                           args=('W', [2], 'L', {'sense_time': sense_time, 'new_data': new_data}, None),
                           daemon=False)
                    # daemon=false相当于在主线程最后调用thread.join方法,子线程为后台线程，主线程完成后会等待子线程结束然后再结束
                    # daemon=true则主线程结束,子线程自动结束
                else:
                    if not self.TID:
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
                if not self.TID:
                    self.check_is_allocated()
                    if not self.TID:
                        self.cur_State = 0
                        sense_time = time.time()
                        new_data = [{'uav_id': self.UID, 'flying_state': 0}]
                        Thread(target=self.connect_with_center,
                               args=('W', [2], 'L', {'sense_time': sense_time, 'new_data': new_data}, None),
                               daemon=False)
                        continue
                if self.TID == 0:
                    # working in search_coverage_task
                    get_data = self.connect_with_center(RoW='R', View_List=[0, 1], GoL='L')
                    self.Local_View_Map.update_map(get_data)
                    self.sense_within_range(env)


                elif self.TID == 1:
                    # working in rescue_coverage_task
                    get_data = self.connect_with_center(RoW='R', View_List=[0, 1, 4], GoL='L')
                    self.Local_View_Map.update_map(get_data[0:2])
                    self.sense_within_range(env)

            time.sleep(2)
        # 主进程要求终止后，需要处理的收尾工作
        return None

    # 下面的应该全是辅助run函数实现的函数
    def check_is_allocated(self):
        task_data = self.connect_with_center(RoW='R', GoL='G', SQLs=[
            "SELECT area_id, responsible_fleet_id, end_time FROM public.rescue_support_task",
            "SELECT area_id, responsible_fleet_id, end_time FROM public.search_coverage_task"])
        rescue_support_task = task_data[0][0]  # tuple, only one area
        search_coverage_task = task_data[1][0]  # tuple, only one area
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
        def get_local_info():
            return self.cur_PX, self.cur_PY, self.SR

        concrete_local = get_local_info()
        # update local view using concrete_local
        sense_time = time.time()
        self.Local_View_Map.update_map(concrete_local, sense_time)


if __name__ == '__main__':

    qtool = QueryTool(database='multiAgents')
    col_nms, rows = qtool.get_view(view_name='drones_cur_state')
    drone_num = len(rows)

    fleet = []
    fleet_thread = []
    env = ConcreteEnv()

    for i in range(drone_num):
        fleet.append(UAV(ID=i, experiment_config=ExperimentConfig()))
        drone_con_thread = Thread(target=fleet[i].run, args=(env,))
        # drone_con_thread = Thread(target=fleet[i].test)
        fleet_thread.append(drone_con_thread)
        drone_con_thread.start()

    time.sleep(30)

    for i in range(drone_num):
        fleet[i].terminate()
        fleet_thread[i].join()
