import numpy as np


def within_blackout(ps, bus_ids):
    
    # Check connections list for the buses in question
    if len(ps.blackout_connections['buses']) == 0:
        # If no connections found, start a new connection list:
        ps.blackout_connections['buses'].append([int(bus_ids[0]), int(bus_ids[1])])
        ps.blackout_connections['lines'].append([bus_ids])
    else:
        # Figure out if buses belong to any already collected connections
        flag = 0
        count = 0
        for bus_conn, line_conn in zip(ps.blackout_connections['buses'], ps.blackout_connections['lines']):
            ind = np.array([i in bus_conn for i in bus_ids.astype('int')])
            if any(ind):  # Are any buses in question in connections?
                # These could both be true
                unique_bus = bus_ids[~ind]  # Detects which bus is unique to connections
                flag = 1
                break
            count += 1

        # If in no connections list, create a new one
        if flag == 0:
            ps.blackout_connections['buses'].append([int(bus_ids[0]), int(bus_ids[1])])
            ps.blackout_connections['lines'].append([bus_ids])
        elif flag == 1:
            for b_id in unique_bus:
                if b_id not in bus_conn:
                    ps.blackout_connections['buses'][count].append(int(b_id))
            ps.blackout_connections['lines'][count].append(bus_ids)

    return
