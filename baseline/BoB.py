# action_space = [(0, 1, 1), (0, -1, 1), (-1, 0, 1), (1, 0, 1), (0, 0, 1), (0, 0, 0)]
# up(north),down(south),left(west),right(east)

import numpy as np


def BoB(view_map, agents_pos, agents_path, scale, action_space, cur_x, cur_y, uid, fid, his_step, hybrid=False):
    '''

    :param view_map:
    :param agents_pos:
    :param agents_path: 2D list
    the number of agents * the length of the backtracking path list
    (the length of the backtracking path list maybe 0 if the agent isn't backtracking)
    :param scale:
    :param action_space:
    :param cur_x:
    :param cur_y:
    :param uid:
    :param fid:
    :param his_step:
    :param hybrid:
    :return:
    '''
    if hybrid:
        not_end_point, next_x, next_y, his_step = boustrophedon_step(view_map, scale, action_space, cur_x, cur_y, uid,
                                                                     fid, his_step)
        if not not_end_point:
            back_points = find_backtracking_points(view_map, scale, agents_pos, agents_path)
            tar_x, tar_y, path = find_shortest_backtracking_path(scale, view_map, cur_x, cur_y, back_points)


def check_valid(ck_x, ck_y, local_view_map, scale, fid, agents_pos=None):
    is_valid = True
    if 0 <= ck_x < scale[0] and 0 <= ck_y < scale[1]:
        next_nid = ck_x * scale[1] + ck_y
        next_node = None
        has_neighbor = False
        if isinstance(local_view_map.Nodes, dict):
            next_node = local_view_map.Nodes[next_nid]
            if next_nid in list(local_view_map.Neighbors.keys()):
                has_neighbor = True
        elif isinstance(local_view_map.Nodes, list):
            next_node = local_view_map.Nodes[ck_x][ck_y]
            if agents_pos and next_nid in agents_pos:
                has_neighbor = True
        is_valid = (next_node is not None) and (not next_node.blocked and not next_node.visited) and \
                   (not has_neighbor)
        if fid == 0 or fid == 2:
            if next_node.danger_level > 0:
                is_valid = False
    else:
        is_valid = False
    return is_valid


