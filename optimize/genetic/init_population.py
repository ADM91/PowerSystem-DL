import numpy as np


def init_population(action_map, n):

    seq_len = len(action_map)
    init_pop = np.empty((n, seq_len))
    for i in range(n):
        init_pop[i, :] = np.random.permutation(list(action_map.keys()))

    return init_pop
