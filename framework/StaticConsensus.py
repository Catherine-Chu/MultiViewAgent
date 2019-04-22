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
        self.UNIT = 60  # pixel
        self.VIEWS_INDEX = {'drone_local_nodes': 0,
                            'drone_local_edges': 1,
                            'drone_self_info': 2,
                            'drone_charge_targets': 3,
                            'drone_rescue_targets': 4,
                            'drone_delivery_targeys': 5,
                            'drone_local_neighbors': 6
                            }
        self.DANGER_LEVEL = {
            'safe': 0,
            'dangerous': 1,
            'blocked': 2
        }
        self.NODE_TYPE = {
            'normal_safe': 0,
            'blocked': 1,
            'charging_station': 2,
            'normal_dangerous': 3
        }
        self.TASK_INDEX = {'search_recoverage':0,
                           'rescue_support':1,
                           'transport':2}
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
        self.END = '*'


class ExperimentConfig:

    def __init__(self):
        self.timeout = 90000  # max simulation time
        self.waittime = 30
        self.center_check_interval = 10  # interval(s) of checking for task status
        self.W_Threshold = 0.6  # E charge warning threshold
        self.C_Threshold = 0.8  # E charging threshold
        # Drone damage degree
        self.N_Damage = 0   # No damage
        self.M_Damage = 1   # Medium damage
        self.S_Damage = 2   # Serious damage
        # Survivors threshold for refuges
        self.S_max = 10
        self.refuge_prob = 0.05
        self.MAX_LOAD = 10
        self.MAX_E = 20000
        self.FLOYD_INTERVAL = 5
        self.HYBRID_ALPHA_T = 0.8
        self.HYBRID_ALPHA = 0
        self.HYBRID_CAL_INTERVAL = 0.5
