import sys
sys.path.append('../')

import copy
import random
import time
from itertools import combinations

import gym
import gym.spaces as spaces
import numpy as np
import pandas as pd
from gym.envs.classic_control import rendering
from scipy.special import comb

from framework.Center import *


class SimulatedEnv(gym.Env):
    metadata = {
        'render.modes': ['human', 'rgb_array'],
        'video.frames_per_second': 2
    }

    def __init__(self, scale=(0, 0), obstacles_prob=0.2, obstacles_num=None, stations_num=None, initMode='Default',
                 topology='Grid'):
        self.interval = 5
        self.countStep = self.interval
        self.state = []
        self.viewer = None
        self.scale = scale
        self.Points = []
        self.Edges = []
        self.initMode = initMode
        self.topology = topology
        self.obstacles_num = obstacles_num
        self.stations_num = stations_num
        self.obstacles_prob = obstacles_prob
        if self.topology == 'Grid':
            if initMode == "Default":
                self.initDefault(obstacles_prob, obstacles_num, stations_num)
            elif initMode == 'View':
                self.initView()
        self.action_space = spaces.Discrete(5)  # 0, 1, 2，3，4: 不动，右左下上
        self.observation_space = spaces.Dict(
            {'global': spaces.Box(np.array([0, 0]), np.array([self.scale[0], self.scale[1]])),
             'local': spaces.Discrete(5)})
        pass

    def reset(self):
        self.state.clear()
        self.countStep = self.interval
        for l in self.Points:
            for p in l:
                p.visited = False
                p.timespent = 0
                p.reachable = p.init_reachable
                if isinstance(p, ChargingPoint):
                    p.stop_num = p.init_stop_num
                    p.chargingList.clear()

    def initView(self):
        self.initDefault()

    def initDefault(self, obstacles_prob, obstacles_num, stations_num):
        x, y = self.scale
        p_ = None
        obs_p = None
        stat_p = None

        if stations_num:
            self.stations_num = stations_num
        else:
            self.stations_num = int(x / 4)

        if obstacles_num:
            self.obstacles_num = obstacles_num
            p_ = random.sample([i for i in range(x * y)], self.obstacles_num + self.stations_num)
            obs_p = p_[0:self.obstacles_num]
            stat_p = p_[self.obstacles_num:self.obstacles_num + self.stations_num]
        else:
            p_ = random.sample([i for i in range(x * y)], self.stations_num)
            stat_p = p_

        for i in range(x):
            self.Points.append([])
            for j in range(y):
                rc = True
                if not obstacles_num:
                    if random.uniform(0, 1) < obstacles_prob:
                        rc = False
                else:
                    if i * y + j in obs_p:
                        rc = False
                self.Points[i].append(Point(reachable=rc, changeProb=0))

        for i in range(self.stations_num):
            stat_x = int(stat_p[i] / y)
            stat_y = int(int(stat_p[i]) % y)
            self.Points[int(stat_x)][int(stat_y)] = ChargingPoint()

        for i in range(x * y):
            self.Edges.append([])
        for i in range(x * y):
            i_rr = int(i / y)
            i_cc = int(i % y)
            for j in range(x * y):
                j_rr = int(j / y)
                j_cc = int(j % y)
                if j == i:
                    self.Edges[i].append(Edge(from_p=(i_rr, i_cc), to_p=(j_rr, j_cc), traveltime=0))
                elif (i_rr == j_rr and (i_cc == j_cc + 1 or i_cc == j_cc - 1)) or (
                            (i_rr == j_rr + 1 or i_rr == j_rr - 1) and i_cc == j_cc):
                    self.Edges[i].append(Edge(from_p=(i_rr, i_cc), to_p=(j_rr, j_cc)))
                else:
                    self.Edges[i].append(Edge(from_p=(i_rr, i_cc), to_p=(j_rr, j_cc), traveltime=100000))

    def step(self, action):
        reward = []
        done = True

        for i in range(len(self.state)):
            if action[i]:
                # 到达该点环境反馈的奖励
                self.state[i][0] += action[i][0]
                self.state[i][1] += action[i][1]
                P = self.Points[self.state[i][0]][self.state[i][1]]

                if not P.reachable:
                    self.state[i][2] = 1
                    reward.append(-10)
                elif P.ischargingp:
                    reward.append(0)
                elif P.visited:
                    reward.append(-1)
                else:
                    reward.append(1)

                # 在该点经过/悬停使其转为visited的环境反馈的奖励，并更新visited环境量
                if action[i][0] == 0 and action[i][1] == 0:
                    staytime = 1
                else:
                    staytime = 0
                if not P.ischargingp and not P.visited:
                    if P.timespent + staytime < P.timecost:
                        reward[i] += 5
                    elif P.timespent + staytime == P.timecost:
                        reward[i] += 10
                        self.Points[self.state[i][0]][self.state[i][1]].visited = True
                    else:
                        if P.timespent < P.timecost:
                            reward[i] += 10 - (P.timespent + staytime - P.timecost)
                        else:
                            reward[i] -= staytime
                        self.Points[self.state[i][0]][self.state[i][1]].visited = True
                    P.timespent += staytime
                if P.ischargingp:
                    reward[i] -= staytime
                    P.timespent += 0

                # 在该点由降落到起飞并更新的环境量
                if self.state[i][3] == 1 and not (action[i][0] == 0 and action[i][1] == 0 and action[i][2] == True):
                    self.state[i][3] = 0
                    if self.Points[self.state[i][0]][self.state[i][1]].ischargingp:
                        self.Points[self.state[i][0]][self.state[i][1]].stop_num -= 1

                # 在该点降落反馈的奖励,并更新降落引发的环境量
                if action[i][0] == 0 and action[i][1] == 0 and action[i][2] == True:
                    self.state[i][3] = 1
                    staytime = 1
                    if P.ischargingp:
                        if P.timespent + staytime < P.timecost:
                            reward[i] += 5
                        elif P.timespent + staytime == P.timecost:
                            reward[i] += 10
                        else:
                            if P.timespent < P.timecost:
                                reward[i] += 10 - (P.timespent + staytime - P.timecost)
                            else:
                                reward[i] -= staytime
                        self.Points[self.state[i][0]][self.state[i][1]].stop_num += 1
                    else:
                        reward[i] += 0
                        # 如果有余力而且有点可以去，但是选择了降落应该给予惩罚，
                        # 但只根据位置和是否完成了cov任务/坠毁的信息不足以知道uav是不是有余力，
                        # 或者说，这不是环境能够知道的事
            else:
                reward.append(None)
            done = done and self.state[i][2]

        if not done:
            done = self.checkCovProcess()
            if done:
                for i in range(len(self.state)):
                    self.state[i][2] = 1

        return self.state, reward, done, {}

    def render(self, mode='human', close=False):
        if close:
            if self.viewer is not None:
                self.viewer.close()
                self.viewer = None
            return

        screen_width = 500
        screen_height = 500

        w = 400 / (self.scale[0] - 1)
        h = 400 / (self.scale[1] - 1)

        if self.viewer is None:
            self.viewer = rendering.Viewer(screen_width, screen_height)
            h_lines = []
            v_lines = []
            agents = []
            obstacles = []
            stations = []
            self.agents_trans = []

            # 创建网格线
            for r in range(self.scale[0]):
                h_lines.append([])
                for c in range(self.scale[1] - 1):
                    line = rendering.Line((50 + c * w, 450 - r * h), (50 + (c + 1) * w, 450 - r * h))
                    line.set_color(0, 0, 0)
                    h_lines[r].append(line)
                    self.viewer.add_geom(line)
            for c in range(self.scale[1]):
                v_lines.append([])
                for r in range(self.scale[0] - 1):
                    line = rendering.Line((50 + c * w, 450 - r * h), (50 + c * w, 450 - (r + 1) * h))
                    line.set_color(0, 0, 0)
                    v_lines[c].append(line)
                    self.viewer.add_geom(line)
            # 创建障碍物/充电站
            for r in range(self.scale[0]):
                for c in range(self.scale[1]):
                    if not self.Points[r][c].reachable:
                        obs = rendering.make_circle(min(w, h) / 2)
                        obs_trans = rendering.Transform(translation=(50 + c * w, 450 - r * h))
                        obs.add_attr(obs_trans)
                        obs.set_color(0, 0, 0)
                        obstacles.append(obs)
                        self.viewer.add_onetime(obs)
                    if self.Points[r][c].ischargingp:
                        station = rendering.make_polygon(
                            [(50 + c * w, 450 - r * h + h / 2), (50 + c * w - w / 2, 450 - r * h - h / 2),
                             (50 + c * w + w / 2, 450 - r * h - h / 2)])
                        stat_trans = rendering.Transform()
                        station.add_attr(stat_trans)
                        station.set_color(0, 0.8, 0.3)
                        stations.append(station)
                        self.viewer.add_geom(station)
            # 创建UAVs
            for i in range(len(self.state)):
                agent_pos = self.state[i]
                agent = rendering.make_circle(min(w, h) / 2)
                agent_trans = rendering.Transform(translation=(50 + agent_pos[1] * w, 450 - agent_pos[0] * h))
                self.agents_trans.append(agent_trans)
                agent.add_attr(self.agents_trans[i])
                agent.set_color(0.8, 0.6, 0.4)
                agents.append(agent)
                self.viewer.add_geom(agent)

            self.h_lines = h_lines
            self.v_lines = v_lines
            self.agents = agents
            self.obstacles = obstacles
            self.stations = stations
            self.visited_points = []

        if self.state is None or len(self.state) == 0: return None

        self.obstacles.clear()
        self.visited_points.clear()
        for r in range(self.scale[0]):
            for c in range(self.scale[1]):
                if not self.Points[r][c].reachable:
                    obs = rendering.make_circle(min(w, h) / 2)
                    obs_trans = rendering.Transform(translation=(50 + c * w, 450 - r * h))
                    obs.add_attr(obs_trans)
                    obs.set_color(0, 0, 0)
                    self.obstacles.append(obs)
                    self.viewer.add_onetime(obs)
                if self.Points[r][c].visited:
                    visited_point = rendering.make_circle(min(w, h) / 4)
                    visited_trans = rendering.Transform(translation=(50 + c * w, 450 - r * h))
                    visited_point.add_attr(visited_trans)
                    visited_point.set_color(255, 0, 0)
                    self.visited_points.append(visited_point)
                    self.viewer.add_onetime(visited_point)

        for i in range(len(self.state)):
            agent_pos = self.state[i]
            self.agents_trans[i].set_translation(50 + agent_pos[1] * w, 450 - agent_pos[0] * h)

        return self.viewer.render(return_rgb_array=mode == 'rgb_array')

    def close(self):
        if self.viewer: self.viewer.close()

    def checkCovProcess(self):
        result = True
        for x in range(self.scale[0]):
            for y in range(self.scale[1]):
                if not self.Points[x][y].ischargingp and self.Points[x][y].reachable:
                    result = result and self.Points[x][y].visited
        return result


