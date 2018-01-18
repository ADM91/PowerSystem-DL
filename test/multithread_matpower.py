from multiprocessing import Pool, Process, Lock
from multiprocessing.managers import BaseManager
import timeit
from oct2py import Oct2Py
from oct2py import octave
from time import sleep
from copy import copy, deepcopy
octave.addpath('/home/alexander/Documents/MATLAB/matpower6.0')

import numpy as np
from oct2py import octave
from auxiliary.config import mp_opt, line_ratings, deconstruct_1, deconstruct_3
from optimize.RestorationTreeParallel import RestorationTree
from system.PowerSystem import PowerSystem

np.set_printoptions(precision=2)

# Evaluate base case power system
base_case = octave.loadcase('case14')
base_case['branch'][:, 5] = line_ratings  # Have to add line ratings
base_result = octave.runpf(base_case, mp_opt)

# Instantiate PowerSystem class
ps = PowerSystem(base_result,
                 spad_lim=10,
                 deactivated=deconstruct_3,
                 verbose=0,
                 verbose_state=0)
# tree = RestorationTree(ps)

# Create base manager:
m = BaseManager()
m.register('tree', RestorationTree, exposed=['fill_root_tree', 'create_nodes', 'root', 'action_list'])
m.start()
tree = m.tree()


s = []
l = Lock()
p = Pool(processes=3)
p.apply_async(test_shared_var, (l, tree, 1,))
p.apply_async(test_shared_var, (l, tree, 2,))
p.apply_async(test_shared_var, (l, tree, 3,))
p.apply_async(test_shared_var, (l, tree, 4,))
p.apply_async(test_shared_var, (l, tree, 5,))


def test_shared_tree_object(lock, tree, number):

    tree.create_nodes()





def test_opf(case):
    start = timeit.default_timer()
    oc = Oct2Py()
    oc.addpath('/home/alexander/Documents/MATLAB/matpower6.0')
    base_result = oc.runopf(case)
    stop = timeit.default_timer()

    return stop - start


def test_shared_var(shared, inp):
    sleep(1)
    shared = shared.append(inp)
    print(shared)


def start_process(s, val):
    p = Process(target=test_shared_var, args=(s, val))
    p.start()


for i in range(5):
    start_process(i)




c = octave.loadcase('case14')
p = Pool(processes=6)
start = timeit.default_timer()
p.map(test_opf, (c,c,c,c,c,c,c,c,c,c,c,c,c,c,c,c,c,c,c,c,c,c,c))
stop = timeit.default_timer()

print(stop - start)

# import threading
# import time
# import timeit
# from oct2py import Oct2Py
# import oct2py
# # from copy import deepcopy
# # oct2py.octave.addpath('/home/alexander/Documents/MATLAB/matpower6.0')
#
# exitFlag = 0
#
#
# class myThread(threading.Thread):
#
#     def __init__(self, name, case):
#         threading.Thread.__init__(self)
#         self.oct = Oct2Py()
#         self.oct.addpath('/home/alexander/Documents/MATLAB/matpower6.0')
#         self.name = name
#         self.case = case
#
#     def run(self):
#         print("Starting " + self.name)
#         test_opf(self.name, self.case, self.oct)
#         print("Exiting " + self.name)
#
#
# def test_opf(thread_name, case, octave):
#
#     mpc = octave.loadcase(case)
#     start = timeit.default_timer()
#     base_result = octave.runopf(mpc)
#     stop = timeit.default_timer()
#
#     print("%s: execution time %s" % (thread_name, stop-start))
#
#
# # Create new threads
# thread1 = myThread("Thread-1", 'case14')
# thread2 = myThread("Thread-2", 'case14')
#
# # Start new Threads
# start = timeit.default_timer()
# thread1.start()
# thread2.start()
# thread1.join()
# thread2.join()
# stop = timeit.default_timer()
# print(stop-start)












# def print_time(threadName, counter, delay):
#    while counter:
#       if exitFlag:
#          threadName.exit()
#       time.sleep(delay)
#       print("%s: %s" % (threadName, time.ctime(time.time())))
#       counter -= 1


















