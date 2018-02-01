from multiprocessing import Pool, Lock, Manager, Process, active_children
from optimize.genetic.optimization_parallel import optimization_parallel
from time import sleep

def genetic_alg_parallel(ps_inputs, pop_size, iterations, optimizations, eta, folder='test', save_data=1, n_processes=1):

    # Multiprocessing variables
    # pool = Pool(processes=n_processes)
    # man = Manager()
    # lock = Lock()

    # Create processes containing optimization
    processes = []
    for i in range(optimizations):
        processes.append(Process(target=optimization_parallel, args=(ps_inputs, pop_size, iterations, i, eta, folder, save_data)))
        # pool.apply_async(optimization_parallel, args=(ps_inputs, pop_size, iterations, i, eta, data, lock))

    # Run processes, limit total active processes to 7
    while len(processes) > 0:

        print('active child processes: %s ' % len(active_children()))
        if len(active_children()) < 6:
            print('kicking off process')
            p = processes.pop()
            p.start()
        else:
            sleep(1)