def boustrophedon_step(local_view_map, scale, action_space, cur_x, cur_y, uid, fid, his_step, agents_pos=None):
    '''
    :param local_view_map:
    :param scale:
    :param action_space:
    :param cur_x:
    :param cur_y:
    :param uid:
    :param fid:
    :param his_step: 1<=len(his_step)<=2
    :return:
    '''
    if len(his_step) == 0:
        if cur_y <= scale[1] / 2:
            his_step = ['N']
        else:
            his_step = ['S']
    last_step = his_step[len(his_step) - 1]
    lsec_step = None
    if len(his_step) > 1:
        lsec_step = his_step[0]
    if last_step == 'N':
        # Check North
        n_x = action_space[0][0] + cur_x
        n_y = action_space[0][1] + cur_y
        if check_valid(n_x, n_y, local_view_map, scale, fid, agents_pos):
            return True, n_x, n_y, his_step
        else:
            # Check East
            n_x = action_space[3][0] + cur_x
            n_y = action_space[3][1] + cur_y
            if check_valid(n_x, n_y, local_view_map, scale, fid, agents_pos):
                his_step = [last_step, 'E']
                return True, n_x, n_y, his_step
            else:
                # Check West (last choice)
                n_x = action_space[2][0] + cur_x
                n_y = action_space[2][1] + cur_y
                if check_valid(n_x, n_y, local_view_map, scale, fid, agents_pos):
                    his_step = [last_step, 'W']
                    return True, n_x, n_y, his_step
                else:
                    return False, cur_x, cur_y, his_step
    elif last_step == 'S':
        # Check South
        n_x = action_space[1][0] + cur_x
        n_y = action_space[1][1] + cur_y
        if check_valid(n_x, n_y, local_view_map, scale, fid, agents_pos):
            return True, n_x, n_y, his_step
        else:
            # Check West
            n_x = action_space[2][0] + cur_x
            n_y = action_space[2][1] + cur_y
            if check_valid(n_x, n_y, local_view_map, scale, fid, agents_pos):
                his_step = [last_step, 'W']
                return True, n_x, n_y, his_step
            else:
                # Check East (last choice)
                n_x = action_space[3][0] + cur_x
                n_y = action_space[3][1] + cur_y
                if check_valid(n_x, n_y, local_view_map, scale, fid, agents_pos):
                    his_step = [last_step, 'E']
                    return True, n_x, n_y, his_step
                else:
                    return False, cur_x, cur_y, his_step
    elif last_step == 'W':
        if lsec_step:
            if lsec_step == 'S':
                # Check North
                n_x = action_space[0][0] + cur_x
                n_y = action_space[0][1] + cur_y
                if check_valid(n_x, n_y, local_view_map, scale, fid, agents_pos):
                    his_step = [last_step, 'N']
                    return True, n_x, n_y, his_step
                else:
                    # Check South
                    n_x = action_space[1][0] + cur_x
                    n_y = action_space[1][1] + cur_y
                    if check_valid(n_x, n_y, local_view_map, scale, fid, agents_pos):
                        his_step = [last_step, 'S']
                        return True, n_x, n_y, his_step
                    else:
                        # Check West (last choice)
                        n_x = action_space[2][0] + cur_x
                        n_y = action_space[2][1] + cur_y
                        if check_valid(n_x, n_y, local_view_map, scale, fid, agents_pos):
                            return True, n_x, n_y, his_step
                        else:
                            return False, cur_x, cur_y, his_step
            elif lsec_step == 'N':
                # Check South
                n_x = action_space[1][0] + cur_x
                n_y = action_space[1][1] + cur_y
                if check_valid(n_x, n_y, local_view_map, scale, fid, agents_pos):
                    his_step = [last_step, 'S']
                    return True, n_x, n_y, his_step
                else:
                    # Check North
                    n_x = action_space[0][0] + cur_x
                    n_y = action_space[0][1] + cur_y
                    if check_valid(n_x, n_y, local_view_map, scale, fid, agents_pos):
                        his_step = [last_step, 'N']
                        return True, n_x, n_y, his_step
                    else:
                        # Check West (last choice)
                        n_x = action_space[2][0] + cur_x
                        n_y = action_space[2][1] + cur_y
                        if check_valid(n_x, n_y, local_view_map, scale, fid, agents_pos):
                            return True, n_x, n_y, his_step
                        else:
                            return False, cur_x, cur_y, his_step
        else:
            his_step = ['S', last_step]
            return boustrophedon_step(local_view_map, scale, action_space, cur_x, cur_y, uid, fid, his_step, agents_pos)
    elif last_step == 'E':
        if lsec_step:
            if lsec_step == 'N':
                # Check South
                n_x = action_space[1][0] + cur_x
                n_y = action_space[1][1] + cur_y
                if check_valid(n_x, n_y, local_view_map, scale, fid, agents_pos):
                    his_step = [last_step, 'S']
                    return True, n_x, n_y, his_step
                else:
                    # Check North
                    n_x = action_space[0][0] + cur_x
                    n_y = action_space[0][1] + cur_y
                    if check_valid(n_x, n_y, local_view_map, scale, fid, agents_pos):
                        his_step = [last_step, 'N']
                        return True, n_x, n_y, his_step
                    else:
                        # Check East (last choice)
                        n_x = action_space[3][0] + cur_x
                        n_y = action_space[3][1] + cur_y
                        if check_valid(n_x, n_y, local_view_map, scale, fid, agents_pos):
                            return True, n_x, n_y, his_step
                        else:
                            return False, cur_x, cur_y, his_step
            elif lsec_step == 'S':
                # Check North
                n_x = action_space[0][0] + cur_x
                n_y = action_space[0][1] + cur_y
                if check_valid(n_x, n_y, local_view_map, scale, fid, agents_pos):
                    his_step = [last_step, 'N']
                    return True, n_x, n_y, his_step
                else:
                    # Check South
                    n_x = action_space[1][0] + cur_x
                    n_y = action_space[1][1] + cur_y
                    if check_valid(n_x, n_y, local_view_map, scale, fid, agents_pos):
                        his_step = [last_step, 'S']
                        return True, n_x, n_y, his_step
                    else:
                        # Check East (last choice)
                        n_x = action_space[3][0] + cur_x
                        n_y = action_space[3][1] + cur_y
                        if check_valid(n_x, n_y, local_view_map, scale, fid, agents_pos):
                            return True, n_x, n_y, his_step
                        else:
                            return False, cur_x, cur_y, his_step
        else:
            his_step = ['N', last_step]
            return boustrophedon_step(local_view_map, scale, action_space, cur_x, cur_y, uid, fid, his_step, agents_pos)


