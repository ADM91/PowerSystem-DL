from auxiliary.open_path import safe_open_w
import pickle
from optimize.action_map import create_action_map
from objective.objective_function import objective_function
import numpy as np
from copy import deepcopy
from anytree import Walker
from auxiliary.integrate_dict import integrate_dict
from multiprocessing import Pool, Process, Lock, Manager, Value
from multiprocessing.managers import BaseManager
from optimize.stochastic_tree_search_thread import stochastic_tree_search_thread

# Instantiate tree walker for data collection
w = Walker()


def stochastic_tree_search(ps, tree, opt_iteration, res_iteration, method='cost', verbose=0, save_data=0, folder='test', n_processes=3):

    # Creates a fixed dictionary of integer - action pairs
    action_map = create_action_map(ps.action_list)

    # -------------------------------------
    # Create manager for data storage dictionary
    # -------------------------------------
    data_man = Manager()
    data = data_man.dict()

    # -------------------------------------
    # Create access manager for tree object:
    # -------------------------------------
    tree_man = BaseManager()
    tree_man.register('tree', tree, exposed=['fill_root_tree', 'create_nodes', 'root', 'action_list'])
    tree_man.start()
    tree = tree_man.tree()

    # -------------------------------------
    # Create lock and process pool:
    # -------------------------------------
    lock = Lock()
    pool = Pool(processes=n_processes)

    for i in range(opt_iteration):

        # Optimization data dictionary
        data['opt %s' % i] = {}

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
        cheapest = Value(9999999)

        # Run all iterations
        for ii in range(res_iteration):
            # Pack all arguments
            stuff = [i, ii,
                     deepcopy(ps),
                     tree,
                     data, total_cost_store, best_total_cost_store, action_sequence_store, cheapest,
                     lock,
                     method,
                     action_map,
                     verbose]
            pool.apply_async(stochastic_tree_search_thread, (stuff,))

        # Save optimization run data to optimization dictionary
        data['opt %s' % i]['action_sequence_store'] = action_sequence_store
        data['opt %s' % i]['total_cost_store'] = total_cost_store
        data['opt %s' % i]['best_total_cost_store'] = best_total_cost_store

    # Save data dictionary to file!
    if save_data:
        with safe_open_w("data/%s/optimization_dict.pickle" % folder, 'wb') as output_file:
            pickle.dump(data, output_file)

    return data, action_map
