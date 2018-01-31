from optimize.execute_sequence import execute_sequence_2
from objective.objective_function import objective_function
from copy import deepcopy


def evaluate_individual(ps, individual, action_map, verbose=0):

    # Feasibility preserving evaluation
    store = []
    final_gene = []
    init_gene = list(individual)
    gene_length = len(individual)
    states = []

    ps.reset()

    # Execute until finial gene is complete
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
        time_store, energy_store, cost_store = objective_function(states, ps.ideal_state)
        return time_store, energy_store, cost_store, final_gene
    else:
        return [], []


