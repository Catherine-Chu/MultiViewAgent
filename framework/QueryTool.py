# -*- coding:utf-8 -*-

import psycopg2

class QueryTool:

    def __init__(self, database):
        self.database = database
        self.user = 'postgres'
        self.password = '2399321cwj'
        self.host = '127.0.0.1'
        self.port = '5432'
        self.conn = psycopg2.connect(database=self.database, user=self.user, password=
                                     self.password, host=self.host, port=self.port)
        self.conn.set_session(autocommit=True)
        self.cur = self.conn.cursor()


    def get_view(self,view_name):
        # 下列语句中只返回后半句的结果
        # self.cur.execute("SELECT * FROM public.{}; SELECT * FROM public.{};".format(view_name[0],view_name[1]))
        # 下列语句两句都会执行
        # self.cur.execute("UPDATE public.grid_nodes SET visited=True WHERE node_id=0;"
        #                  "UPDATE public.grid_nodes SET visited=True WHERE node_id=1;")
        self.cur.execute("SELECT * FROM public.{}".format(view_name))
        rows = self.cur.fetchall()
        colnames = [desc[0] for desc in self.cur.description]
        return colnames, rows

    def clear_db_connection(self):
        self.conn.commit()
        self.cur.close()
        self.conn.close()

if __name__ == '__main__':
    qt = QueryTool(database='multiAgents')
    # colnames, rows = qt.get_view(view_name='drone_local_nodes')
    qt.cur.execute('UPDATE drone_local_nodes SET victims_num = 5 WHERE uav_id = 0 and node_id = 6')
    print(qt.cur.query)
    print(qt.cur.statusmessage)
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