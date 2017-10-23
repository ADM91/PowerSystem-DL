import numpy as np


def between_blackout_energized(ps, island_1, island_2, bus_ids):

    state_list = list()

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

    line_ind = np.all(ps.islands['blackout']['branch'][:, 0:2] == bus_ids, axis=1)

    # Add branch to energized island branch matrix
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

    # Add the bus to energized bus matrix if not already there (from ideal case but set load served = 0))
    bus_ind = ps.ideal_case['bus'][:, 0] == black_bus
    if np.any(bus_ind):
        bus_added = np.append(ps.ideal_case['bus'][bus_ind, :], [0, 0, 0, 0]).reshape((1, -1))
        if black_bus in ps.action_list['fixed load']:
            bus_added[:, 2:4] = 0  # Set the load equal to zero
        ps.islands[ps.island_map[energ_island]]['bus'] = np.append(ps.islands[ps.island_map[energ_island]]['bus'],
                                                                   bus_added,
                                                                   axis=0)
        # Move generator and dispatchable loads (if they exist) to the energized island gen and gencost matricies
        # if np.sum(ps.islands[ps.island_map[energ_island]]['gen'][:, 0] == black_bus) == 0:  # perform if generators aren't already there
        gen_ind = ps.islands['blackout']['gen'][:, 0] == black_bus
        if np.sum(gen_ind) >= 1:
            gen = ps.islands['blackout']['gen'][gen_ind, :]
            gencost = ps.islands['blackout']['gencost'][gen_ind, :]
            gen[:, 7] = 0  # Leave out of service, activating the generator/load is a separate action
            gen = np.append(gen, np.zeros((np.sum(gen_ind), 4)), axis=1)

            print(gen)
            print(gencost)
            ps.islands[ps.island_map[energ_island]]['gen'] = np.append(ps.islands[ps.island_map[energ_island]]['gen'],
                                                                       gen,
                                                                       axis=0)
            ps.islands[ps.island_map[energ_island]]['gencost'] = np.append(ps.islands[ps.island_map[energ_island]]['gencost'],
                                                                           gencost,
                                                                           axis=0)
            # Remove gen or dispatch load from blackout matricies
            ps.islands['blackout']['gen'] = np.delete(ps.islands['blackout']['gen'], np.where(gen_ind), axis=0)
            ps.islands['blackout']['gencost'] = np.delete(ps.islands['blackout']['gencost'], np.where(gen_ind), axis=0)

    # Remove bus and branch from blackout island
    bus_ind = ps.islands['blackout']['bus'][:, 0] == black_bus
    ps.islands['blackout']['bus'] = np.delete(ps.islands['blackout']['bus'], np.where(bus_ind), axis=0)
    ps.islands['blackout']['branch'] = np.delete(ps.islands['blackout']['branch'], np.where(line_ind), axis=0)

    # Check for blackout connected buses
    for bus_conn, line_conn in zip(ps.blackout_connections['buses'], ps.blackout_connections['lines']):
        if black_bus in bus_conn:

            if ps.verbose:
                print('\nThere is a connected blackout network')
                print('Connected blackout buses:')
                print(bus_conn)
                print('Connected blackout lines:')
                print(line_conn)

            # Deal with any blackout lines that connect the blackout system to the energized system
            line_conn_np = np.array(line_conn)
            line_ind = [np.any(np.all(line_conn_np == branch, axis=1)) for branch in ps.islands['blackout']['branch'][:, 0:2]]

            # Add branch(s) to energized island branch matrix
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

            # Attach networked buses to the island (if it doesn't already exist!!!!)
            bus_ind = np.where([bus in bus_conn for bus in ps.ideal_case['bus'][:, 0]])[0]

            # If bus(es) not already in the island bus matrix, put them there and remove from blackout:
            for ind, bus in zip(bus_ind, ps.ideal_case['bus'][bus_ind, 0]):
                if bus not in ps.islands[ps.island_map[energ_island]]['bus'][:, 0]:
                    bus_added = np.append(ps.ideal_case['bus'][ind, :], [0, 0, 0, 0]).reshape((1, -1))
                    if black_bus in ps.action_list['fixed load']:
                        bus_added[:, 2:4] = 0  # Set the load equal to zero
                    ps.islands[ps.island_map[energ_island]]['bus'] = np.append(ps.islands[ps.island_map[energ_island]]['bus'],
                                                                               bus_added,
                                                                               axis=0)

                    # Move generator and dispatchable loads (if they exist)
                    gen_ind = ps.islands['blackout']['gen'][:, 0] == bus
                    if np.sum(gen_ind) >= 1:
                        gen = ps.islands['blackout']['gen'][gen_ind, :]
                        gencost = ps.islands['blackout']['gencost'][gen_ind, :]
                        gen[:, 7] = 0  # Leave out of service, activating the generator/load is a separate action
                        gen = np.append(gen, np.zeros((np.sum(gen_ind), 4)), axis=1)

                        ps.islands[ps.island_map[energ_island]]['gen'] = np.append(
                            ps.islands[ps.island_map[energ_island]]['gen'],
                            gen,
                            axis=0)
                        ps.islands[ps.island_map[energ_island]]['gencost'] = np.append(
                            ps.islands[ps.island_map[energ_island]]['gencost'],
                            gencost,
                            axis=0)
                        # Remove gen or dispatch load from blackout matricies
                        ps.islands['blackout']['gen'] = np.delete(ps.islands['blackout']['gen'], np.where(gen_ind), axis=0)
                        ps.islands['blackout']['gencost'] = np.delete(ps.islands['blackout']['gencost'], np.where(gen_ind), axis=0)

                # Remove energized bus from blackout matrix
                ind2 = ps.islands['blackout']['bus'][:, 0] == bus
                ps.islands['blackout']['bus'] = np.delete(ps.islands['blackout']['bus'], np.where(ind2), axis=0)

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
