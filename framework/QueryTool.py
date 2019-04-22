# -*- coding:utf-8 -*-

import psycopg2
import json


class QueryTool:

    def __init__(self, database="multiAgents"):
        self.database = database
        self.user = 'postgres'
        self.password = '2399321cwj'
        self.host = '127.0.0.1'
        self.port = '5432'
        self.conn = psycopg2.connect(database=self.database, user=self.user, password=
        self.password, host=self.host, port=self.port)
        self.conn.set_session(autocommit=True)
        self.cur = self.conn.cursor()

    def get_view(self, view_name):
        # 下列语句中只返回后半句的结果
        # self.cur.execute("SELECT * FROM public.{}; SELECT * FROM public.{};".format(view_name[0],view_name[1]))
        # 下列语句两句都会执行
        # self.cur.execute("UPDATE public.grid_nodes SET visited=True WHERE node_id=0;"
        #                  "UPDATE public.grid_nodes SET visited=True WHERE node_id=1;")
        self.cur.execute("SELECT * FROM public.{}".format(view_name))
        rows = self.cur.fetchall()
        colnames = [desc[0] for desc in self.cur.description]
        return colnames, rows

    def update_drones_location(self, drone_ids, new_locs):
        for i in range(len(drone_ids)):
            for j in range(len(drone_ids[i])):
                self.cur.execute("UPDATE public.drones_cur_state "
                                 "SET loc_node_id = {} "
                                 "WHERE uav_id = {}".format(new_locs[i][j], drone_ids[i][j]))
        return True

    def sql_execute(self, query):
        try:
            self.cur.execute(query)
            rows = self.cur.fetchall()
            colnames = [desc[0] for desc in self.cur.description]
            return colnames, rows
        except psycopg2.ProgrammingError as exc:
            print(exc)
            self.conn.rollback()
            # self.cur = self.conn.cursor()
            # self.cur.execute(query)
            # rows = self.cur.fetchall()
            # colnames = [desc[0] for desc in self.cur.description]
            # return colnames, rows
        except psycopg2.InterfaceError as exc:
            print(exc)
            self.conn = psycopg2.connect(database=self.database,
                                                    user=self.user, password=
                                                    self.password, host=self.host,
                                                    port=self.port)
            self.cur = self.conn.cursor()
            # self.cur.execute(query)
            # rows = self.cur.fetchall()
            # colnames = [desc[0] for desc in self.cur.description]
            # return colnames, rows

    def safe_execute(self, query):
        try:
            self.cur.execute(query)
        except psycopg2.ProgrammingError as exc:
            print(exc)
            self.conn.rollback()
            # self.cur = self.conn.cursor()
            # self.cur.execute(query)
        except psycopg2.InterfaceError as exc:
            print(exc)
            self.conn = psycopg2.connect(database=self.database,
                                                    user=self.user, password=
                                                    self.password, host=self.host,
                                                    port=self.port)
            self.cur = self.conn.cursor()
            # self.cur.execute(query)

    def clear_db_connection(self):
        self.conn.commit()
        self.cur.close()
        self.conn.close()


if __name__ == '__main__':
    qt = QueryTool(database='multiAgents')
    # colnames, rows = qt.get_view(view_name='drone_local_nodes')
    qt.cur.execute('SELECT end_time FROM public.search_coverage_task '
                   'WHERE start_time IS NOT NULL AND end_time IS NULL '
                   'AND responsible_fleet_id = {} '.format(0))

    # print(qt.cur.query)
    # print(qt.cur.statusmessage)
    print(json.loads(json.dumps(qt.cur.fetchall())))
    qt.clear_db_connection()
    # print(colnames)
    # print(rows)
    # rows.insert(0,colnames)
    # print(rows)
    # # print(isinstance(colnames, list))
    # # print(isinstance(colnames, dict))
    # # print(isinstance(rows,list))
    # # print(isinstance(rows,dict))
    # a='[{"n1":1, "n2":0}]'
    # a = ast.literal_eval(a)
    # print(a)
    # print(a[0])
    # print(isinstance(a[0],list))
    # print(isinstance(a[0],tuple))
    # print(isinstance(a[0],dict))
    #
    # print(a[0]['n1'])
