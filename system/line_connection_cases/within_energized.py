import numpy as np
from auxiliary.set_opf_constraints import set_opf_constraints
from system.take_snapshot import take_snapshot
from copy import deepcopy


def within_energized(ps, island_1, bus_ids, spad_lim):

    # print('Before snapshot is taken (outside the class)')
    # print(ps.current_state['real inj'][17, [2, 4]])
    # print(ps.islands['0']['branch'][17, 10:13])

    # Take preliminary snapshot of the system
    state_list, island_list = take_snapshot(ps, 'Preliminary state', [], [])

    # print('After evaluate state function (outside the class)')
    # print(ps.current_state['real inj'][17, [2, 4]])
    # print(state_list[-1]['real inj'][17, [2, 4]])
    # print(ps.islands['0']['branch'][17, 10:13])
    # print(island_list[-1]['0']['branch'][17, 10:13])
    # print('\n')

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

    # Set opf constraints
    ps.islands[ps.island_map[island_1]] = set_opf_constraints(test_case=ps.islands[ps.island_map[island_1]],
                                                              set_branch=branch_ind,
                                                              max_SPA=spad_lim,
                                                              set_gen=False,
                                                              set_loads=False)
    # Run opf on the islands
    ps.evaluate_islands()  # Matpower needs to be altered for this to work -- Think I got it

    # Take snapshot
    title = 'Rescheduling for connection of branch %s - %s' % (int(bus_ids[0]), int(bus_ids[1]))
    state_list, island_list = take_snapshot(ps, title, state_list, island_list)

    # Close the line and restore the SPA diff constraint
    ps.islands[ps.island_map[island_1]]['branch'][branch_ind, 10] = 1
    ps.islands[ps.island_map[island_1]] = set_opf_constraints(test_case=ps.islands[ps.island_map[island_1]],
                                                              set_branch=branch_ind,
                                                              max_SPA=360,
                                                              set_gen=False,
                                                              set_loads=False)

    # Run opf to get final steady state
    ps.evaluate_islands()

    # Take final snapshot
    title = 'Solving state after line connection'
    state_list, island_list = take_snapshot(ps, title, state_list, island_list)

    # Ensure that current state variable has the most recent information
    # ps.current_state = deepcopy(state_list[-1])

    return state_list, island_list
