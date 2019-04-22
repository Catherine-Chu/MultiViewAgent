# coding:utf-8

import threading


class MyThread(threading.Thread):
    def __init__(self, func, args=()):
        super(MyThread, self).__init__()
        self.func = func
        self.args = args
        self.result = None

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        threading.Thread.join(self)  # 等待线程执行完毕
        try:
            return self.result
        except Exception as e:
            print(e)
            return None


def print_test():
    print("Done!")


if __name__ == '__main__':
    test = MyThread(func=print_test)
    test.start()
    print(test.is_alive())
    print("here!")
    print(test.is_alive())
