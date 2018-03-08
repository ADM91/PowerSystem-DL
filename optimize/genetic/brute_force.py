import itertools
from auxiliary.open_path import safe_open_w
import pickle
from optimize.genetic.evaluate_individual import evaluate_individual
import numpy as np


def brute_force(ps, base_result, action_map, i, data, save_data, folder):

    perms = np.array(list(itertools.permutations(action_map.keys())))

    cost_list = []
    feasible_individuals = []
    for individual in perms:
        actions = [action_map[ind] for ind in individual]
        print('evaluating: %s' % actions)
        time_store, energy_store, cost_store, final_gene = evaluate_individual(ps, individual, action_map, start_over=0)
        if len(final_gene) > 0:
            cost_list.append(cost_store['combined total'])
            feasible_individuals.append(final_gene)

    if len(cost_list) > 0:
        order = np.argsort(cost_list)
        cost_list = np.array(cost_list)
        feasible_individuals = np.array(feasible_individuals)
        print('\nOpt iter: %s (Brute force)' % i)
        print('population fitness: \n%s\n' % cost_list[order])
        print('population genes:\n%s\n' % feasible_individuals[order])

        fittest_individual = feasible_individuals[np.argmin(cost_list), :]
        best_total_cost_store = np.min(cost_list)

        # Save the key opt data
        data['action_sequence_store'] = fittest_individual
        data['best_total_cost_store'] = best_total_cost_store
        data['metadata'] = ps.metadata
        data['spad_lim'] = ps.spad_lim
        data['deactivated'] = ps.deactivated
        data['base_result'] = base_result

        # Save data dictionary to file!
        print('saving data from brute force! cost_list: %s' % cost_list)
        if save_data:
            with safe_open_w("data/%s/optimization_%s.pickle" % (folder, i), 'wb') as output_file:
                pickle.dump(data, output_file)
    else:
        print('\nOpt iter: %s (Brute force) NO SUITABLE INDIVIDUALS' % i)

        return