def build_globle_q_table(env, n_agents, actions):
    scale = env.scale
    n_comb_status = comb(scale[0]*scale[1],n_agents)
    combins = list(combinations(range(scale[0]*scale[1]), n_agents))
    table = pd.DataFrame(np.zeros((n_comb_status * n_agents, len(actions))), columns=actions, )

    for i in range(0, n_comb_status):
        agents_pos = combins[i]
        for j in range(0, n_agents):
            agent_pos = agents_pos[j]


    return combins, table


if __name__ == '__main__':
    # done代表全局的是否结束
    # moved代表不违反动作选择约束(包括动作是否合法和动作是否安全)的情况下有动作可做
    # done returned from env.step代表没有撞墙，并且还没有完全覆盖
    # reward为大小为n的集合,表示当前步骤下每个agent获得的即时奖励
    episode = 1 # 迭代轮数
    scale = (20, 20) # 搜索范围
    uav_num = 2 # UAVs机群规模
    MAX_T = int(scale[0] * scale[1]/uav_num * 2) # 最大搜索步数
    Lamda = 0.9
    Learning_Rate = 0.1

    env = Env(scale=scale, obstacles_num=40, stations_num=5)
    view = copy.deepcopy(env)

    loc_combins_list, table = build_globle_q_table(env=env, n_agents = uav_num, actions = ['0','1','2','3','4','5'])

    for x in range(view.scale[0]):
        for y in range(view.scale[1]):
            if isinstance(view.Points[x][y], ChargingPoint):
                init_prob = view.Points[x][y].changeProb
                view.Points[x][y].changeProb = 0.2
                view.Points[x][y].update()
                view.Points[x][y].changeProb = init_prob
            else:
                view.Points[x][y].update()
    center = Center(view)

    fleet = []
    tmp_fleet_pos = []
    uav_count = 0
    while uav_count < uav_num:
        rand_x = int(random.randint(0, scale[0] - 1))
        rand_y = int(random.randint(0, scale[1] - 1))
        f_p = rand_x * scale[1]+rand_y
        t_P = env.Points[rand_x][rand_y]
        if t_P.reachable and f_p not in tmp_fleet_pos:
            if (not isinstance(t_P,ChargingPoint)) or (isinstance(t_P,ChargingPoint) and t_P.stop_num<t_P.cap):
                fleet.append(UAV(pos_x=rand_x, pos_y=rand_y))
                tmp_fleet_pos.append(f_p)
                uav_count += 1

    for i in range(episode):
        start_t = time.time()
        env.reset()
        del center.global_view
        center.global_view = copy.deepcopy(view)
        dones = False
        temp_dones = True

        loc_combins = []

        for u in fleet:
            u.reset()
            env.state.append(np.array([u.pos[0], u.pos[1], 0, 0]))# x,y,isdone(结束或者坠毁),island(主动降落）
            loc_combins.append(u.pos[0]*env.scale[1]+u.pos[1])
            env.Points[u.pos[0]][u.pos[1]].reachable = True
            env.Points[u.pos[0]][u.pos[1]].visited = True
            if isinstance(env.Points[u.pos[0]][u.pos[1]], ChargingPoint):
                env.Points[u.pos[0]][u.pos[1]].stop_num += 1
            center.global_view.Points[u.pos[0]][u.pos[1]].reachable = True
            center.global_view.Points[u.pos[0]][u.pos[1]].visited = True
            if isinstance(center.global_view.Points[u.pos[0]][u.pos[1]], ChargingPoint):
                center.global_view.Points[u.pos[0]][u.pos[1]].stop_num = env.Points[u.pos[0]][u.pos[1]].stop_num
        center.global_view.state = env.state

        step_count = 0
        loc_combins = tuple(loc_combins.sort())
        loc_index = loc_combins_list.index(loc_combins)
        while step_count < MAX_T and not dones:
            env.render()
            action = []
            obs_n = env.state
            has_moved = False
            for u in fleet:
                moved, done, ac, center, table = u.chooseAction(env=env,center=center,q_table=table,loc_index=loc_index, loc_combins=loc_combins, loc_combins_list=loc_combins_list)
                if moved:
                    action.append(ac)
                else:
                    action.append(None)
                has_moved = has_moved or moved # 只要还有在moved的has_moved=True

            dones = not has_moved

            if not dones:
                new_state, reward, terminal, info = env.step(action)
                center.global_view.state = new_state
                loc_combins = []
                q_predicts = []
                global_terminal = True
                for i in range(len(fleet)):
                    from_p = fleet[i].pos[0]*env.scale[1]+fleet[i].pos[1]
                    ss = loc_index * len(loc_combins) + loc_combins.index(from_p)
                    if action[i]:
                        q_predicts.append(table.loc[ss, fleet[i].actions.index(action[i])])
                    else:
                        q_predicts.append(0)

                    fleet[i].pos[0]=new_state[i][0]
                    fleet[i].pos[1]=new_state[i][1]
                    fleet[i].terminal = terminal[i]
                    fleet[i].experience.add(obs_n[i], action[i], reward[i], new_state[i], float(terminal[i]))
                    global_terminal = global_terminal and terminal[i]
                    loc_combins.append(new_state[i][0]*env.scale[1]+new_state[i][1])
                    center = fleet[i].put_local_view(env=env, center=center, action=action[i])
                loc_combins = tuple(loc_combins.sort())
                loc_index = loc_combins_list.index(loc_combins)

                q_targets = []

                for i in range(len(fleet)):
                    if not terminal[i]:
                        new_from_p = fleet[i].pos[0] * env.scale[1] + fleet[i].pos[1]
                        ss_ = loc_index * len(loc_combins) + loc_combins.index(from_p)
                        q_targets.append(reward[i] + Lamda * table.iloc[ss_, :].max())
                    else:
                        q_targets.append(reward[i])
                for i in range(len(q_predicts)):
                    table.loc[ss, fleet[i].actions.index(action[i])] += Learning_Rate * (q_targets[i] - q_predicts[i])

                step_count += 1
                dones = global_terminal
            else:
                for i in range(len(fleet)):
                    center = fleet[i].put_local_view(env=env, center=center, action=action[i])
                break
            time.sleep(0.5)
        episode_t = time.time()-start_t
        print("episode %d: %s s."%(i , episode_t))

    env.close()