def find_backtracking_points(view_map, scale, agents_pos=None, agents_path=None):
    back_points = []
    if not agents_pos and isinstance(view_map.Nodes, dict):
        agents_pos = list(view_map.Neighbors.keys())
    if isinstance(view_map.Nodes, dict):
        for node_id, node in view_map.Nodes.items():
            x = int(node_id / scale[1])
            y = int(node_id % scale[1])
            s2_s, s4_s, s6_s, s8_s = eliminate_agent_surroundings(x, y, scale)
            if calculate_b(x, y, view_map, scale) >= 1 and (node_id not in agents_pos) \
                    and (s2_s not in agents_pos) and (s4_s not in agents_pos) \
                    and (s6_s not in agents_pos) and (s8_s not in agents_pos):
                back_points.append(node_id)
    elif isinstance(view_map.Nodes, list):
        for i in range(scale[0]):
            for j in range(scale[1]):
                node_id = i * scale[1] + j
                s2_s, s4_s, s6_s, s8_s = eliminate_agent_surroundings(i, j, scale)
                if calculate_b(i, j, view_map, scale) >= 1 and (node_id not in agents_pos) \
                        and (s2_s not in agents_pos) and (s4_s not in agents_pos) \
                        and (s6_s not in agents_pos) and (s8_s not in agents_pos):
                    back_points.append(node_id)
    # print(agents_path)
    back_points = eliminate_agent_path_conflict(back_points, agents_path)
    return back_points


def calculate_b(i, j, view_map, scale):
    def check_relation(i1, j1, i2, j2):
        if 0 <= i1 < scale[0] and 0 <= j1 < scale[1]:
            n1 = i1 * scale[1] + j1
            n2 = i2 * scale[1] + j2
            if isinstance(view_map.Nodes, dict):
                if n1 in list(view_map.Nodes.keys()):
                    if ((n2 in list(view_map.Nodes.keys()) and view_map.Nodes[n2].blocked)
                        or n2 not in list(view_map.Nodes.keys())) \
                            and (not view_map.Nodes[n1].blocked and not view_map.Nodes[n1].danger_level > 0 and
                                 not view_map.Nodes[n1].visited):
                        return 1
                    else:
                        return 0
                else:
                    return 0
            elif isinstance(view_map.Nodes, list):
                if ((0 <= i2 < scale[0] and 0 <= j2 < scale[1] and view_map.Nodes[i2][j2].blocked)
                    or not (0 <= i2 < scale[0] and 0 <= j2 < scale[1])) \
                        and (not view_map.Nodes[i1][j1].blocked and not view_map.Nodes[i1][j1].danger_level > 0 and
                             not view_map.Nodes[i1][j1].visited):
                    return 1
                else:
                    return 0
        else:
            return 0

    x1 = i + 1
    y1 = j
    x2 = i + 1
    y2 = j + 1
    x3 = i
    y3 = j + 1
    x4 = i - 1
    y4 = j + 1
    x5 = i - 1
    y5 = j
    x6 = i - 1
    y6 = j - 1
    x7 = i
    y7 = j - 1
    x8 = i + 1
    y8 = j - 1
    b = check_relation(x1, y1, x2, y2) + check_relation(x1, y1, x8, y8) + \
        check_relation(x5, y5, x4, y4) + check_relation(x5, y5, x6, y6) + \
        check_relation(x3, y3, x2, y2) + check_relation(x3, y3, x4, y4) + \
        check_relation(x7, y7, x6, y6) + check_relation(x7, y7, x8, y8)
    return b


def eliminate_agent_surroundings(x, y, scale):
    if 0 <= x - 1 < scale[0] and 0 <= y - 1 < scale[1]:
        s2_s = (x - 1) * scale[1] + (y - 1)
    else:
        s2_s = None
    if 0 <= x + 1 < scale[0] and 0 <= y - 1 < scale[1]:
        s4_s = (x + 1) * scale[1] + (y - 1)
    else:
        s4_s = None
    if 0 <= x + 1 < scale[0] and 0 <= y + 1 < scale[1]:
        s6_s = (x + 1) * scale[1] + (y + 1)
    else:
        s6_s = None
    if 0 <= x - 1 < scale[0] and 0 <= y + 1 < scale[1]:
        s8_s = (x - 1) * scale[1] + (y + 1)
    else:
        s8_s = None
    return s2_s, s4_s, s6_s, s8_s


def eliminate_agent_path_conflict(back_points, agents_path):
    # print(agents_path)
    # for a in list(agents_path.keys()):
    #     for p in range(len(back_points)):
    #         if len(agents_path[a]) > 0:
    #             if back_points[p] == agents_path[a][0]:
    #                 del back_points[p]
    tar_list = []
    for a in list(agents_path.keys()):
        if len(agents_path[a]) > 0:
            tar_list.append(agents_path[a][0])
    back_points = list(set(back_points).difference(set(tar_list)))
    return back_points


