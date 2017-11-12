import pickle
import numpy as np
from objective.objective_function import objective_function
from optimize.execute_sequence import execute_sequence
from optimize.sequence_decoder import decode_sequence
from optimize.delay_faulty_action import delay_faulty_action
from auxiliary.open_path import safe_open_w
import time



def random_search_opt(ps, opt_iteration, res_iteration, verbose=1, save_data=0, folder='test'):

    for i in range(opt_iteration):

        # Run random action permutations
        n_actions = int(np.sum([len(item) for item in ps.action_list.values()]))
        best_sequence = np.random.permutation(n_actions)
        best_total_cost = [9999999]

        # Reset data storage
        states_store = []
        time_store = []
        energy_store = []
        cost_store = []
        sequence_store = []

        for ii in range(res_iteration):
            start_time = time.time()

            # Random sequence permutation (rate changes with iteration)
            [a, b, c, d, e, f] = np.random.choice(n_actions, size=6, replace=False)
            test_sequence = best_sequence
            test_sequence[a], test_sequence[b] = test_sequence[b], test_sequence[a]
            if ii < int((2 / 3) * res_iteration):
                test_sequence[c], test_sequence[d] = test_sequence[d], test_sequence[c]
            if ii < int((1 / 3) * res_iteration):
                test_sequence[e], test_sequence[f] = test_sequence[f], test_sequence[e]
            action_sequence = decode_sequence(ps.action_list, test_sequence)

            # Sequence execution
            count = 0
            success = 0
            while count < 5:
                ps.reset()
                states = execute_sequence(ps, action_sequence)
                if states[0] == 'fail':
                    test_sequence = delay_faulty_action(test_sequence, states[1])
                    action_sequence = decode_sequence(ps.action_list, test_sequence)
                    if verbose:
                        print('--- Fail ----')
                else:
                    if verbose:
                        print('--- Success ----')
                    success = 1
                    break
                count += 1

            t1 = time.time() - start_time

            # Sequence evaluation
            if success:
                [restore_time, energy, cost] = objective_function(states, ps.ideal_state)

                if cost['combined total'] < best_total_cost[-1]:
                    states_store.append(states)
                    time_store.append(restore_time)
                    energy_store.append(energy)
                    cost_store.append(cost)
                    sequence_store.append(action_sequence)
                    best_total_cost.append(cost['combined total'])
                    best_sequence = test_sequence
                else:
                    best_total_cost.append(best_total_cost[-1])

                if verbose:
                    print("--- %s ---" % t1)
                    print('Iteration: %s' % ii)
                    print('Cost of restoration: %.1f' % cost['combined total'])
                    print('Lowest cost thus far: %.1f\n\n' % best_total_cost[-1])
            else:
                if verbose:
                    print('--- I gave up, moving on ----\n\n')

        # Save data to pickle
        if save_data:
            data = [states_store, time_store, energy_store, cost_store, sequence_store, best_total_cost]
            with safe_open_w("data/%s/rand_opt_%s.pickle" % (folder, i), 'wb') as output_file:
                pickle.dump(data, output_file)
