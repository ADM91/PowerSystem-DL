from copy import deepcopy
from optimize.execute_sequence import execute_sequence_2
from objective.objective_function import objective_function
from auxiliary.integrate_dict import integrate_dict


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

        # print('Arguments to revert function')
        # print(state['real inj'][17, [2, 4]])
        # print(islands['0']['branch'][17, 10:13])

        ps.revert(state, islands)

        # print('After revert (outside the class)')
        # print(ps.current_state['real inj'][17, [2, 4]])
        # print(ps.islands['0']['branch'][17, 10:13])

        # Append inside dictionary
        for t in time:
            time_store.append(t)
        energy_store = integrate_dict(energy_store, energy)
        cost_store = integrate_dict(cost_store, cost)

    return [state_store, island_store, time_store, energy_store, cost_store]