def find_shortest_backtracking_path(scale, view_map, cur_x, cur_y, back_points):
    cur_p = scale[1] * cur_x + cur_y
    INF = 100000000

    def gen_ns(s):
        i = int(s / scale[1])
        j = int(s % scale[1])
        # sur = [[1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1], [0, -1], [1, -1]]
        sur = [[0, 1], [0, -1], [-1, 0], [1, 0]]
        ns = []
        for it in sur:
            if isinstance(view_map.Nodes, dict):
                if 0 <= i + it[0] < scale[0] and 0 <= j + it[1] < scale[1]:
                    ns_id = int((i + it[0]) * scale[1] + (j + it[1]))
                    if ns_id in list(view_map.Nodes.keys()):
                        if not view_map.Nodes[ns_id].blocked and view_map.Nodes[ns_id].danger_level == 0:
                            ns.append(ns_id)
            elif isinstance(view_map.Nodes, list):
                if 0 <= i + it[0] < scale[0] and 0 <= j + it[1] < scale[1]:
                    if i + it[0] < len(view_map.Nodes):
                        if j + it[1] < len(view_map.Nodes[0]):
                            ns_id = int((i + it[0]) * scale[1] + (j + it[1]))
                            if not view_map.Nodes[i + it[0]][j + it[1]].blocked \
                                    and view_map.Nodes[i + it[0]][j + it[1]].danger_level == 0:
                                ns.append(ns_id)
        return ns

    def cal_dis(s, s_):
        i = int(s / scale[1])
        j = int(s % scale[1])
        i_ = int(s_ / scale[1])
        j_ = int(s_ % scale[1])
        dis = abs(i_ - i) + abs(j_ - j)
        if isinstance(view_map.Nodes, dict):
            if view_map.Nodes[s].blocked or view_map.Nodes[s_].blocked \
                    or view_map.Nodes[s].danger_level > 0 or view_map.Nodes[s_].danger_level > 0:
                dis = INF
        elif isinstance(view_map.Nodes, list):
            if view_map.Nodes[i][j].blocked or view_map.Nodes[i_][j_].blocked \
                    or view_map.Nodes[i][j].danger_level > 0 or view_map.Nodes[i_][j_].danger_level > 0:
                dis = INF
        return dis

    def greedy_a_star_search():

        def cal_h():
            result = {}
            if isinstance(view_map.Nodes, dict):
                for s_id in list(view_map.Nodes.keys()):
                    result[s_id] = INF
                    for p_id in back_points:
                        if result[s_id] > cal_dis(s_id, p_id):
                            result[s_id] = cal_dis(s_id, p_id)
            elif isinstance(view_map.Nodes, list):
                for i in range(len(view_map.Nodes)):
                    for j in range(len(view_map.Nodes[i])):
                        s_id = i * scale[1] + j
                        result[s_id] = INF
                        for p_id in back_points:
                            if result[s_id] > cal_dis(s_id, p_id):
                                result[s_id] = cal_dis(s_id, p_id)
            return result

        def cal_g():
            result = dict({})
            if isinstance(view_map.Nodes, dict):
                for s_id in list(view_map.Nodes.keys()):
                    result[s_id] = INF
            elif isinstance(view_map.Nodes, list):
                for i in range(len(view_map.Nodes)):
                    for j in range(len(view_map.Nodes[i])):
                        s_id = i * scale[1] + j
                        result[s_id] = INF
            result[cur_p] = 0
            return result

        # initialize
        h = cal_h()
        g = cal_g()
        # print(h)
        # print(g)

        # path = []
        closed = []
        f = {cur_p: h[cur_p]}
        parent = {cur_p: cur_p}
        open_list = [[cur_p, f[cur_p]]]
        while len(open_list) > 0:
            open_list.sort(key=lambda x: x[1])  # sort by the second column from smaller to bigger
            rm_s = open_list.pop(0)
            s = rm_s[0]
            if s in back_points:
                s_ = s
                path = [s_]
                while parent[s_] != cur_p:
                    s_ = parent[s_]
                    path.append(s_)
                path.append(cur_p)
                # print("returned path:", path)
                return path
            closed.append(s)
            ns = gen_ns(s)
            # print("ns:", ns)
            for s_ in ns:
                if s_ not in closed:
                    tmp_open = np.array(open_list)
                    if len(tmp_open) == 0:
                        g[s_] = INF
                    else:
                        if s_ not in list(tmp_open[:, 0]):
                            g[s_] = INF
                    dis = cal_dis(s, s_)
                    # print("estimated dis from s to s_:", dis)
                    # print("current dis g[s],g[s_]:", g[s], g[s_])
                    if g[s] + dis < g[s_]:
                        g[s_] = g[s] + dis
                        f[s_] = g[s_] + h[s_]
                        parent[s_] = s
                        if s_ not in tmp_open:
                            # print("append something into open list")
                            open_list.append([s_, f[s_]])

    back_path = greedy_a_star_search()
    if back_path:
        tar = back_path[0]
        target_x = int(tar / scale[1])
        target_y = int(tar % scale[1])
        return target_x, target_y, back_path
    else:
        return None, None, None
