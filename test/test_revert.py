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
    islands_evaluated = deepcopy(ps.islands_evaluated)
    ideal_state = deepcopy(ps.ideal_state)
    l1 = []  # for tracking state (should always return to the same state after revert)

    for action in actions:

        # Snapshot of initial state
        state_store.append(ps.current_state)

        # Perform action
        intermediate_states = execute_sequence_2(ps, action, action_map)
        for s in intermediate_states:
            state_store.append(s)

        l1.append(ps.islands_evaluated)

        # Evaluate objective function for action
        [time, energy, cost] = objective_function(intermediate_states, ideal_state)

        ps.revert(state, islands, islands_evaluated)


        # state_store.append(ps.current_state)

        # Append inside dictionary
        for t in time:
            time_store.append(t)
        energy_store = integrate_dict(energy_store, energy)
        cost_store = integrate_dict(cost_store, cost)

    return [state_store, time_store, energy_store, cost_store], l1



