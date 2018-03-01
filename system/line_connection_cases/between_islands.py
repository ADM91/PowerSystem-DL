from copy import deepcopy
import numpy as np
from system.take_snapshot import take_snapshot


def between_islands(ps, island_1, island_2, bus_ids):

    # Get the state prior to connection
    success = ps.evaluate_islands()
    if success == 0:
        return [], []

    state_list, island_list = take_snapshot(ps, 'Island reconnection preliminary state', [], [])

    # Find and move line to island_1:
    island_1_ind = np.all(ps.islands[ps.island_map[island_1]]['branch'][:, 0:2] == bus_ids, axis=1)
    island_2_ind = np.all(ps.islands[ps.island_map[island_2]]['branch'][:, 0:2] == bus_ids, axis=1)
    blackout_ind = np.all(ps.islands['blackout']['branch'][:, 0:2] == bus_ids, axis=1)

    if np.sum(island_1_ind) == 1:
        ps.islands[ps.island_map[island_1]]['branch'][island_1_ind, 10] = 1
    elif np.sum(island_2_ind) == 1:
        # Island 2 gets appended to island 1 later
        ps.islands[ps.island_map[island_2]]['branch'][island_2_ind, 10] = 1
    elif np.sum(blackout_ind) == 1:
        # Give line to island 1 if its in blackout
        ps.islands[ps.island_map[island_1]]['branch'] = np.vstack((ps.islands[ps.island_map[island_1]]['branch'],
                                                                  np.hstack((ps.islands['blackout']['branch'][blackout_ind, :][0], np.zeros(4)))))
        ps.islands['blackout']['branch'] = np.delete(ps.islands['blackout']['branch'], blackout_ind, axis=0)
    else:
        print('Couldnt find the tie line, aborting')
        return [], []

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
    success = ps.evaluate_islands()
    if success == 0:
        return [], []

    # Take final snapshot
    title = 'Solving state after island connection'
    state_list, island_list = take_snapshot(ps, title, state_list, island_list)

    # Ensure that current state variable has the most recent information
    # ps.current_state = state_list[-1]

    return state_list, island_list
