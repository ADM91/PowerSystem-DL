import numpy as np


def get_in(a):
    if len(a) == 1:
        return a[0]
    else:
        return a


def combine_gen(gen, gencost):

    unique_bus = np.unique(gen[:,0])
    n = len(unique_bus)
    m_gen = len(gen[0])
    m_gencost = len(gencost[0])
    new_gen = np.empty((n, m_gen))
    new_gencost = np.empty((n, m_gencost))

    remove_ind = []
    for i, bus in enumerate(unique_bus):

        # Find index to all generators on same bus
        gen_ind = gen[:, 0] == bus
        # Sum together stats from all generators on same bus
        sum_gen = np.sum(gen[gen_ind, :], axis=0)

        # Index to one of the generators)
        ind1 = get_in(np.where(gen_ind))[0]
        gen1 = gen[ind1, :]

        # Tweak the elements that should not be summed
        sum_gen[0] = bus      # Bus id
        sum_gen[5] = gen1[5]  # Voltage magnitude setpoint
        sum_gen[7] = 1        # Machine status

        # If the generator has no output, remove from the system
        if sum_gen[1] <= 0:
            remove_ind.append(i)
        else:
            new_gen[i, :] = sum_gen
            new_gencost[i, :] = gencost[0]

    new_gen = np.delete(new_gen, remove_ind, axis=0)
    new_gencost = np.delete(new_gencost, remove_ind, axis=0)

    return new_gen, new_gencost
