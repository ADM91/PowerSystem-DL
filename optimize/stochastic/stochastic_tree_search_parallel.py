import pickle
# from multiprocessing import Pool, Process, Lock, Manager, Value
from threading import Lock, Thread, active_count
from time import sleep

from anytree import Walker

from auxiliary.action_map import create_action_map
from auxiliary.open_path import safe_open_w
# from multiprocessing.managers import BaseManager
from optimize.stochastic.stochastic_tree_search_thread import stochastic_tree_search_thread
from system.PowerSystem import PowerSystem

# Instantiate tree walker for data collection
w = Walker()


def stochastic_tree_search_parallel(root,
                                    opt_iteration,
                                    res_iteration,
                                    ps_inputs,
                                    method='cost',
                                    verbose=0,
                                    save_data=0,
                                    folder='test',
                                    n_processes=3):

    print('Started stochastic tree search')

    [base_result,
     spad_lim,
     deactivated,
     ps_verbose,
     verbose_state] = ps_inputs

    # -------------------------------------
    # Create manager for data storage dictionary
    # -------------------------------------
    # data_man = Manager()
    # data = data_man.dict()
    data = {}

    for i in range(opt_iteration):

        # Optimization data dictionary
        data['opt %s' % i] = {}

        # -------------------------------------
        # Reset key data storage variables
        # -------------------------------------
        # man_1 = Manager()
        # man_2 = Manager()
        # man_3 = Manager()
        # action_sequence_store = man_1.list()
        # total_cost_store = man_2.list()
        # best_total_cost_store = man_3.list()
        action_sequence_store = []
        total_cost_store = []
        best_total_cost_store = []

        # -------------------------------------
        # Reset cheapest restoration value
        # -------------------------------------
        # cheapest = Value('f', 9999999)
        cheapest = 9999999

        # -------------------------------------
        # Create lock and process pool:
        # -------------------------------------
        lock = Lock()
        l_data = Lock()
        l_total_cost_store = Lock()
        l_best_total_cost_store = Lock()
        l_action_sequence_store = Lock()
        l_cheapest = Lock()
        # pool = Pool(processes=n_processes)

        # Create threads
        threads = []
        for ii in range(res_iteration):
            # Instantiate a power system class for each thread/process
            ps = PowerSystem(base_result,
                             spad_lim=spad_lim,
                             deactivated=deactivated,
                             verbose=ps_verbose,
                             verbose_state=verbose_state)

            # Creates a fixed dictionary of integer - action pairs
            action_map = create_action_map(ps.action_list)

            # Pack all arguments
            stuff = [i, ii,
                     ps,
                     root,
                     data, total_cost_store, best_total_cost_store, action_sequence_store, cheapest,
                     l_data, l_total_cost_store, l_best_total_cost_store, l_action_sequence_store, l_cheapest,
                     lock,
                     method,
                     action_map,
                     verbose]

            threads.append(Thread(name='opt %s iter %s' % (i, ii), target=stochastic_tree_search_thread, args=(stuff,)))

        # Run all iterations
        while len(threads) > 0:
        # for ii in range(res_iteration):
            print('active threads: %s' % active_count())

            # Only allow x threads at a time
            if len(threads) >= 0 and active_count() <= 8:
                print('outside: initiating optimization %s, restoration %s' % (i, len(threads)))

                threads.pop().start()

                # # Instantiate a power system class for each thread/process
                # ps = PowerSystem(base_result,
                #                  spad_lim=spad_lim,
                #                  deactivated=deactivated,
                #                  verbose=ps_verbose,
                #                  verbose_state=verbose_state)
                #
                # # Creates a fixed dictionary of integer - action pairs
                # action_map = create_action_map(ps.action_list)
                #
                # # Pack all arguments
                # stuff = [i, count,
                #          ps,
                #          root,
                #          data, total_cost_store, best_total_cost_store, action_sequence_store, cheapest,
                #          l_data, l_total_cost_store, l_best_total_cost_store, l_action_sequence_store, l_cheapest,
                #          lock,
                #          method,
                #          action_map,
                #          verbose]
                #
                # t = Thread(name='opt %s iter %s' % (i, count), target=stochastic_tree_search_thread, args=(stuff,))

                # Decrement count by one
                # count += 1

                # Initiate process within pool
                # pool.apply(stochastic_tree_search_thread, (stuff,))
            sleep(5)


        # pool.close()
        # pool.join()

        # Save optimization run data to optimization dictionary
        data['opt %s' % i]['action_sequence_store'] = action_sequence_store
        data['opt %s' % i]['total_cost_store'] = total_cost_store
        data['opt %s' % i]['best_total_cost_store'] = best_total_cost_store

    # Save data dictionary to file!
    if save_data:
        with safe_open_w("data/%s/optimization_dict.pickle" % folder, 'wb') as output_file:
            pickle.dump(data, output_file)

    # return data
