from framework.Center import *
from framework.Drones import *

if __name__ == "__main__":
    # initializing database
    with open(file='../data/metadata.json', mode='r') as fr:
        metadata = json.loads("".join(fr.readlines()))['metadata']
        dg = GlobalDataInitializer(agent_num=metadata['agent_num'],
                                   map_width=metadata['width'],
                                   map_height=metadata['height'],
                                   charge_num=metadata['charge_num'],
                                   danger_num=metadata['danger_num'],
                                   charge_pos_list=metadata['charge_pos_list'],
                                   obstacle_num=metadata['obstacle_num'],
                                   db_used=True
                                   )
        dg.initNewMapViews()
        dg.initNewAgentViews()
        dg.initNewTaskViews()
        dg.ClearDBInitializer()

    # initializing concrete environment data
    qtool = QueryTool(database='multiAgents')
    col_nms_1, rows_1 = qtool.get_view(view_name='drones_cur_state')
    col_nms_2, rows_2 = qtool.get_view(view_name='charging_stations_config')
    col_nms_3, rows_3 = qtool.sql_execute(query="SELECT * FROM public.drones_cur_state,public.drones_config "
                                                "WHERE drones_config.uav_id = drones_cur_state.uav_id "
                                                "AND drones_config.fleet_id = 0")
    col_nms_4, rows_4 = qtool.sql_execute(query="SELECT * FROM public.drones_cur_state,public.drones_config "
                                                "WHERE drones_config.uav_id = drones_cur_state.uav_id "
                                                "AND drones_config.fleet_id = 1")
    col_nms_5, rows_5 = qtool.sql_execute(query="SELECT * FROM public.drones_cur_state,public.drones_config "
                                                "WHERE drones_config.uav_id = drones_cur_state.uav_id "
                                                "AND drones_config.fleet_id = 2")
    qtool.clear_db_connection()

    drone_num = len(rows_1)
    drone_locs = [{}, {}, {}]
    for row in rows_3:
        drone_locs[0][row[col_nms_3.index('uav_id')]] = row[col_nms_3.index('loc_node_id')]
    for row in rows_4:
        drone_locs[1][row[col_nms_4.index('uav_id')]] = row[col_nms_4.index('loc_node_id')]
    for row in rows_5:
        drone_locs[2][row[col_nms_5.index('uav_id')]] = row[col_nms_5.index('loc_node_id')]
    charge_list = []
    for row in rows_2:
        charge_list.append(row[col_nms_2.index('node_id')])
    # metadata = '../data/metadata.json'
    # if metadata and os.path.isfile(metadata):
    #     with open(file=metadata, mode='r') as fr:
    #         metadata = json.loads("".join(fr.readlines()))['metadata']
    #         agent_g_num = metadata['agent_num']
    #         charge_pos_list = metadata['charge_pos_list']
    #         uav_count = 0
    #         drone_locs = []
    #         for j in range(len(agent_g_num)):
    #             drone_locs.append({})
    #             fleet_id = j
    #             for i in range(agent_g_num[j]):
    #                 uav_id = uav_count
    #                 uav_count += 1
    #                 if j != 2:
    #                     loc_node_id = random.randint(0, metadata['width'] * metadata['height'])
    #                 else:
    #                     loc_node_id = random.choice(charge_pos_list)
    #                 drone_locs[j][uav_id] = loc_node_id
    #         drone_num = uav_count
    # else:
    #     charge_list = []
    #     agent_g_num = [4]
    #     drone_locs = []
    #     uav_count = 0
    #     width = 10
    #     height = 10
    #     for j in range(len(agent_g_num)):
    #         drone_locs.append({})
    #         fleet_id = j
    #         for i in range(agent_g_num[j]):
    #             uav_id = uav_count
    #             uav_count += 1
    #             if j != 2:
    #                 loc_node_id = random.randint(0, width * height)
    #             else:
    #                 loc_node_id = random.choice(charge_list)
    #             drone_locs[j][uav_id] = loc_node_id
    #     drone_num = uav_count

    env = ConcreteEnv(charge_list=charge_list, drone_locs=drone_locs)

    # initializing shared parameters and locks in for simulating broadcasting
    # global_map = []
    # for i in range(drone_num):
    #     global_map.append(GlobalViewMap(scale=(env.width, env.height)))
    #
    # agents_path = []
    # next_pos = []
    # agents_pos = []
    # for i in range(drone_num):
    #     agents_path.append(dict({}))
    #     next_pos.append(dict({}))
    #     agents_pos.append(dict({}))
    #     for j in range(drone_num):
    #         agents_path[i][j] = []
    #         next_pos[i][j] = -1
    #
    # map_lock = []
    # paths_lock = []
    # next_lock = []
    # pos_lock = []
    # for i in range(drone_num):
    #     map_lock.append(Lock())
    #     paths_lock.append(Lock())
    #     next_lock.append(Lock())
    #     pos_lock.append(Lock())

    # initializing center object
    center = Center(metadata)

    # initializing agents container and running threads container
    fleet = []
    fleet_thread = []

    # start the threads for center
    process_thread = Thread(target=center.process_request_in_queue)
    process_thread.start()  # process thread

    # check_thread = Thread(target=center.check_state)
    # check_thread.start()  # check thread

    socket_thread = Thread(target=center.socket_communication)
    socket_thread.start()  # socket thread

    # start the threads for drones
    for i in range(drone_num):
        fleet.append(UAV(ID=i, experiment_config=ExperimentConfig()))
        # print(i)
        # print(int(drone_locs[0][i] / env.height))
        # print(int(drone_locs[0][i] % env.height))
        # print(int(drone_locs[0][i]))
        drone_con_thread = Thread(target=fleet[i].run, args=(env,))
        # drone_con_thread = Thread(target=fleet[i].test)
        fleet_thread.append(drone_con_thread)
        drone_con_thread.start()

    def center_drawing():
        W_ = center.experiment_config.W_Threshold
        C_ = center.experiment_config.C_Threshold
        timeout = center.experiment_config.timeout
        render_global_views(metadata['width'], metadata['height'], W_, C_, timeout)

    def agents_drawing():
        # drawing the concrete env and all drones current state and their local_view
        start_time = time.time()
        cur_pos = []
        cur_e = []
        cur_sr = []
        cur_f = []
        for i in range(drone_num):
            cur_pos.append([fleet[i].cur_PX, fleet[i].cur_PY])
            cur_f.append(fleet[i].FID)
            if fleet[i].cur_E >= fleet[i].E * (1 - fleet[i].experiment_config.W_Threshold):
                new_e = 0
            elif fleet[i].E * (1 - fleet[i].experiment_config.C_Threshold) <= fleet[i].cur_E < fleet[i].E * (
                    1 - fleet[i].experiment_config.W_Threshold):
                new_e = 1
            else:
                new_e = 2
            cur_e.append(new_e)
            cur_sr.append(fleet[i].SR)
        env_window = Cgrid(env=env, agents_info=(cur_pos, cur_e, cur_f), agents_view=cur_sr)
        # env_window.mainloop()

        while True:
            cur_pos = []
            cur_e = []
            cur_sr = []
            for i in range(drone_num):
                cur_pos.append([fleet[i].cur_PX, fleet[i].cur_PY])
                new_e = -1
                if fleet[i].cur_E >= fleet[i].E * (1 - fleet[i].experiment_config.W_Threshold):
                    new_e = 0
                elif fleet[i].E * (1 - fleet[i].experiment_config.C_Threshold) <= fleet[i].cur_E < fleet[i].E * (
                        1 - fleet[i].experiment_config.W_Threshold):
                    new_e = 1
                else:
                    new_e = 2
                cur_e.append(new_e)
                cur_sr.append(fleet[i].SR)
            s_ = env_window.step(env, cur_pos, cur_e, cur_sr)
            env_window.update_idletasks()
            env_window.update()
            time.sleep(0.1)
            time_elapse = time.time() - start_time
            if time_elapse > fleet[0].experiment_config.timeout:
                break

        # 线程结束前最后的收尾工作
        fw = open('../log/broadcast_statistic.txt', mode='w')
        with fw:
            for i in range(drone_num):
                fw.write("drone {} end work with path length {}.\n".format(i, fleet[i].cur_PLen))

    # center_draw_thread = Thread(target=center_drawing)
    # center_draw_thread.start()
    #
    # agents_draw_thread = Thread(target=agents_drawing)
    # agents_draw_thread.start()
    #
    # agents_draw_thread.join()
    for i in range(drone_num):
        fleet[i].terminate()
        fleet_thread[i].join()
    print("Drones' activities end!")

    # center_draw_thread.join()
    # time.sleep(10)  # waiting for ending listening
    socket_thread.join()
    # check_thread.join()
    process_thread.join()  # waiting for ending processing