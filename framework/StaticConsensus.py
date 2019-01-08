# -*- coding:utf-8 -*-

'''
This file is used to define the common consensus arguments between agents and center.
Including,
Static Info:
    Local views' names and corresponding indexes;
    Max Length for edges;
    Max stack size of each running threads in center/agents;
Experiments Arguments:
    threshold for charging warning;
    threshold for going for charging;

'''
class StaticInfo:

    def __init__(self):
        self.UNIT = 400  # pixel
        self.VIEWS_INDEX = {'drone_local_nodes': 0,
                            'drone_local_edges': 1,
                            'drone_self_info': 2,
                            'drone_charge_targets': 3,
                            'drone_rescue_targets': 4
                            }
        self.NODE_TYPE = {
            'normal': 0,
            'blocked': 1,
            'charging_station': 2
        }
        self.TASK_INDEX = {'search_recoverage':0,
                           'rescue_support':1}
        self.FLYING_STATE = {
            'WW':0,
            'IW':1,
            'GC':2,
            'WC':3,
            'IC':4,
            'END':5
        }
        self.THREAD_STACK_SIZE = 65536
        self.EDGE_INX = 100000000

class ExperimentConfig:

    def __init__(self):
        self.timeout = 600
        self.center_check_interval = 10
        self.W_Threshold = 0.6
        self.C_Threshold = 0.8
        self.N_Damage = 0
        self.M_Damage = 1
        self.S_Damage = 2