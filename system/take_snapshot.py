from copy import deepcopy


def take_snapshot(ps, title, state_list, island_list):

    # Take snapshot of the system
    state = ps.evaluate_state(list(ps.islands.values()))
    state['Title'] = title  # Shows up on plot
    state_list.append(state)
    island_list.append(deepcopy(ps.islands))

    return state_list, island_list
