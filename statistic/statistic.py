import os
import math
import time
import json


try:
    def run_statistic():
        root = os.path.abspath(os.path.dirname(os.getcwd()) + os.path.sep + ".")
        file_dir = os.path.join(root, "framework")
        log_dir = os.path.join(root, 'log')

        # scale = [(10, 10), (20, 20), (50, 50), (100, 100)]
        # group = [1, 4, 8, 16, 32]
        # view_range = [2, 4, 8, 16, 32]
        scale = [(10, 10)]
        group = [4]
        view_range = [2, 3, 4, 5]
        max_memory = [2, 3, 4, 5]

        for vr in range(len(view_range)):
            for i in range(len(scale)):
                width = scale[i][0]
                height = scale[i][1]
                obstacle_num = int(width * height * 0.1)
                for j in range(len(group)):
                    agent_num = [group[j], 0, 0]
                    if view_range[vr] <= int(math.sqrt(pow(width, 2) + pow(height, 2))):
                        # t_tag = time.strftime("%m%d%H%M", time.localtime())
                        cur_args = "--width {} --height {} --obstacle_num {} " \
                                   "--agent_num '{}' --view_range {} --max_memory {}".format(
                            width, height, obstacle_num, str(agent_num), view_range[vr], max_memory[vr])
                        # if not os.path.exists(drone_log + '_{}.log'.format(t_tag)):
                        #     f = open(drone_log + '_{}.log'.format(t_tag), mode='w')
                        #     f.close()
                        # cmd1 = 'python ' + file_dir + '/Center1.py {} > '.format(
                        #     cur_args) + center_log + '_{}.log'.format(t_tag)
                        # cmd2 = 'sleep 1; python ' + file_dir + '/Drones1.py {} > '.format(
                        #     cur_args) + drone_log + '_{}.log'.format(t_tag)
                        cmd1 = 'python ' + file_dir + '/Center1.py {}'.format(
                            cur_args)
                        cmd2 = 'sleep 1; python ' + file_dir + '/Drones1.py {}'.format(
                            cur_args)
                        os.system(cmd1 + ' & ' + cmd2)
                        time.sleep(5)
except Exception as e:
    print(e)

for t in range(4):
    run_statistic()
    time.sleep(30)
