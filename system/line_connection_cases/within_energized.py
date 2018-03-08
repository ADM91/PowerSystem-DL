import numpy as np
from system.take_snapshot import take_snapshot
from copy import deepcopy


def within_energized(ps, island_1, bus_ids, spad_lim):

    # Take preliminary snapshot of the system
    state_list, island_list = take_snapshot(ps, 'Preliminary state', [], [])

    # Set opf constraint to SPA diff
    # Make sure branch in question is on island branch matrix (isn't if each bus is added via blackout connection)
    branch_ind = np.all(ps.islands[ps.island_map[island_1]]['branch'][:, 0:2] == bus_ids, axis=1)

    if not np.any(branch_ind):
        # Add branch to the island
        branch_ind = np.all(ps.islands['blackout']['branch'][:, 0:2] == bus_ids, axis=1)
        line_data = ps.islands['blackout']['branch'][branch_ind, :]
        line_data[:, 10] = 1  # Enable the line
        ps.islands[ps.island_map[island_1]]['branch'] = np.append(
            ps.islands[ps.island_map[island_1]]['branch'],
            np.concatenate((line_data, np.zeros((len(line_data), 4))), axis=1),
            axis=0)

        # Remove branch from blackout
        ps.islands['blackout']['branch'] = np.delete(ps.islands['blackout']['branch'], np.where(branch_ind), axis=0)

        # Sort branches and Re-identify branch-ind
        b1 = ps.islands[ps.island_map[island_1]]['branch'][:, 0]
        b2 = ps.islands[ps.island_map[island_1]]['branch'][:, 1]
        line_order = np.lexsort((b2, b1))  # First sort by bus1 then by bus2
        ps.islands[ps.island_map[island_1]]['branch'] = ps.islands[ps.island_map[island_1]]['branch'][line_order, :]
        branch_ind = np.all(ps.islands[ps.island_map[island_1]]['branch'][:, 0:2] == bus_ids, axis=1)
        # print('branches: %s' % ps.islands[ps.island_map[island_1]]['branch'][:, 0:2])
        # print('selected branch: %s' % bus_ids)
        # print('branch_ind: %s' % branch_ind)
        # print('bus ids: %s' % bus_ids)
        # print(ps.islands['blackout']['bus'])

    # Set opf constraints
    ps.islands[ps.island_map[island_1]] = ps.set_opf_constraints(test_case=ps.islands[ps.island_map[island_1]],
                                                                 set_branch=branch_ind,
                                                                 max_spa=spad_lim,
                                                                 set_gen=False,
                                                                 set_loads=False)
    # Run opf on the islands
    success = ps.evaluate_islands()  # Matpower needs to be altered for this to work -- Think I got it
    if success == 0:
        return [], []

    # Take snapshot
    title = 'Rescheduling for connection of branch %s - %s' % (int(bus_ids[0]), int(bus_ids[1]))
    state_list, island_list = take_snapshot(ps, title, state_list, island_list)

    # Close the line and restore the SPA diff constraint
    ps.islands[ps.island_map[island_1]]['branch'][branch_ind, 10] = 1

    ps.islands[ps.island_map[island_1]] = ps.set_opf_constraints(test_case=ps.islands[ps.island_map[island_1]],
                                                                 set_branch=branch_ind,
                                                                 max_spa=360,
                                                                 set_gen=False,
                                                                 set_loads=False)

    # Run opf to get final steady state
    success = ps.evaluate_islands()
    if success == 0:
        return [], []

    # Take final snapshot
    title = 'Solving state after line connection'
    state_list, island_list = take_snapshot(ps, title, state_list, island_list)

    # Ensure that current state variable has the most recent information
    # ps.current_state = deepcopy(state_list[-1])

    return state_list, island_list
