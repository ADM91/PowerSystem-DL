from copy import deepcopy
import numpy as np
from system.take_snapshot import take_snapshot


def between_islands(ps, island_1, island_2):

    # Get the state prior to connection
    ps.evaluate_islands()
    state_list, island_list = take_snapshot(ps, 'Island reconnection preliminary state', [], [])

    # Append all of island 2 to island 1
    island_2_copy = deepcopy(ps.islands[ps.island_map[island_2]])
    ps.islands[ps.island_map[island_1]]['bus'] = np.append(ps.islands[ps.island_map[island_1]]['bus'], island_2_copy['bus'], axis=0)
    ps.islands[ps.island_map[island_1]]['branch'] = np.append(ps.islands[ps.island_map[island_1]]['branch'], island_2_copy['branch'], axis=0)
    ps.islands[ps.island_map[island_1]]['gen'] = np.append(ps.islands[ps.island_map[island_1]]['gen'], island_2_copy['gen'], axis=0)
    ps.islands[ps.island_map[island_1]]['gencost'] = np.append(ps.islands[ps.island_map[island_1]]['gencost'], island_2_copy['gencost'], axis=0)

    # Sort the bus matrix in ascending order
    bus_order = np.argsort(ps.islands[ps.island_map[island_1]]['bus'][:, 0], axis=0, kind='quicksort')
    ps.islands[ps.island_map[island_1]]['bus'] = ps.islands[ps.island_map[island_1]]['bus'][bus_order, :]

    # Sort the branch matrix in ascending order
    b1 = ps.islands[ps.island_map[island_1]]['branch'][:, 0]
    b2 = ps.islands[ps.island_map[island_1]]['branch'][:, 1]
    line_order = np.lexsort((b2, b1))  # First sort by bus1 then by bus2
    ps.islands[ps.island_map[island_1]]['branch'] = ps.islands[ps.island_map[island_1]]['branch'][line_order, :]
    
    # Delete island 2
    del ps.islands[ps.island_map[island_2]]

    # TODO: remove weaker of two swing buses, there will be at least two buses as is
    
    # Evaluate post connection state
    ps.evaluate_islands()

    # Take final snapshot
    title = 'Solving state after island connection'
    state_list, island_list = take_snapshot(ps, title, state_list, island_list)

    # Ensure that current state variable has the most recent information
    ps.current_state = state_list[-1]

    return state_list, island_list
