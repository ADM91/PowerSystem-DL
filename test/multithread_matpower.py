
from copy import deepcopy

import numpy as np
from oct2py import octave
from optimize.stochastic_tree_search_parallel import stochastic_tree_search_parallel

from auxiliary.action_map import create_action_map
from auxiliary.config import mp_opt, line_ratings, deconstruct_1, deconstruct_3
from optimize.stochastic.stochastic_tree_search_thread import stochastic_tree_search_thread
from system.PowerSystem import PowerSystem
# from multiprocessing import Pool, Process, Lock, Manager, Value
# from multiprocessing.managers import BaseManager
from tree.RestorationTreeParallel import create_shared_root

np.set_printoptions(precision=2)

# Evaluate base case power system
base_case = octave.loadcase('case14')
base_case['branch'][:, 5] = line_ratings  # Have to add line ratings
base_result = octave.runpf(base_case, mp_opt)

# Instantiate PowerSystem class
ps = PowerSystem(base_result,
                 spad_lim=10,
                 deactivated=deconstruct_1,
                 verbose=0,
                 verbose_state=0)

action_map = create_action_map(ps.action_list)

# tree = RestorationTree()
# tree.fill_root(deepcopy(ps.current_state), deepcopy(ps.islands), deepcopy(ps.action_list))
# root = create_root(deepcopy(ps.current_state), deepcopy(ps.islands), deepcopy(ps.action_list))

# -------------------------------------
# Create access manager for root node:
# -------------------------------------
# man = BaseManager()
# man.register('Node', Node)
# man.start()
# man.
root = create_shared_root(deepcopy(ps.current_state), deepcopy(ps.islands), deepcopy(ps.action_list))

ps_inputs = [base_result, 10, deconstruct_3, 0, 0]

data = stochastic_tree_search_parallel(root,
                                       1,
                                       30,
                                       ps_inputs,
                                       method='cost',
                                       verbose=0,
                                       save_data=0,
                                       folder='test',
                                       n_processes=3)

# Test stuff that doesnt work!
# ---------------------------
from multiprocessing import Manager, Value, Lock, Pool, Process
from multiprocessing.managers import BaseManager


class MyManager(BaseManager):
    pass

# -------------------------------------
# Create manager for data storage dictionary
# -------------------------------------
data_man = Manager()
data = data_man.dict()

# -------------------------------------
# Create access manager for tree object:
# -------------------------------------
# tree_man = MyManager()
# tree_man.register('tree', RestorationTree, exposed=('fill_root', 'create_nodes'))
# tree_man.start()
# tree = tree_man.tree

# Optimization data dictionary
data['opt %s' % 0] = {}

# -------------------------------------
# Reset key data storage variables
# -------------------------------------
man_1 = Manager()
man_2 = Manager()
man_3 = Manager()
action_sequence_store = man_1.list()
total_cost_store = man_2.list()
best_total_cost_store = man_3.list()

# -------------------------------------
# Reset cheapest restoration value
# -------------------------------------
cheapest = Value('f', 9999999)

# -------------------------------------
# Create lock and process pool:
# -------------------------------------
lock = Lock()
pool = Pool(processes=3)

# Pack all arguments
stuff = [0, 0,
         ps,
         tree,
         data, total_cost_store, best_total_cost_store, action_sequence_store, cheapest,
         lock,
         'cost',
         action_map,
         0]
print(stuff)

# Initiate process within pool
pool.apply_async(stochastic_tree_search_thread, (stuff,))

p = Process(target=stochastic_tree_search_thread, args=(stuff,))

# tree = RestorationTree(ps)

# Create base manager:
# m = BaseManager()
# m.register('tree', RestorationTree, exposed=['fill_root_tree', 'create_nodes', 'root', 'action_list'])
# m.start()
# tree = m.tree()
#
#
# s = []
# l = Lock()
# p = Pool(processes=3)
# p.apply_async(test_shared_var, (l, tree, 1,))
# p.apply_async(test_shared_var, (l, tree, 2,))
# p.apply_async(test_shared_var, (l, tree, 3,))
# p.apply_async(test_shared_var, (l, tree, 4,))
# p.apply_async(test_shared_var, (l, tree, 5,))
#
#
# def test_shared_tree_object(lock, tree, number):
#
#     tree.create_nodes()
#
#
#
#
#
# def test_opf(case):
#     start = timeit.default_timer()
#     oc = Oct2Py()
#     oc.addpath('/home/alexander/Documents/MATLAB/matpower6.0')
#     base_result = oc.runopf(case)
#     stop = timeit.default_timer()
#
#     return stop - start
#
#
# def test_shared_var(shared, inp):
#     sleep(1)
#     shared = shared.append(inp)
#     print(shared)
#
#
# def start_process(s, val):
#     p = Process(target=test_shared_var, args=(s, val))
#     p.start()
#
#
# for i in range(5):
#     start_process(i)
#
#
#
#
# c = octave.loadcase('case14')
# p = Pool(processes=6)
# start = timeit.default_timer()
# p.map(test_opf, (c,c,c,c,c,c,c,c,c,c,c,c,c,c,c,c,c,c,c,c,c,c,c))
# stop = timeit.default_timer()
#
# print(stop - start)

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


















