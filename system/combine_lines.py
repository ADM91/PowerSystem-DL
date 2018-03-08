import numpy as np
from oct2py import octave
from system.combine_gen import combine_gen


def get_in(a):
    if len(a) == 1:
        return a[0]
    else:
        return a


def combine_lines(branch):

    unique_line = np.unique(ar=branch[:, [0, 1]],  axis=0)
    n = len(unique_line)
    m_branch = len(branch[0])
    new_branch = np.empty((n, m_branch))

    for i, buses in enumerate(unique_line):

        branch_ind = np.all(branch[:, [0,1]] == buses, axis=1)

        # Index to one of the lines
        ind1 = get_in(np.where(branch_ind))[0]
        branch1 = branch[ind1, :]

        new_branch[i, :] = branch1

        # If more than one line, combine parameters!
        if sum(branch_ind) > 1:
            # Capacity
            new_branch[i, 5] = np.sum(branch[branch_ind, 5])
            new_branch[i, 6] = np.sum(branch[branch_ind, 6])
            new_branch[i, 7] = np.sum(branch[branch_ind, 7])

            # Resistance
            new_branch[i, 2] = 1/np.sum(1/branch[branch_ind, 2])

            # Reactance
            new_branch[i, 3] = 1/np.sum(1/branch[branch_ind, 3])

            # Shunt susceptance
            new_branch[i, 4] = np.sum(branch[branch_ind, 4])

    return new_branch
