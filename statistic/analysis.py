import pstats

# 创建Stats对象
p = pstats.Stats("/Users/chuwenjie/PycharmProjects/MultiViewAgent/log/5_5_4_04171516_2.0/center_func.out")

# strip_dirs(): 去掉无关的路径信息
# sort_stats(): 排序，支持的方式和上述的一致
# print_stats(): 打印分析结果，可以指定打印前几行

# # 和直接运行cProfile.run("test()")的结果是一样的
# p.strip_dirs().sort_stats(-1).print_stats()
#
# # 按照函数名排序，只打印前3行函数的信息, 参数还可为小数,表示前百分之几的函数信息
# p.strip_dirs().sort_stats("name").print_stats(3)

# 按照运行时间和函数名进行排序
p.strip_dirs().sort_stats("cumulative", "name").print_stats(0.1)

# # 如果想知道有哪些函数调用了sum_num
p.print_callers(0.1, "process_request_in_queue")
p.print_callers(0.1, "socket_communication")
p.print_callers(0.1, "safe_execute")

# 查看test()函数中调用了哪些函数
p.print_callees("process_request_in_queue")
# 查看test()函数中调用了哪些函数
p.print_callees("socket_communication")

p1 = pstats.Stats("/Users/chuwenjie/PycharmProjects/MultiViewAgent/log/5_5_4_04171516_2.0/hybrid_func.out")
p1.strip_dirs().sort_stats("cumulative", "name").print_stats(0.1)

p1.print_callers(0.1, "connect_with_center")

p2 = pstats.Stats("/Users/chuwenjie/PycharmProjects/MultiViewAgent/log/5_5_4_04171516_2.0/broadcast_func.out")
p2.strip_dirs().sort_stats("cumulative", "name").print_stats(0.1)

# from threading import Thread
# import time

# def test(n):
#     result = 1
#     for i in range(n):
#         result = result * i
#     return result
#
# run_test = Thread(target=test, args=(100000,))
# run_test.start()
#
# start_t = time.clock()
# run_test.join()
# end_t = time.clock()
# print(end_t-start_t)