import numpy as np
from auxiliary.iterable import iterable


def add_energy(energy_list):

    total_list = list()
    for items in energy_list:
        total = 0
        for item in iterable(items):
            add = np.sum(item)
            total += add
        total_list.append(total)

    return np.array(total_list)
