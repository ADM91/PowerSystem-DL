from copy import deepcopy
from optimize.execute_sequence import execute_sequence_2
from objective.objective_function import objective_function
from numpy import float64


def iterable(a):
    if type(a) in [int, float, float64]:
        return [a]
    else:
        return a


def integrate_dict(dict1, dict2):

    # Combines the contents of two similar dictionaries
    for key in dict1.keys():
        if key in dict2.keys():
            for item in iterable(dict2[key]):
                dict1[key].append(item)
        else:
            print('Error: dictionary keys do not match!!!')

    return dict1


def test_revert(ps, actions, action_map):

    # This function tests the revert function of the PowerSystem class, to validate its performance.
    state_store = []
    island_store = []
    time_store = []
    energy_store = {'lost load': [],
                    'losses': [],
                    'dispatch deviation': []}
    cost_store = {'lost load': [],
                  'losses': [],
                  'dispatch deviation': [],
                  'total': [],
                  'combined total': []}

    # Deepcopy relevant ps attributes
    islands = deepcopy(ps.islands)
    state = deepcopy(ps.current_state)
    ideal_state = deepcopy(ps.ideal_state)

    for action in actions:

        # Perform action
        intermediate_states, intermediate_islands = execute_sequence_2(ps, action, action_map)
        for s, i in zip(intermediate_states, intermediate_islands):
            state_store.append(s)
            island_store.append(i)

        # Evaluate objective function for action
        [time, energy, cost] = objective_function(intermediate_states, ideal_state)

        ps.revert(state, islands)

        # Append inside dictionary
        for t in time:
            time_store.append(t)
        energy_store = integrate_dict(energy_store, energy)
        cost_store = integrate_dict(cost_store, cost)

    return [state_store, island_store, time_store, energy_store, cost_store]



