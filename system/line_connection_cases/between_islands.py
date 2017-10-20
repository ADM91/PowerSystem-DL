from copy import deepcopy
import numpy as np


def between_islands(ps, island_1, island_2):

    state_list = list()

    # Get the state prior to connection
    ps.evaluate_islands()
    prelim_state = ps.evaluate_state(list(ps.islands_evaluated.values()))
    prelim_state['Title'] = 'Island reconnection preliminary state'  # Shows up on plot
    state_list.append(prelim_state)
    
    # Append all of island 2 to island 1
    island_2_copy = deepcopy(ps.islands[ps.island_map[island_2]])
    ps.islands[ps.island_map[island_1]]['bus'] = np.append(ps.islands[ps.island_map[island_1]]['bus'], island_2_copy['bus'], axis=0)
    ps.islands[ps.island_map[island_1]]['branch'] = np.append(ps.islands[ps.island_map[island_1]]['branch'], island_2_copy['branch'], axis=0)
    ps.islands[ps.island_map[island_1]]['gen'] = np.append(ps.islands[ps.island_map[island_1]]['gen'], island_2_copy['gen'], axis=0)
    ps.islands[ps.island_map[island_1]]['gencost'] = np.append(ps.islands[ps.island_map[island_1]]['gencost'], island_2_copy['gencost'], axis=0)
    
    # Delete island 2
    del ps.islands[ps.island_map[island_2]]

    # TODO: do this better, it gave me an error... or don't do it at all?
    # Remember: to remove the weaker of the swing buses!
    # ind = ps.islands[ps.island_map[island_1]]['bus'][:, 1] == 3
    # # print(ind)
    # bus_id = ps.islands[ps.island_map[island_1]]['bus'][ind, 0]
    # # print(bus_id)
    # gen_ind = ps.islands[ps.island_map[island_1]]['gen'][:, 0] == bus_id
    # # print(gen_ind)
    # gen_cap = ps.islands[ps.island_map[island_1]]['gen'][gen_ind, 8]
    # # print(gen_cap)
    # gen_weak_ind = ps.islands[ps.island_map[island_1]]['gen'][:, 8] == np.min(gen_cap)
    # # print(gen_weak_ind)
    # gen_weak_bus_id = ps.islands[ps.island_map[island_1]]['gen'][gen_weak_ind, 0]
    # # print(gen_weak_bus_id)
    # weak_bus_ind = ps.islands[ps.island_map[island_1]]['bus'][:, 0] == gen_weak_bus_id
    # # print(weak_bus_ind)
    #
    # # Set weak bus type to 1 (PQ bus)
    # ps.islands[ps.island_map[island_1]]['bus'][weak_bus_ind, 1] = 1
    
    # Get the post connection state
    ps.evaluate_islands()
    after_connection_state = ps.evaluate_state(list(ps.islands_evaluated.values()))
    after_connection_state['Title'] = 'Solving state after island connection'
    state_list.append(after_connection_state)

    return state_list
