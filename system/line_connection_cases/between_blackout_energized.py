import numpy as np


def between_blackout_energized(ps, island_1, island_2, bus_ids):

    state_list = list()

    # If there is another line connecting this bus to the energized island, we have to find it and remove it
    # from the blackout line matrix, it is now an out-of-service line within the energized island.

    # I have a problem with my tabulation of buses, If I add a blackout connector line, I have to add that bus as
    # well, which I think ive neglected.

    # Which bus is blackout and which is energized?
    if island_1 == -1:
        black_bus = bus_ids[0]
        energ_bus = bus_ids[1]
        energ_island = island_2
    else:
        black_bus = bus_ids[1]
        energ_bus = bus_ids[0]
        energ_island = island_1
    
    if ps.verbose:
        print('black bus: %s' % black_bus)
        print('energized bus: %s\n' % energ_bus)

    if ps.verbose:
        print('Blackout buses before removal:')
        print(ps.islands['blackout']['bus'][:, 0])
        print('Blackout lines before removal:')
        print(ps.islands['blackout']['branch'][:, 0:2])

    # Take preliminary snapshot of the system
    prelim_state = ps.evaluate_state(list(ps.islands_evaluated.values()))
    prelim_state['Title'] = 'Preliminary state'  # Shows up on plot
    state_list.append(prelim_state)

    # Deal with any extra blackout lines that connect the blackout bus to the energized system
    # 1: find if such lines exist (index to line in islands blackout matrix)
    # line_ind = [np.any([ps.islands[ps.island_map[energ_island]]['bus'][:, 0] == bus for bus in branch]) and
    #             np.any([bus_ids == bus for bus in branch])
    #             for branch in ps.islands['blackout']['branch'][:, 0:2]]
    # line_ind = [np.any([ps.islands[ps.island_map[energ_island]]['bus'][:, 0] == bus for bus in branch])
    #             for branch in ps.islands['blackout']['branch'][:, 0:2]]
    line_ind = np.all(ps.islands['blackout']['branch'][:, 0:2] == bus_ids, axis=1)

    # 2: add to energized island branch matrix
    line_data = ps.islands['blackout']['branch'][line_ind, :]
    if ps.verbose:
        print('Line indices of swapped connectors:')
        print(line_ind)
        print('Line data for connector line(s) being swapped to the energized system:')
        print(line_data[:, [0, 1, 5, 10]])
    added_lines = np.concatenate((line_data, np.zeros((len(line_data), 4))), axis=1)
    added_lines[:, 10] = 1  # Enable the added line
    ps.islands[ps.island_map[energ_island]]['branch'] = np.append(
        ps.islands[ps.island_map[energ_island]]['branch'],
        added_lines,
        axis=0)

    # 3: remove from the blackout branch matrix
    ps.islands['blackout']['branch'] = np.delete(ps.islands['blackout']['branch'], np.where(line_ind), axis=0)

    # Make sure line in question is enabled
    # line_ind = np.all(ps.islands[ps.island_map[energ_island]]['branch'][:, 0:2] == bus_ids, axis=1)
    # ps.islands[ps.island_map[energ_island]]['branch'][line_ind, 10] = 1

    # Add the bus to energized bus matrix if not already there (taken from ideal case, i.e. enabled)
    bus_ind = ps.ideal_case['bus'][:, 0] == black_bus
    if np.any(bus_ind):
        ps.islands[ps.island_map[energ_island]]['bus'] = np.append(ps.islands[ps.island_map[energ_island]]['bus'],
                                                                   np.append(ps.ideal_case['bus'][bus_ind, :], [0, 0, 0, 0]).reshape((1, -1)),
                                                                   axis=0)

    # Remove stuff from blackout island
    bus_ind = ps.islands['blackout']['bus'][:, 0] == black_bus
    line_ind = np.all(ps.islands['blackout']['branch'][:, 0:2] == bus_ids, axis=1)
    ps.islands['blackout']['bus'] = np.delete(ps.islands['blackout']['bus'], np.where(bus_ind), axis=0)
    ps.islands['blackout']['branch'] = np.delete(ps.islands['blackout']['branch'], np.where(line_ind), axis=0)

    # Check if blackout bus is a part of connected blackout area and connect all if so
    for bus_conn, line_conn in zip(ps.blackout_connections['buses'], ps.blackout_connections['lines']):
        if black_bus in bus_conn:

            if ps.verbose:
                print('\nThere is a connected blackout network')
                print('Connected blackout buses:')
                print(bus_conn)
                print('Connected blackout lines:')
                print(line_conn)

            # Deal with any blackout lines that connect the blackout system to the energized system
            # 1: find if such lines exist (index to line in islands blackout matrix)
            # line_ind = [np.any([ps.islands[ps.island_map[energ_island]]['bus'][:, 0] == bus for bus in branch]) and
            #             np.any([bus_conn == bus for bus in branch])
            #             for branch in ps.islands['blackout']['branch'][:, 0:2]]
            line_conn_np = np.array(line_conn)
            line_ind = [np.any(np.all(line_conn_np == branch, axis=1)) for branch in ps.islands['blackout']['branch'][:, 0:2]]

            # 2: add branch(s) to energized island branch matrix
            line_data = ps.islands['blackout']['branch'][line_ind, :]
            line_data[:, 10] = 1  # Enable the line(s)!
            if ps.verbose:
                print('Line data for connector line(s) being swapped to the energized system:')
                print(line_data[:, [0, 1, 5, 10]])
            ps.islands[ps.island_map[energ_island]]['branch'] = np.append(
                ps.islands[ps.island_map[energ_island]]['branch'],
                np.concatenate((line_data, np.zeros((len(line_conn), 4))), axis=1),
                axis=0)

            # Remove branch(s) from blackout island
            line_ind = np.any([np.all(ps.islands['blackout']['branch'][:, 0:2] == line, axis=1) for line in line_conn], axis=0)
            ps.islands['blackout']['branch'] = np.delete(ps.islands['blackout']['branch'], np.where(line_ind), axis=0)


            # # 3: remove from the blackout branch matrix
            # ps.islands['blackout']['branch'] = np.delete(ps.islands['blackout']['branch'], np.where(line_ind), axis=0)

            # Attach networked buses to the island (if it doesn't already exist!!!!)
            # bus_ind = np.any([ps.ideal_case['bus'][:, 0] == bus for bus in bus_conn], axis=0)
            bus_ind = np.where([bus in bus_conn for bus in ps.ideal_case['bus'][:, 0]])[0]

            print(bus_ind)

            # line_ind = np.any([np.all(ps.ideal_case['branch'][:, 0:2] == line, axis=1) for line in line_conn], axis=0)

            # If bus(es) not already in the island bus matrix, put them there and remove from blackout:
            for ind, bus in zip(bus_ind, ps.ideal_case['bus'][bus_ind, 0]):
                if bus not in ps.islands[ps.island_map[energ_island]]['bus'][:, 0]:
                    print(ind)
                    print(ps.ideal_case['bus'][ind, :])
                    ps.islands[ps.island_map[energ_island]]['bus'] = np.append(ps.islands[ps.island_map[energ_island]]['bus'],
                                                                               np.concatenate((ps.ideal_case['bus'][ind, :].reshape((1, -1)), np.zeros((1, 4))), axis=1),
                                                                               axis=0)
                ind2 = ps.islands['blackout']['bus'][:, 0] == bus
                ps.islands['blackout']['bus'] = np.delete(ps.islands['blackout']['bus'], np.where(ind2), axis=0)

            # ps.islands[ps.island_map[energ_island]]['branch'] = np.append(ps.islands[ps.island_map[energ_island]]['branch'],
            #                                                               np.concatenate((ps.ideal_case['branch'][line_ind,:], np.zeros((len(line_conn), 4))), axis=1),
            #                                                               axis=0)

            # Remove lines and buses from blackout list
            ps.blackout_connections['buses'].remove(bus_conn)
            ps.blackout_connections['lines'].remove(line_conn)
    
            break

    if ps.verbose:
        print('Blackout buses after removal:')
        print(ps.islands['blackout']['bus'][:, 0])
        print('Blackout lines after removal:')
        print(ps.islands['blackout']['branch'][:, 0:2])

    # Sort the bus matrix in ascending order
    bus_order = np.argsort(ps.islands[ps.island_map[energ_island]]['bus'][:, 0], axis=0, kind='quicksort')
    ps.islands[ps.island_map[energ_island]]['bus'] = ps.islands[ps.island_map[energ_island]]['bus'][bus_order, :]
    
    # Sort the branch matrix in ascending order
    b1 = ps.islands[ps.island_map[energ_island]]['branch'][:, 0]
    b2 = ps.islands[ps.island_map[energ_island]]['branch'][:, 1]
    line_order = np.lexsort((b2, b1))  # First sort by bus1 then by bus2
    ps.islands[ps.island_map[energ_island]]['branch'] = ps.islands[ps.island_map[energ_island]]['branch'][line_order, :]
    
    # Run opf to get final steady state
    ps.evaluate_islands()
    after_connection_state = ps.evaluate_state(list(ps.islands_evaluated.values()))
    after_connection_state['Title'] = 'Solving state after line connection'
    state_list.append(after_connection_state)

    return state_list
