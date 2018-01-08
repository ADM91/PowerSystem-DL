from optimize.execute_sequence import execute_sequence_2
from objective.objective_function import objective_function


def test_sequence(ps, sequence, action_map):

    ps.reset()
    state_list = execute_sequence_2(ps, sequence, action_map)
    [time_store, energy_store, cost_store] = objective_function(state_list, ps.ideal_state)

    return [state_list, time_store, energy_store, cost_store]