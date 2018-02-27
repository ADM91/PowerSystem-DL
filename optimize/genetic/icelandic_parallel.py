from multiprocessing import Pool, Lock, Manager, Process, active_children
from time import sleep


def icelandic_parallel(ps_inputs, pop_size, iterations, attempts, eta, fun, folder='test', save_data=1, n_processes=1):

    # Create processes containing optimization
    processes = []
    for i in range(attempts):
        # Generate process objects
        processes.append(Process(target=fun, args=(ps_inputs, pop_size, iterations, i, eta, folder, save_data)))

    # Run processes, limit total active processes to 7
    baseline_p = len(active_children())
    while len(processes) > 0:

        print('active child processes: %s ' % len(active_children()))
        if len(active_children()) < baseline_p+n_processes:
            print('kicking off process')
            p = processes.pop()
            p.start()
        else:
            sleep(1)
