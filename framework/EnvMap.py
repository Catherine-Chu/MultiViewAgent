from framework.EnvComponents import *
import random
import time
import psycopg2

class ConcreteEnv:
    def __init__(self, datasrc=None, metadata=None):
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
        random.seed(time.time())
        if datasrc:
            self.width = metadata['width']
            self.height = metadata['height']
            self.node_num = metadata['node_num']
            self.edge_num = metadata['edge_num']
            self.charge_num = metadata['charge_num']
            self.obstacle_num = metadata['obstacle_num']
            self.env_change_prob = metadata['env_change_prob']
            self.stat_change_prob = metadata['stat_change_prob']
            # TODO: define datasrc structure and process the real data into specific structure
            # TODO: create Points & Edges objects according to datasrc


class LocalViewMap:

    def __init__(self, data=None):
        self.Edges = []
        self.Nodes = []
        if data:
           nodes_data = data[0]
           edges_data = data[1]

    def update_map(self, data, sense_time = None):
        new_nodes_data = data[0]
        new_edges_data = data[1]
        if sense_time:
            # 利用感知到的数据更新地图
            # 在新数据记录上标记True,不更新的记录上标记False,并且标记感知时间
            return True
        else:
            # 利用从center获取的view数据更新地图
            # 所有数据记录都把更新标记标为False
            return False