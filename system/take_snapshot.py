from copy import deepcopy


def take_snapshot(ps, title, state_list, island_list):

    ps.current_state = ps.evaluate_state(list(ps.islands.values()))
    ps.current_state['Title'] = title  # Shows up on plot
    state_list.append(deepcopy(ps.current_state))
    island_list.append(deepcopy(ps.islands))

    return state_list, island_list
