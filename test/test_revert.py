from copy import deepcopy
from optimize.execute_sequence import execute_sequence_2
from objective.objective_function import objective_function


def test_revert(ps, actions, action_map):

    # This function tests the revert function of the PowerSystem class, to validate its performance.
    state_store = []
    time_store = []
    energy_store = []
    cost_store = []

    # Deepcopy relevant ps attributes
    islands = deepcopy(ps.islands)
    state = deepcopy(ps.current_state)
    islands_evaluated = deepcopy(ps.islands_evaluated)

    for action in actions:

        states = list()

        # Snapshot of initial state
        states.append(ps.current_state)

        # Perform action
        intermediate_states = execute_sequence_2(ps, action, action_map)
        for s in intermediate_states:
            states.append(s)

        # Evaluate objective function for action
        [time, energy, cost] = objective_function(intermediate_states, ps.ideal_state)

        ps.revert(state, islands, islands_evaluated)
        states.append(ps.current_state)

        state_store.append(states)
        time_store.append(time)
        energy_store.append(energy)
        cost_store.append(cost)

    return [state_store, time_store, energy_store, cost_store]

# # Second action
# ps.action_line([5, 6])
# islands = deepcopy(ps.islands)
# state = deepcopy(ps.current_state)
# blackout_conn = deepcopy(ps.blackout_connections)
# states.append(ps.current_state)
# ps.action_line([6, 12])
# ps.revert(islands, state, blackout_conn)
# states.append(ps.current_state)
#
# # Third action
# ps.action_line([6, 12])
# islands = deepcopy(ps.islands)
# state = deepcopy(ps.current_state)
# blackout_conn = deepcopy(ps.blackout_connections)
# states.append(ps.current_state)
# ps.action_line([9, 10])
# ps.revert(islands, state, blackout_conn)
# states.append(ps.current_state)