from copy import deepcopy
import numpy as np
from objective.objective_function import objective_function
from system.execute_sequence import execute_sequence_2


def evaluate_individual(ps, individual, action_map, verbose=0, start_over=1):

    # Feasibility preserving evaluation
    store = []
    final_gene = []
    init_gene = list(individual)
    gene_length = len(individual)
    states = []

    ps.reset()

    # Execute until finial gene is complete
    fail_count = 0
    while len(final_gene) < gene_length:

        # Save PowerSystem state in case reversion is necessary
        state = deepcopy(ps.current_state)
        islands = deepcopy(ps.islands)

        # Begin by executing actions in store
        flag = 0
        for val in store:
            state_list, island_list = execute_sequence_2(ps, val, action_map)
            if len(state_list) > 0:  # Success!
                store.remove(val)
                final_gene.append(val)
                for s in state_list:
                    states.append(s)
                flag = 1
                break
            else:  # Failure :(
                ps.revert(state, islands)
                if verbose:
                    print('reverted store action: %s' % action_map[val])

        # If value from store list was executed, continue to next loop iteration
        if flag == 1:
            continue

        # RARE: if there are unexecutable actions in the store array after the inital gene is depleted:
        if len(init_gene) == 0 and flag == 0:
            if start_over == 1:
                print('\nUnexecutable individual: reshuffling actions and starting over!\n ')
                # Reshuffle the actions:
                individual = np.random.permutation(list(action_map.keys()))
                # Restart the evaluation process
                store = []
                final_gene = []
                init_gene = list(individual)
                gene_length = len(individual)
                states = []
                ps.reset()
                state = deepcopy(ps.current_state)
                islands = deepcopy(ps.islands)
                fail_count += 1
                if fail_count >= 5:
                    return [], [], [], []
            else:
                return [], [], [], []

        # Execute action in initial gene
        val = init_gene[0]
        state_list, island_list = execute_sequence_2(ps, val, action_map)
        if len(state_list) > 0:  # Success!
            init_gene.remove(val)
            final_gene.append(val)
            for s in state_list:
                states.append(s)
        else:  # Failure :(
            store.append(val)
            init_gene.remove(val)
            ps.revert(state, islands)
            if verbose:
                print('reverted init gene action: %s' % action_map[val])

        if verbose:
            print('init_gene : %s' % init_gene)
            print('store: %s' % store)
            print('final_gene: %s\n' % final_gene)

    if len(final_gene) == gene_length:
        # Evaluate the objective function
        time_store, energy_store, cost_store = objective_function(states, ps.ideal_state, ps.metadata)
        if cost_store['combined total'] < 0:
            return [], [], [], []
        else:
            return time_store, energy_store, cost_store, final_gene
    else:
        return [], [], [], []


